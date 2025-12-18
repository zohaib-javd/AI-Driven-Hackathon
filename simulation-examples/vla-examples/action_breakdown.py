"""
Multi-Step Action Breakdown Algorithm for VLA Pipeline

This module implements algorithms to break down complex robot actions
into multi-step sequences that can be executed by the robot.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import time
import re
from pathlib import Path
import heapq
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActionStatus(Enum):
    """Status of an action"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionType(Enum):
    """Types of robot actions"""
    NAVIGATION = "navigation"
    MANIPULATION = "manipulation"
    PERCEPTION = "perception"
    CONTROL = "control"
    COMPOUND = "compound"


@dataclass
class ActionStep:
    """Represents a single action step"""
    step_id: str
    action_type: ActionType
    action: str
    target: str
    parameters: Dict[str, Any]
    description: str
    dependencies: List[str]
    estimated_duration: float
    priority: int
    confidence: float
    status: ActionStatus = ActionStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class ActionSequence:
    """Represents a sequence of actions"""
    sequence_id: str
    original_task: str
    steps: List[ActionStep]
    estimated_total_duration: float
    created_at: float
    metadata: Dict[str, Any]


@dataclass
class BreakdownResult:
    """Result of action breakdown"""
    success: bool
    action_sequence: Optional[ActionSequence]
    confidence: float
    errors: List[str]
    warnings: List[str]
    processing_time: float


class ActionDependencyGraph:
    """
    Graph representing dependencies between action steps
    """

    def __init__(self):
        self.graph = defaultdict(list)  # Adjacency list
        self.in_degree = defaultdict(int)  # Number of incoming edges
        self.nodes = set()  # All nodes in the graph

    def add_node(self, node_id: str):
        """Add a node to the graph"""
        self.nodes.add(node_id)
        if node_id not in self.in_degree:
            self.in_degree[node_id] = 0

    def add_dependency(self, from_node: str, to_node: str):
        """Add a dependency edge from_node -> to_node"""
        self.add_node(from_node)
        self.add_node(to_node)

        # Add edge
        self.graph[from_node].append(to_node)
        self.in_degree[to_node] += 1

    def get_ready_nodes(self) -> List[str]:
        """Get nodes with no dependencies (in-degree = 0)"""
        return [node for node in self.nodes if self.in_degree[node] == 0]

    def remove_node(self, node: str):
        """Remove a node and update dependencies"""
        if node not in self.nodes:
            return

        # Remove outgoing edges
        for neighbor in self.graph[node]:
            self.in_degree[neighbor] -= 1

        # Remove node
        self.graph.pop(node, None)
        self.in_degree.pop(node, None)
        self.nodes.remove(node)

    def is_empty(self) -> bool:
        """Check if the graph is empty"""
        return len(self.nodes) == 0

    def topological_sort(self) -> List[str]:
        """Perform topological sort to get execution order"""
        # Copy the graph
        temp_graph = ActionDependencyGraph()
        temp_graph.graph = {k: v[:] for k, v in self.graph.items()}
        temp_graph.in_degree = self.in_degree.copy()
        temp_graph.nodes = self.nodes.copy()

        result = []
        queue = deque(temp_graph.get_ready_nodes())

        while queue:
            node = queue.popleft()
            result.append(node)

            # Remove node and update dependencies
            for neighbor in temp_graph.graph[node]:
                temp_graph.in_degree[neighbor] -= 1
                if temp_graph.in_degree[neighbor] == 0:
                    queue.append(neighbor)

            # Remove from temp graph
            temp_graph.graph.pop(node, None)
            temp_graph.in_degree.pop(node, None)
            temp_graph.nodes.remove(node)

        # Check for cycles
        if len(result) != len(self.nodes):
            raise ValueError("Cycle detected in dependencies")

        return result


class ActionBreakdownAlgorithm:
    """
    Algorithm for breaking down complex actions into multi-step sequences
    """

    def __init__(self):
        self.dependency_graph = ActionDependencyGraph()
        self.action_templates = self._load_action_templates()

    def _load_action_templates(self) -> Dict[str, Any]:
        """Load action templates for common robot tasks"""
        return {
            "fetch_object": {
                "steps": [
                    {"action": "navigate_to", "target": "location", "depends_on": []},
                    {"action": "find_object", "target": "object", "depends_on": ["navigate_to"]},
                    {"action": "grasp_object", "target": "object", "depends_on": ["find_object"]},
                    {"action": "navigate_to", "target": "delivery_location", "depends_on": ["grasp_object"]}
                ],
                "parameters": ["object", "location", "delivery_location"]
            },
            "clean_surface": {
                "steps": [
                    {"action": "navigate_to", "target": "surface_location", "depends_on": []},
                    {"action": "detect_dirty_areas", "target": "surface", "depends_on": ["navigate_to"]},
                    {"action": "clean_area", "target": "dirty_area", "depends_on": ["detect_dirty_areas"]},
                    {"action": "inspect_cleanliness", "target": "surface", "depends_on": ["clean_area"]}
                ],
                "parameters": ["surface", "surface_location"]
            },
            "assemble_object": {
                "steps": [
                    {"action": "navigate_to", "target": "component_location", "depends_on": []},
                    {"action": "grasp_component", "target": "component", "depends_on": ["navigate_to"]},
                    {"action": "navigate_to", "target": "assembly_location", "depends_on": ["grasp_component"]},
                    {"action": "place_component", "target": "assembly_point", "depends_on": ["navigate_to"]},
                    {"action": "verify_assembly", "target": "assembly", "depends_on": ["place_component"]}
                ],
                "parameters": ["components", "assembly_location", "assembly_plan"]
            }
        }

    def breakdown_action(self, task: str, parameters: Dict[str, Any] = None) -> BreakdownResult:
        """
        Break down a complex action into a sequence of steps

        Args:
            task: The high-level task to break down
            parameters: Additional parameters for the task

        Returns:
            BreakdownResult with the action sequence
        """
        start_time = time.time()
        errors = []
        warnings = []

        try:
            # Determine the action template based on the task
            template = self._select_template(task, parameters or {})

            if not template:
                errors.append(f"No suitable template found for task: {task}")
                return BreakdownResult(
                    success=False,
                    action_sequence=None,
                    confidence=0.0,
                    errors=errors,
                    warnings=warnings,
                    processing_time=time.time() - start_time
                )

            # Generate steps based on the template
            steps = self._generate_steps_from_template(template, parameters or {})

            # Create dependency graph
            self._create_dependency_graph(steps)

            # Sort steps by dependencies
            execution_order = self._get_execution_order()
            sorted_steps = self._sort_steps_by_order(steps, execution_order)

            # Calculate total duration
            total_duration = sum(step.estimated_duration for step in sorted_steps)

            # Create action sequence
            sequence = ActionSequence(
                sequence_id=f"seq_{int(time.time())}_{hash(task) % 10000}",
                original_task=task,
                steps=sorted_steps,
                estimated_total_duration=total_duration,
                created_at=time.time(),
                metadata={
                    "template_used": template.get("name", "unknown"),
                    "parameters": parameters,
                    "num_steps": len(sorted_steps)
                }
            )

            # Calculate confidence based on template match and parameter completeness
            confidence = self._calculate_confidence(task, parameters, template)

            return BreakdownResult(
                success=True,
                action_sequence=sequence,
                confidence=confidence,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            errors.append(f"Action breakdown failed: {str(e)}")
            logger.error(f"Error breaking down action '{task}': {e}")
            return BreakdownResult(
                success=False,
                action_sequence=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

    def _select_template(self, task: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Select the most appropriate template for the task"""
        task_lower = task.lower()

        # Keyword-based template selection
        if any(keyword in task_lower for keyword in ["fetch", "get", "bring", "pick up", "retrieve"]):
            return {**self.action_templates["fetch_object"], "name": "fetch_object"}
        elif any(keyword in task_lower for keyword in ["clean", "tidy", "organize"]):
            return {**self.action_templates["clean_surface"], "name": "clean_surface"}
        elif any(keyword in task_lower for keyword in ["assemble", "build", "construct"]):
            return {**self.action_templates["assemble_object"], "name": "assemble_object"}
        else:
            # Use a generic template for unknown tasks
            return self._create_generic_template(task, parameters)

    def _create_generic_template(self, task: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a generic template for unknown tasks"""
        # This is a simplified approach - in practice, you might use LLMs for more sophisticated parsing
        steps = []

        # Analyze the task to determine likely steps
        task_lower = task.lower()

        # If it involves navigation
        if any(keyword in task_lower for keyword in ["go to", "navigate to", "move to"]):
            steps.append({
                "action": "navigate_to",
                "target": parameters.get("location", "unknown"),
                "depends_on": []
            })

        # If it involves manipulation
        if any(keyword in task_lower for keyword in ["pick", "grasp", "place", "move"]):
            steps.append({
                "action": "manipulate_object",
                "target": parameters.get("object", "unknown"),
                "depends_on": []
            })

        # If it involves perception
        if any(keyword in task_lower for keyword in ["find", "locate", "detect", "look"]):
            steps.append({
                "action": "perceive_environment",
                "target": parameters.get("target", "unknown"),
                "depends_on": []
            })

        # Add a generic completion step
        steps.append({
            "action": "report_completion",
            "target": "task",
            "depends_on": [step["action"] for step in steps]  # Depends on all previous steps
        })

        return {
            "name": "generic",
            "steps": steps,
            "parameters": list(parameters.keys())
        }

    def _generate_steps_from_template(self, template: Dict[str, Any],
                                    parameters: Dict[str, Any]) -> List[ActionStep]:
        """Generate action steps from a template"""
        steps = []

        for i, template_step in enumerate(template["steps"]):
            # Determine action type
            action_type = self._classify_action_type(template_step["action"])

            # Set default parameters based on template
            step_params = template_step.get("parameters", {}).copy()
            step_params.update(parameters)  # Override with provided parameters

            # Determine target
            target_key = template_step["target"]
            target = parameters.get(target_key, target_key)  # Use provided parameter or literal

            # Estimate duration based on action type
            duration = self._estimate_duration(template_step["action"])

            # Set priority (lower number = higher priority)
            priority = i + 1

            # Set confidence based on parameter completeness
            confidence = self._estimate_confidence_for_step(template_step, parameters)

            step = ActionStep(
                step_id=f"step_{i+1}",
                action_type=action_type,
                action=template_step["action"],
                target=target,
                parameters=step_params,
                description=f"{template_step['action']} {target}",
                dependencies=template_step.get("depends_on", []),
                estimated_duration=duration,
                priority=priority,
                confidence=confidence
            )

            steps.append(step)

        return steps

    def _classify_action_type(self, action: str) -> ActionType:
        """Classify the type of action"""
        action_lower = action.lower()

        if any(nav_word in action_lower for nav_word in ["navigate", "go", "move", "travel", "path", "waypoint"]):
            return ActionType.NAVIGATION
        elif any(manip_word in action_lower for manip_word in ["grasp", "pick", "place", "lift", "hold", "manipulate"]):
            return ActionType.MANIPULATION
        elif any(percept_word in action_lower for percept_word in ["detect", "find", "locate", "perceive", "scan", "observe"]):
            return ActionType.PERCEPTION
        elif any(control_word in action_lower for control_word in ["start", "stop", "pause", "resume", "reset", "calibrate"]):
            return ActionType.CONTROL
        else:
            return ActionType.COMPOUND

    def _estimate_duration(self, action: str) -> float:
        """Estimate duration for an action"""
        duration_map = {
            "navigate_to": 5.0,
            "find_object": 4.0,
            "grasp_object": 3.0,
            "place_object": 2.5,
            "clean_area": 8.0,
            "detect_dirty_areas": 3.0,
            "inspect_cleanliness": 2.0,
            "grasp_component": 3.0,
            "place_component": 2.5,
            "verify_assembly": 4.0,
            "report_completion": 1.0
        }

        return duration_map.get(action, 3.0)  # Default to 3 seconds

    def _estimate_confidence_for_step(self, template_step: Dict[str, Any],
                                    parameters: Dict[str, Any]) -> float:
        """Estimate confidence for a specific step"""
        # Check if required parameters are provided
        required_params = template_step.get("required_parameters", [])
        provided_params = [param for param in required_params if param in parameters]

        # Calculate confidence based on parameter completeness
        if not required_params:
            return 0.9  # High confidence if no required parameters

        completeness = len(provided_params) / len(required_params)
        base_confidence = 0.6  # Base confidence

        return base_confidence + (0.4 * completeness)  # Add up to 0.4 based on completeness

    def _create_dependency_graph(self, steps: List[ActionStep]):
        """Create dependency graph from action steps"""
        # Clear existing graph
        self.dependency_graph = ActionDependencyGraph()

        # Add all nodes
        for step in steps:
            self.dependency_graph.add_node(step.step_id)

        # Add dependencies
        for step in steps:
            for dep in step.dependencies:
                # Find the actual step ID that corresponds to the dependency
                dep_step_id = self._find_step_id_for_dependency(dep, steps)
                if dep_step_id:
                    self.dependency_graph.add_dependency(dep_step_id, step.step_id)

    def _find_step_id_for_dependency(self, dependency: str, steps: List[ActionStep]) -> Optional[str]:
        """Find the step ID that corresponds to a dependency"""
        # Look for a step whose action matches the dependency
        for step in steps:
            if dependency.lower() in step.action.lower() or dependency == step.step_id:
                return step.step_id
        return None

    def _get_execution_order(self) -> List[str]:
        """Get the execution order of steps using topological sort"""
        return self.dependency_graph.topological_sort()

    def _sort_steps_by_order(self, steps: List[ActionStep], execution_order: List[str]) -> List[ActionStep]:
        """Sort steps according to execution order"""
        step_dict = {step.step_id: step for step in steps}
        sorted_steps = []

        for step_id in execution_order:
            if step_id in step_dict:
                sorted_steps.append(step_dict[step_id])

        return sorted_steps

    def _calculate_confidence(self, task: str, parameters: Dict[str, Any],
                            template: Dict[str, Any]) -> float:
        """Calculate overall confidence for the breakdown"""
        # Consider parameter completeness
        required_params = template.get("parameters", [])
        provided_params = [param for param in required_params if param in parameters]

        completeness = len(provided_params) / len(required_params) if required_params else 1.0

        # Consider template match quality
        match_quality = 0.8  # Base quality for keyword matching

        return (completeness * 0.6) + (match_quality * 0.4)  # Weighted combination

    def breakdown_compound_action(self, task: str, subtasks: List[Dict[str, Any]]) -> BreakdownResult:
        """
        Break down a compound action consisting of multiple subtasks

        Args:
            task: The overall compound task
            subtasks: List of subtasks with their parameters

        Returns:
            BreakdownResult with the combined action sequence
        """
        start_time = time.time()
        errors = []
        warnings = []

        try:
            all_steps = []
            total_duration = 0.0

            # Break down each subtask
            for i, subtask in enumerate(subtasks):
                subtask_name = subtask.get("name", f"subtask_{i+1}")
                subtask_params = subtask.get("parameters", {})

                sub_breakdown = self.breakdown_action(subtask_name, subtask_params)

                if sub_breakdown.success and sub_breakdown.action_sequence:
                    # Add dependencies between subtasks (sequential execution)
                    if all_steps:
                        # Make current subtask depend on the last step of the previous subtask
                        prev_last_step = all_steps[-1].step_id
                        for step in sub_breakdown.action_sequence.steps:
                            if not step.dependencies:
                                step.dependencies.append(prev_last_step)

                    all_steps.extend(sub_breakdown.action_sequence.steps)
                    total_duration += sub_breakdown.action_sequence.estimated_total_duration
                else:
                    errors.extend(sub_breakdown.errors)
                    # Add a placeholder step for failed subtasks
                    error_step = ActionStep(
                        step_id=f"error_step_{i+1}",
                        action_type=ActionType.CONTROL,
                        action="report_error",
                        target="subtask",
                        parameters={"subtask": subtask_name, "error": sub_breakdown.errors[0] if sub_breakdown.errors else "Unknown error"},
                        description=f"Error in subtask: {subtask_name}",
                        dependencies=[all_steps[-1].step_id] if all_steps else [],
                        estimated_duration=1.0,
                        priority=10,
                        confidence=0.0
                    )
                    all_steps.append(error_step)

            if not all_steps:
                return BreakdownResult(
                    success=False,
                    action_sequence=None,
                    confidence=0.0,
                    errors=errors or ["No steps generated for compound task"],
                    warnings=warnings,
                    processing_time=time.time() - start_time
                )

            # Create compound action sequence
            compound_sequence = ActionSequence(
                sequence_id=f"compound_seq_{int(time.time())}",
                original_task=task,
                steps=all_steps,
                estimated_total_duration=total_duration,
                created_at=time.time(),
                metadata={
                    "compound_task": True,
                    "num_subtasks": len(subtasks),
                    "subtasks": [subtask.get("name", f"subtask_{i}") for i, subtask in enumerate(subtasks)]
                }
            )

            # Calculate compound confidence
            successful_subtasks = sum(1 for sb in [self.breakdown_action(st.get("name", ""), st.get("parameters", {})) for st in subtasks] if sb.success)
            compound_confidence = successful_subtasks / len(subtasks) if subtasks else 0.0

            return BreakdownResult(
                success=True,
                action_sequence=compound_sequence,
                confidence=compound_confidence,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            errors.append(f"Compound action breakdown failed: {str(e)}")
            logger.error(f"Error breaking down compound action '{task}': {e}")
            return BreakdownResult(
                success=False,
                action_sequence=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )


class AdvancedActionBreakdown:
    """
    Advanced action breakdown with optimization and parallel execution capabilities
    """

    def __init__(self):
        self.basic_breakdown = ActionBreakdownAlgorithm()
        self.optimizer = ActionSequenceOptimizer()

    def breakdown_with_optimization(self, task: str, parameters: Dict[str, Any] = None,
                                   optimize_for: str = "time") -> BreakdownResult:
        """
        Break down action with optimization

        Args:
            task: The task to break down
            parameters: Parameters for the task
            optimize_for: What to optimize for ('time', 'energy', 'safety', 'reliability')

        Returns:
            BreakdownResult with optimized action sequence
        """
        # First, get the basic breakdown
        basic_result = self.basic_breakdown.breakdown_action(task, parameters)

        if not basic_result.success or not basic_result.action_sequence:
            return basic_result

        # Optimize the sequence
        optimized_sequence = self.optimizer.optimize_sequence(
            basic_result.action_sequence, optimize_for
        )

        # Create new result with optimized sequence
        return BreakdownResult(
            success=basic_result.success,
            action_sequence=optimized_sequence,
            confidence=basic_result.confidence,
            errors=basic_result.errors,
            warnings=basic_result.warnings,
            processing_time=basic_result.processing_time
        )

    def breakdown_with_parallelization(self, task: str, parameters: Dict[str, Any] = None) -> BreakdownResult:
        """
        Break down action with consideration for parallel execution
        """
        # Get basic breakdown
        result = self.basic_breakdown.breakdown_action(task, parameters)

        if not result.success or not result.action_sequence:
            return result

        # Identify steps that can be executed in parallel
        parallel_groups = self._identify_parallelizable_steps(result.action_sequence.steps)

        # Reorganize steps for potential parallel execution
        reordered_steps = self._reorder_for_parallel_execution(
            result.action_sequence.steps, parallel_groups
        )

        # Update the action sequence
        optimized_sequence = ActionSequence(
            sequence_id=result.action_sequence.sequence_id,
            original_task=result.action_sequence.original_task,
            steps=reordered_steps,
            estimated_total_duration=self._recalculate_duration(reordered_steps),
            created_at=result.action_sequence.created_at,
            metadata={
                **result.action_sequence.metadata,
                "parallelization_applied": True,
                "parallel_groups": len(parallel_groups)
            }
        )

        return BreakdownResult(
            success=result.success,
            action_sequence=optimized_sequence,
            confidence=result.confidence,
            errors=result.errors,
            warnings=result.warnings,
            processing_time=result.processing_time
        )

    def _identify_parallelizable_steps(self, steps: List[ActionStep]) -> List[List[ActionStep]]:
        """Identify groups of steps that can be executed in parallel"""
        # This is a simplified approach - in practice, this would be more sophisticated
        # considering robot resources, environmental constraints, etc.

        # Group steps by resource requirements
        manipulator_steps = [s for s in steps if s.action_type in [ActionType.MANIPULATION]]
        navigation_steps = [s for s in steps if s.action_type in [ActionType.NAVIGATION]]
        perception_steps = [s for s in steps if s.action_type in [ActionType.PERCEPTION]]
        other_steps = [s for s in steps if s.action_type not in [ActionType.MANIPULATION, ActionType.NAVIGATION, ActionType.PERCEPTION]]

        # Steps that don't compete for the same resources can potentially run in parallel
        # For simplicity, we'll group by type, but in reality, this would be more nuanced
        parallel_groups = []

        # Add non-conflicting groups
        if manipulator_steps:
            parallel_groups.append(manipulator_steps)
        if navigation_steps:
            parallel_groups.append(navigation_steps)
        if perception_steps:
            parallel_groups.append(perception_steps)
        if other_steps:
            parallel_groups.append(other_steps)

        return parallel_groups

    def _reorder_for_parallel_execution(self, steps: List[ActionStep],
                                      parallel_groups: List[List[ActionStep]]) -> List[ActionStep]:
        """Reorder steps to enable parallel execution while respecting dependencies"""
        # For now, we'll interleave steps from different groups where possible
        # while maintaining dependency constraints

        # This is a simplified implementation
        # A full implementation would use more sophisticated scheduling algorithms

        # Create a dependency-aware scheduler
        scheduled_steps = []
        remaining_steps = steps[:]

        # Process steps in dependency order
        processed_ids = set()

        while remaining_steps:
            # Find steps whose dependencies are satisfied
            ready_steps = []
            for step in remaining_steps:
                deps_satisfied = all(dep_id in processed_ids for dep_id in step.dependencies)
                if deps_satisfied:
                    ready_steps.append(step)

            if not ready_steps:
                # Circular dependency or error
                logger.warning("Unable to schedule remaining steps due to dependencies")
                scheduled_steps.extend(remaining_steps)
                break

            # Add ready steps to schedule
            for step in ready_steps:
                scheduled_steps.append(step)
                processed_ids.add(step.step_id)
                remaining_steps.remove(step)

        return scheduled_steps

    def _recalculate_duration(self, steps: List[ActionStep]) -> float:
        """Recalculate total duration considering potential parallelization"""
        # Simplified calculation - in practice, this would consider actual parallel execution
        # and resource constraints
        return sum(step.estimated_duration for step in steps) * 0.8  # Assume 20% improvement


class ActionSequenceOptimizer:
    """
    Optimizes action sequences for various objectives
    """

    def __init__(self):
        self.optimization_functions = {
            'time': self._optimize_for_time,
            'energy': self._optimize_for_energy,
            'safety': self._optimize_for_safety,
            'reliability': self._optimize_for_reliability
        }

    def optimize_sequence(self, sequence: ActionSequence, objective: str = 'time') -> ActionSequence:
        """Optimize an action sequence for a specific objective"""
        if objective not in self.optimization_functions:
            logger.warning(f"Unknown optimization objective: {objective}, using 'time'")
            objective = 'time'

        optimized_steps = self.optimization_functions[objective](sequence.steps)

        return ActionSequence(
            sequence_id=f"optimized_{sequence.sequence_id}",
            original_task=sequence.original_task,
            steps=optimized_steps,
            estimated_total_duration=self._calculate_optimized_duration(optimized_steps, objective),
            created_at=time.time(),
            metadata={
                **sequence.metadata,
                "optimization_applied": objective,
                "optimized_at": time.time()
            }
        )

    def _optimize_for_time(self, steps: List[ActionStep]) -> List[ActionStep]:
        """Optimize steps for minimum execution time"""
        # Sort by priority (higher priority first) and then by estimated duration (shorter first)
        # for steps with the same priority
        return sorted(steps, key=lambda x: (x.priority, x.estimated_duration))

    def _optimize_for_energy(self, steps: List[ActionStep]) -> List[ActionStep]:
        """Optimize steps for minimum energy consumption"""
        # Energy optimization might involve grouping similar actions,
        # minimizing navigation, etc.
        # For now, we'll prioritize actions that consume less energy
        energy_costs = {
            'navigate_to': 10,
            'grasp_object': 5,
            'place_object': 3,
            'find_object': 8,
            'detect_dirty_areas': 6,
            'clean_area': 12,
            'inspect_cleanliness': 4
        }

        def energy_cost(step: ActionStep) -> int:
            return energy_costs.get(step.action, 7)  # Default cost

        return sorted(steps, key=lambda x: energy_cost(x))

    def _optimize_for_safety(self, steps: List[ActionStep]) -> List[ActionStep]:
        """Optimize steps for maximum safety"""
        # Safety optimization might involve ordering steps to minimize risk,
        # performing safety checks, etc.
        # For now, we'll prioritize steps with higher confidence
        return sorted(steps, key=lambda x: x.confidence, reverse=True)

    def _optimize_for_reliability(self, steps: List[ActionStep]) -> List[ActionStep]:
        """Optimize steps for maximum reliability"""
        # Reliability optimization might involve reordering to handle failures gracefully
        # For now, we'll prioritize steps with higher confidence
        return sorted(steps, key=lambda x: x.confidence, reverse=True)

    def _calculate_optimized_duration(self, steps: List[ActionStep], objective: str) -> float:
        """Calculate duration after optimization"""
        base_duration = sum(step.estimated_duration for step in steps)

        # Apply optimization factor based on objective
        optimization_factors = {
            'time': 0.9,  # 10% improvement
            'energy': 1.0,  # No direct time impact
            'safety': 1.1,  # Might take longer for safety
            'reliability': 1.05  # Slightly longer for reliability
        }

        factor = optimization_factors.get(objective, 1.0)
        return base_duration * factor


def main():
    """Example usage of the Action Breakdown Algorithm"""
    print("Multi-Step Action Breakdown Algorithm Example")

    # Initialize the breakdown algorithm
    breakdown_alg = ActionBreakdownAlgorithm()
    advanced_breakdown = AdvancedActionBreakdown()

    # Example tasks to break down
    example_tasks = [
        {
            "task": "fetch_object",
            "parameters": {"object": "red cup", "location": "kitchen", "delivery_location": "living room"}
        },
        {
            "task": "clean_surface",
            "parameters": {"surface": "dining table", "surface_location": "dining room"}
        },
        {
            "task": "assemble_object",
            "parameters": {"components": ["part_a", "part_b"], "assembly_location": "workbench", "assembly_plan": "simple_join"}
        }
    ]

    print("\n--- Basic Action Breakdown Examples ---")
    for i, task_info in enumerate(example_tasks):
        task = task_info["task"]
        params = task_info["parameters"]

        print(f"\nTask {i+1}: {task} with params {params}")
        result = breakdown_alg.breakdown_action(task, params)

        if result.success and result.action_sequence:
            seq = result.action_sequence
            print(f"  Success: {result.success}")
            print(f"  Confidence: {result.confidence:.3f}")
            print(f"  Steps: {len(seq.steps)}")
            print(f"  Estimated Duration: {seq.estimated_total_duration:.2f}s")

            print("  Step Details:")
            for j, step in enumerate(seq.steps):
                print(f"    {j+1}. {step.action} {step.target} - {step.description} "
                      f"(dur: {step.estimated_duration}s, conf: {step.confidence:.2f}, pri: {step.priority})")
                if step.dependencies:
                    print(f"        Dependencies: {step.dependencies}")
        else:
            print(f"  Failed: {result.errors}")

        print(f"  Processing Time: {result.processing_time:.3f}s")

    # Example: Compound action breakdown
    print(f"\n--- Compound Action Breakdown ---")
    compound_task = "complete_household_chores"
    subtasks = [
        {"name": "fetch_object", "parameters": {"object": "keys", "location": "bedroom", "delivery_location": "entrance"}},
        {"name": "clean_surface", "parameters": {"surface": "kitchen_counter", "surface_location": "kitchen"}},
        {"name": "fetch_object", "parameters": {"object": "mail", "location": "entrance_table", "delivery_location": "kitchen"}}
    ]

    compound_result = breakdown_alg.breakdown_compound_action(compound_task, subtasks)
    if compound_result.success and compound_result.action_sequence:
        seq = compound_result.action_sequence
        print(f"Compound task broken down successfully")
        print(f"  Total steps: {len(seq.steps)}")
        print(f"  Estimated duration: {seq.estimated_total_duration:.2f}s")
        print(f"  Confidence: {compound_result.confidence:.3f}")

        # Show first few steps
        for j, step in enumerate(seq.steps[:6]):  # Show first 6 steps
            print(f"    {j+1}. {step.action} {step.target} - {step.description}")

        if len(seq.steps) > 6:
            print(f"    ... and {len(seq.steps) - 6} more steps")

    # Example: Advanced breakdown with optimization
    print(f"\n--- Advanced Breakdown with Optimization ---")
    simple_task = "fetch_object"
    simple_params = {"object": "water_bottle", "location": "kitchen", "delivery_location": "office"}

    # Break down with time optimization
    time_opt_result = advanced_breakdown.breakdown_with_optimization(
        simple_task, simple_params, optimize_for="time"
    )
    if time_opt_result.success and time_opt_result.action_sequence:
        seq = time_opt_result.action_sequence
        print(f"Time-optimized breakdown:")
        print(f"  Original duration estimate: {seq.metadata.get('estimated_total_duration', 'N/A')}")
        print(f"  Optimized duration: {seq.estimated_total_duration:.2f}s")
        print(f"  Steps: {len(seq.steps)}")

    # Break down with parallelization
    parallel_result = advanced_breakdown.breakdown_with_parallelization(
        simple_task, simple_params
    )
    if parallel_result.success and parallel_result.action_sequence:
        seq = parallel_result.action_sequence
        print(f"Parallelizable breakdown:")
        print(f"  Estimated duration: {seq.estimated_total_duration:.2f}s")
        print(f"  Steps: {len(seq.steps)}")

    print("\nMulti-Step Action Breakdown example completed!")


if __name__ == "__main__":
    main()