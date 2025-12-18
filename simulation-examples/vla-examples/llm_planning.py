"""
LLM Cognitive Planning Module for Task Breakdown in VLA Pipeline

This module implements cognitive planning using Large Language Models (LLMs)
to break down complex tasks into executable steps for humanoid robots.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import openai
import time
import re
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlanningStatus(Enum):
    """Status of planning operation"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    INVALID_INPUT = "invalid_input"


class TaskComplexity(Enum):
    """Complexity levels for tasks"""
    SIMPLE = "simple"  # 1-2 steps
    MODERATE = "moderate"  # 3-5 steps
    COMPLEX = "complex"  # 6-10 steps
    VERY_COMPLEX = "very_complex"  # 10+ steps


@dataclass
class TaskStep:
    """Represents a single step in a task plan"""
    action: str
    target: str
    parameters: Dict[str, Any]
    description: str
    dependencies: List[str]
    estimated_duration: float  # in seconds
    priority: int  # 1 (highest) to 10 (lowest)
    confidence: float  # 0.0 to 1.0


@dataclass
class TaskPlan:
    """Represents a complete task plan"""
    task_id: str
    original_goal: str
    steps: List[TaskStep]
    complexity: TaskComplexity
    estimated_total_duration: float
    status: PlanningStatus
    metadata: Dict[str, Any]
    created_at: float


@dataclass
class PlanningResult:
    """Result of planning operation"""
    success: bool
    task_plan: Optional[TaskPlan]
    confidence: float
    errors: List[str]
    warnings: List[str]
    processing_time: float


class LLMTaxonomy:
    """
    Taxonomy of robot actions and capabilities for LLM planning
    """

    def __init__(self):
        # Navigation actions
        self.navigation_actions = [
            "navigate_to",
            "move_to",
            "go_to",
            "travel_to",
            "approach",
            "reach",
            "path_follow",
            "waypoint_navigation"
        ]

        # Manipulation actions
        self.manipulation_actions = [
            "grasp",
            "pick_up",
            "lift",
            "hold",
            "release",
            "place",
            "put_down",
            "move_object",
            "align",
            "orient",
            "grip",
            "manipulate"
        ]

        # Perception actions
        self.perception_actions = [
            "detect",
            "find",
            "locate",
            "recognize",
            "identify",
            "inspect",
            "observe",
            "scan",
            "sense",
            "perceive"
        ]

        # Control actions
        self.control_actions = [
            "start",
            "stop",
            "pause",
            "resume",
            "reset",
            "calibrate",
            "initialize",
            "shutdown",
            "emergency_stop"
        ]

        # Object categories
        self.object_categories = [
            "container", "furniture", "electronics", "food",
            "utensil", "tool", "clothing", "personal_item"
        ]

        # Location types
        self.location_types = [
            "room", "area", "workspace", "storage", "entrance",
            "exit", "charging_station", "workstation"
        ]

        # Action parameters
        self.action_parameters = {
            "navigation": ["target_location", "speed", "avoid_obstacles", "precision"],
            "manipulation": ["target_object", "grip_force", "orientation", "placement_accuracy"],
            "perception": ["target_object", "scan_range", "recognition_threshold", "view_angle"],
            "control": ["duration", "intensity", "mode", "safety_level"]
        }

    def get_action_category(self, action: str) -> str:
        """Get the category of an action"""
        if action in self.navigation_actions:
            return "navigation"
        elif action in self.manipulation_actions:
            return "manipulation"
        elif action in self.perception_actions:
            return "perception"
        elif action in self.control_actions:
            return "control"
        else:
            return "unknown"


class TaskDecomposer:
    """
    Decomposes complex tasks into simpler sub-tasks
    """

    def __init__(self, llm_taxonomy: LLMTaxonomy):
        self.taxonomy = llm_taxonomy

    def decompose_task(self, goal: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Decompose a complex task into sub-tasks

        Args:
            goal: The high-level goal to decompose
            context: Additional context information

        Returns:
            List of sub-tasks with details
        """
        # First, determine task complexity
        complexity = self.estimate_complexity(goal)

        # For simple tasks, return basic decomposition
        if complexity == TaskComplexity.SIMPLE:
            return self._decompose_simple_task(goal, context)

        # For moderate tasks
        elif complexity == TaskComplexity.MODERATE:
            return self._decompose_moderate_task(goal, context)

        # For complex tasks, use LLM assistance
        else:
            return self._decompose_complex_task_with_llm(goal, context, complexity)

    def estimate_complexity(self, goal: str) -> TaskComplexity:
        """Estimate the complexity of a task based on keywords and structure"""
        goal_lower = goal.lower()

        # Count action verbs
        action_count = 0
        for category in [self.taxonomy.navigation_actions,
                         self.taxonomy.manipulation_actions,
                         self.taxonomy.perception_actions]:
            for action in category:
                if action in goal_lower:
                    action_count += 1

        # Estimate complexity based on action count and other factors
        if action_count <= 1:
            return TaskComplexity.SIMPLE
        elif action_count <= 3:
            return TaskComplexity.MODERATE
        elif action_count <= 6:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.VERY_COMPLEX

    def _decompose_simple_task(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose simple tasks (1-2 steps)"""
        goal_lower = goal.lower()

        # Identify the main action and target
        action = self._identify_primary_action(goal_lower)
        target = self._identify_target(goal_lower)

        steps = [{
            "action": action,
            "target": target,
            "description": goal,
            "dependencies": [],
            "estimated_duration": self._estimate_duration(action),
            "priority": 1,
            "confidence": 0.9
        }]

        return steps

    def _decompose_moderate_task(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose moderate tasks (3-5 steps)"""
        # For moderate tasks, we'll do basic pattern matching
        steps = []

        # Example: "Go to kitchen and pick up red cup"
        if "and" in goal_lower:
            sub_goals = goal.split("and")
            for i, sub_goal in enumerate(sub_goals):
                sub_goal_clean = sub_goal.strip()

                action = self._identify_primary_action(sub_goal_clean)
                target = self._identify_target(sub_goal_clean)

                steps.append({
                    "action": action,
                    "target": target,
                    "description": sub_goal_clean,
                    "dependencies": [] if i == 0 else [f"step_{i-1}"],
                    "estimated_duration": self._estimate_duration(action),
                    "priority": i + 1,
                    "confidence": 0.8
                })

        return steps

    def _decompose_complex_task_with_llm(self, goal: str, context: Dict[str, Any],
                                       complexity: TaskComplexity) -> List[Dict[str, Any]]:
        """Use LLM to decompose complex tasks"""
        if not openai.api_key:
            # Try to get from environment
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                openai.api_key = api_key
            else:
                # Fallback to simple decomposition
                logger.warning("No OpenAI API key found, using simple decomposition")
                return self._decompose_simple_task(goal, context)

        try:
            prompt = self._create_decomposition_prompt(goal, context, complexity)

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_planning_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1000
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("steps", [])

        except Exception as e:
            logger.error(f"LLM decomposition failed: {e}")
            # Fallback to simple decomposition
            return self._decompose_simple_task(goal, context)

    def _create_decomposition_prompt(self, goal: str, context: Dict[str, Any],
                                   complexity: TaskComplexity) -> str:
        """Create prompt for LLM-based task decomposition"""
        context_str = json.dumps(context, indent=2) if context else "{}"

        prompt = f"""
        Decompose the following complex robotics task into executable steps.
        The task has complexity level: {complexity.value}

        Goal: "{goal}"

        Context: {context_str}

        Available actions:
        - Navigation: {', '.join(self.taxonomy.navigation_actions[:5])}...
        - Manipulation: {', '.join(self.taxonomy.manipulation_actions[:5])}...
        - Perception: {', '.join(self.taxonomy.perception_actions[:5])}...
        - Control: {', '.join(self.taxonomy.control_actions[:5])}...

        Return a JSON array of steps with the following structure:
        [
            {{
                "action": "action_name",
                "target": "target_object_or_location",
                "description": "detailed description of the step",
                "dependencies": ["step_id_or_condition"],
                "estimated_duration": number_in_seconds,
                "priority": 1-10,
                "confidence": 0.0-1.0,
                "parameters": {{
                    "param1": "value1",
                    "param2": "value2"
                }}
            }}
        ]

        Requirements:
        - Steps should be ordered logically
        - Dependencies should reflect real execution constraints
        - Durations should be realistic (0.5-30 seconds for typical robot actions)
        - Priorities should reflect importance for successful task completion
        - Confidence should reflect certainty of step feasibility
        """

        return prompt

    def _get_planning_system_prompt(self) -> str:
        """Get the system prompt for planning"""
        return """
        You are a cognitive planning system for humanoid robots. Your task is to decompose high-level goals into executable, low-level steps that a robot can perform. Consider the following:

        1. Physical constraints: Robots have limited mobility, dexterity, and perception
        2. Sequential execution: Most actions must be performed in a specific order
        3. Safety: Always prioritize safe execution over efficiency
        4. Context awareness: Consider the environment and available resources
        5. Action feasibility: Ensure each action is achievable given robot capabilities

        Return only valid JSON as specified in the user prompt.
        """

    def _identify_primary_action(self, text: str) -> str:
        """Identify the primary action in a text"""
        text_lower = text.lower()

        # Check navigation actions first (often primary)
        for action in self.taxonomy.navigation_actions:
            if action in text_lower:
                return action

        # Then manipulation
        for action in self.taxonomy.manipulation_actions:
            if action in text_lower:
                return action

        # Then perception
        for action in self.taxonomy.perception_actions:
            if action in text_lower:
                return action

        # Then control
        for action in self.taxonomy.control_actions:
            if action in text_lower:
                return action

        return "unknown"

    def _identify_target(self, text: str) -> str:
        """Identify the target object/location in a text"""
        # Simple pattern matching for targets
        # This is a basic implementation - in practice, you'd use more sophisticated NLP

        # Look for objects after articles or prepositions
        patterns = [
            r'(?:the|a|an)\s+(\w+(?:\s+\w+)?)\s+(?:from|on|in|at|to)',
            r'(?:to|from|on|in|at)\s+(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:is|are|was|were)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()

        # If no match, return the longest noun phrase
        words = text.split()
        nouns = [w for w in words if w.lower() in
                ['kitchen', 'cup', 'table', 'book', 'keys', 'phone', 'red', 'blue', 'small', 'large']]

        return ' '.join(nouns[:2]) if nouns else 'unknown'

    def _estimate_duration(self, action: str) -> float:
        """Estimate duration for an action"""
        duration_map = {
            'navigate_to': 5.0,
            'move_to': 5.0,
            'go_to': 5.0,
            'grasp': 2.0,
            'pick_up': 2.5,
            'lift': 2.0,
            'place': 2.0,
            'put_down': 2.0,
            'detect': 3.0,
            'find': 4.0,
            'locate': 4.0,
            'stop': 0.5,
            'pause': 0.5,
            'resume': 0.5
        }

        return duration_map.get(action, 3.0)


class LLMCognitivePlanner:
    """
    Main cognitive planning system using LLMs
    """

    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        self.taxonomy = LLMTaxonomy()
        self.decomposer = TaskDecomposer(self.taxonomy)

        # Initialize safety checker
        self.safety_checker = SafetyConstraintChecker()

        logger.info(f"LLM Cognitive Planner initialized with model: {model_name}")

    def create_task_plan(self, goal: str, context: Dict[str, Any] = None) -> PlanningResult:
        """
        Create a task plan for a given goal

        Args:
            goal: The high-level goal to achieve
            context: Context information (robot state, environment, etc.)

        Returns:
            PlanningResult with the task plan
        """
        start_time = time.time()
        errors = []
        warnings = []

        try:
            # Validate inputs
            if not goal or not goal.strip():
                errors.append("Empty goal provided")
                return PlanningResult(
                    success=False,
                    task_plan=None,
                    confidence=0.0,
                    errors=errors,
                    warnings=warnings,
                    processing_time=time.time() - start_time
                )

            # Decompose the task
            sub_tasks = self.decomposer.decompose_task(goal, context)

            if not sub_tasks:
                errors.append("Could not decompose task")
                return PlanningResult(
                    success=False,
                    task_plan=None,
                    confidence=0.0,
                    errors=errors,
                    warnings=warnings,
                    processing_time=time.time() - start_time
                )

            # Convert sub-tasks to TaskStep objects
            steps = []
            for i, sub_task in enumerate(sub_tasks):
                step = TaskStep(
                    action=sub_task.get('action', 'unknown'),
                    target=sub_task.get('target', 'unknown'),
                    parameters=sub_task.get('parameters', {}),
                    description=sub_task.get('description', f'Step {i+1}'),
                    dependencies=sub_task.get('dependencies', []),
                    estimated_duration=sub_task.get('estimated_duration', 3.0),
                    priority=sub_task.get('priority', 5),
                    confidence=sub_task.get('confidence', 0.7)
                )
                steps.append(step)

            # Estimate overall complexity
            complexity = self.decomposer.estimate_complexity(goal)

            # Calculate total estimated duration
            total_duration = sum(step.estimated_duration for step in steps)

            # Create task plan
            task_plan = TaskPlan(
                task_id=f"plan_{int(time.time())}_{hash(goal) % 10000}",
                original_goal=goal,
                steps=steps,
                complexity=complexity,
                estimated_total_duration=total_duration,
                status=PlanningStatus.SUCCESS,
                metadata={
                    "created_with_model": self.model_name,
                    "context_provided": context is not None,
                    "num_steps": len(steps),
                    "timestamp": time.time()
                },
                created_at=time.time()
            )

            # Validate the plan for safety
            validation_result = self.safety_checker.validate_plan(task_plan)
            if not validation_result['is_safe']:
                task_plan.status = PlanningStatus.PARTIAL_SUCCESS
                warnings.extend(validation_result['warnings'])

            # Calculate overall confidence
            avg_confidence = sum(step.confidence for step in steps) / len(steps) if steps else 0.0

            return PlanningResult(
                success=True,
                task_plan=task_plan,
                confidence=avg_confidence,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            errors.append(f"Planning error: {str(e)}")
            logger.error(f"Error creating task plan for goal '{goal}': {e}")
            return PlanningResult(
                success=False,
                task_plan=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

    def refine_plan(self, plan: TaskPlan, feedback: Dict[str, Any]) -> PlanningResult:
        """
        Refine an existing plan based on feedback

        Args:
            plan: The existing task plan to refine
            feedback: Feedback about the plan

        Returns:
            PlanningResult with refined plan
        """
        start_time = time.time()
        errors = []
        warnings = []

        try:
            # In a real implementation, this would use LLM to refine the plan
            # For now, we'll return the original plan with feedback incorporated

            refined_steps = []
            for step in plan.steps:
                # Apply feedback to each step if relevant
                refined_step = self._apply_feedback_to_step(step, feedback)
                refined_steps.append(refined_step)

            # Create refined plan
            refined_plan = TaskPlan(
                task_id=f"refined_{plan.task_id}",
                original_goal=plan.original_goal,
                steps=refined_steps,
                complexity=plan.complexity,
                estimated_total_duration=sum(s.estimated_duration for s in refined_steps),
                status=PlanningStatus.SUCCESS,
                metadata={
                    **plan.metadata,
                    "refined_from": plan.task_id,
                    "feedback_applied": True
                },
                created_at=time.time()
            )

            avg_confidence = sum(step.confidence for step in refined_steps) / len(refined_steps) if refined_steps else 0.0

            return PlanningResult(
                success=True,
                task_plan=refined_plan,
                confidence=avg_confidence,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            errors.append(f"Plan refinement error: {str(e)}")
            logger.error(f"Error refining plan {plan.task_id}: {e}")
            return PlanningResult(
                success=False,
                task_plan=plan,  # Return original on failure
                confidence=plan.steps[0].confidence if plan.steps else 0.0,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

    def _apply_feedback_to_step(self, step: TaskStep, feedback: Dict[str, Any]) -> TaskStep:
        """Apply feedback to a single step"""
        # This is a simplified implementation
        # In practice, you'd use LLM to understand the feedback and modify the step

        # Example: if feedback indicates a step took too long, adjust duration
        if feedback.get('duration_feedback'):
            adjustment = feedback['duration_feedback'].get('adjustment_ratio', 1.0)
            adjusted_duration = step.estimated_duration * adjustment
            return TaskStep(
                action=step.action,
                target=step.target,
                parameters=step.parameters,
                description=step.description,
                dependencies=step.dependencies,
                estimated_duration=adjusted_duration,
                priority=step.priority,
                confidence=step.confidence
            )

        return step

    def merge_plans(self, plans: List[TaskPlan]) -> PlanningResult:
        """
        Merge multiple task plans into a single coherent plan

        Args:
            plans: List of task plans to merge

        Returns:
            PlanningResult with merged plan
        """
        if not plans:
            return PlanningResult(
                success=False,
                task_plan=None,
                confidence=0.0,
                errors=["No plans to merge"],
                warnings=[],
                processing_time=0.0
            )

        if len(plans) == 1:
            return PlanningResult(
                success=True,
                task_plan=plans[0],
                confidence=0.8,  # High confidence for single plan
                errors=[],
                warnings=[],
                processing_time=0.0
            )

        start_time = time.time()
        errors = []
        warnings = []

        try:
            # Combine all steps from all plans
            all_steps = []
            for plan in plans:
                all_steps.extend(plan.steps)

            # Sort steps by priority and dependencies
            sorted_steps = self._sort_steps_by_dependencies(all_steps)

            # Create merged plan
            merged_goal = " + ".join([p.original_goal for p in plans])
            total_duration = sum(step.estimated_duration for step in sorted_steps)

            merged_plan = TaskPlan(
                task_id=f"merged_{int(time.time())}",
                original_goal=merged_goal,
                steps=sorted_steps,
                complexity=max((p.complexity for p in plans),
                             key=lambda x: ["simple", "moderate", "complex", "very_complex"].index(x.value)),
                estimated_total_duration=total_duration,
                status=PlanningStatus.SUCCESS,
                metadata={
                    "merged_from": [p.task_id for p in plans],
                    "num_original_plans": len(plans),
                    "merged_at": time.time()
                },
                created_at=time.time()
            )

            avg_confidence = sum(step.confidence for step in sorted_steps) / len(sorted_steps) if sorted_steps else 0.0

            return PlanningResult(
                success=True,
                task_plan=merged_plan,
                confidence=avg_confidence,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            errors.append(f"Plan merging error: {str(e)}")
            logger.error(f"Error merging plans: {e}")
            return PlanningResult(
                success=False,
                task_plan=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

    def _sort_steps_by_dependencies(self, steps: List[TaskStep]) -> List[TaskStep]:
        """Sort steps based on their dependencies"""
        # Simple topological sort implementation
        sorted_steps = []
        remaining_steps = steps[:]

        while remaining_steps:
            # Find steps with no unsatisfied dependencies
            ready_steps = []
            for step in remaining_steps:
                deps_satisfied = all(
                    any(dep_step.description == dep for dep_step in sorted_steps)
                    for dep in step.dependencies
                )
                if deps_satisfied:
                    ready_steps.append(step)

            if not ready_steps:
                # Circular dependency detected
                logger.warning("Circular dependency detected, breaking cycle")
                sorted_steps.extend(remaining_steps)
                break

            # Add ready steps to sorted list
            sorted_steps.extend(ready_steps)

            # Remove from remaining
            for step in ready_steps:
                remaining_steps.remove(step)

        return sorted_steps


class SafetyConstraintChecker:
    """
    Checks task plans for safety constraints
    """

    def __init__(self):
        self.safety_constraints = [
            self._check_physical_safety,
            self._check_operational_safety,
            self._check_environmental_safety
        ]

    def validate_plan(self, plan: TaskPlan) -> Dict[str, Any]:
        """
        Validate a plan against safety constraints

        Args:
            plan: The task plan to validate

        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []

        for constraint_check in self.safety_constraints:
            result = constraint_check(plan)
            issues.extend(result['issues'])
            warnings.extend(result['warnings'])

        return {
            'is_safe': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'confidence': 1.0 - min(1.0, len(issues) * 0.2)  # Reduce confidence with issues
        }

    def _check_physical_safety(self, plan: TaskPlan) -> Dict[str, List[str]]:
        """Check for physical safety issues"""
        issues = []
        warnings = []

        for step in plan.steps:
            action = step.action.lower()

            # Check for dangerous actions
            if any(danger in action for danger in ['destroy', 'damage', 'break']):
                issues.append(f"Dangerous action detected: {action}")

            # Check for physically impossible actions
            if 'jump' in action and plan.complexity == TaskComplexity.SIMPLE:
                warnings.append(f"High-risk action for simple task: {action}")

        return {'issues': issues, 'warnings': warnings}

    def _check_operational_safety(self, plan: TaskPlan) -> Dict[str, List[str]]:
        """Check for operational safety issues"""
        issues = []
        warnings = []

        # Check for conflicting operations
        nav_count = sum(1 for step in plan.steps if 'navigate' in step.action)
        if nav_count > 5:
            warnings.append(f"High navigation count ({nav_count}), consider optimization")

        return {'issues': issues, 'warnings': warnings}

    def _check_environmental_safety(self, plan: TaskPlan) -> Dict[str, List[str]]:
        """Check for environmental safety issues"""
        issues = []
        warnings = []

        # This would typically check against environment data
        # For now, we'll just add general warnings
        if plan.complexity == TaskComplexity.VERY_COMPLEX:
            warnings.append("Complex plan may require additional environmental verification")

        return {'issues': issues, 'warnings': warnings}


class PlanOptimizer:
    """
    Optimizes task plans for efficiency and safety
    """

    def __init__(self):
        self.optimization_strategies = [
            self._optimize_sequential_actions,
            self._optimize_navigation_paths,
            self._optimize_resource_utilization
        ]

    def optimize_plan(self, plan: TaskPlan) -> TaskPlan:
        """
        Optimize a task plan

        Args:
            plan: The plan to optimize

        Returns:
            Optimized plan
        """
        optimized_plan = plan

        for strategy in self.optimization_strategies:
            optimized_plan = strategy(optimized_plan)

        return optimized_plan

    def _optimize_sequential_actions(self, plan: TaskPlan) -> TaskPlan:
        """Optimize sequentially similar actions"""
        # Example: Combine multiple navigation actions to nearby locations
        optimized_steps = []
        i = 0

        while i < len(plan.steps):
            current_step = plan.steps[i]

            # Look ahead for similar actions that can be combined
            if (current_step.action in ['navigate_to', 'go_to', 'move_to'] and
                i + 1 < len(plan.steps)):
                next_step = plan.steps[i + 1]
                if (next_step.action in ['navigate_to', 'go_to', 'move_to'] and
                    self._are_locations_nearby(current_step.target, next_step.target)):
                    # Combine the navigation steps
                    combined_step = TaskStep(
                        action=current_step.action,
                        target=f"{current_step.target}_then_{next_step.target}",
                        parameters={**current_step.parameters, **next_step.parameters},
                        description=f"Navigate to {current_step.target} then to {next_step.target}",
                        dependencies=current_step.dependencies,
                        estimated_duration=current_step.estimated_duration + next_step.estimated_duration * 0.7,  # Efficiency gain
                        priority=min(current_step.priority, next_step.priority),
                        confidence=(current_step.confidence + next_step.confidence) / 2
                    )
                    optimized_steps.append(combined_step)
                    i += 2  # Skip next step as it's combined
                else:
                    optimized_steps.append(current_step)
                    i += 1
            else:
                optimized_steps.append(current_step)
                i += 1

        return TaskPlan(
            task_id=f"optimized_{plan.task_id}",
            original_goal=plan.original_goal,
            steps=optimized_steps,
            complexity=plan.complexity,
            estimated_total_duration=sum(s.estimated_duration for s in optimized_steps),
            status=plan.status,
            metadata={**plan.metadata, "optimized": True},
            created_at=time.time()
        )

    def _are_locations_nearby(self, loc1: str, loc2: str) -> bool:
        """Check if two locations are nearby (simplified)"""
        # In a real implementation, this would check actual distances
        # For now, we'll just check if they're in the same general area
        common_rooms = ['kitchen', 'living room', 'bedroom', 'office', 'hallway']
        return any(room in loc1.lower() and room in loc2.lower() for room in common_rooms)

    def _optimize_navigation_paths(self, plan: TaskPlan) -> TaskPlan:
        """Optimize navigation paths"""
        # This would typically involve path planning algorithms
        # For now, we'll just ensure navigation steps are efficient
        return plan

    def _optimize_resource_utilization(self, plan: TaskPlan) -> TaskPlan:
        """Optimize resource utilization"""
        # This would involve checking for resource conflicts
        # For now, we'll just return the plan
        return plan


def main():
    """Example usage of the LLM Cognitive Planning Module"""
    print("LLM Cognitive Planning Module Example")

    # Initialize the planner
    planner = LLMCognitivePlanner(model_name="gpt-4")

    # Example goals to test
    test_goals = [
        "Navigate to the kitchen",
        "Pick up the red cup from the table",
        "Go to the living room and find the blue book",
        "Clean the table by moving objects to the shelf",
        "Fetch water from the kitchen and bring it to the office",
        "Inspect the plants in the greenhouse and water those that need it"
    ]

    print("\n--- Task Planning Examples ---")
    for i, goal in enumerate(test_goals):
        print(f"\nGoal {i+1}: '{goal}'")

        # Create plan with simple context
        context = {
            "robot_capabilities": ["navigation", "manipulation", "perception"],
            "environment": {
                "known_locations": ["kitchen", "living room", "office", "bedroom"],
                "objects_present": ["cup", "book", "table", "plants"]
            },
            "current_location": "starting_point"
        }

        result = planner.create_task_plan(goal, context)

        if result.success and result.task_plan:
            plan = result.task_plan
            print(f"  Success: {result.success}")
            print(f"  Complexity: {plan.complexity.value}")
            print(f"  Steps: {len(plan.steps)}")
            print(f"  Estimated Duration: {plan.estimated_total_duration:.2f}s")
            print(f"  Confidence: {result.confidence:.3f}")

            print("  Steps:")
            for j, step in enumerate(plan.steps):
                print(f"    {j+1}. {step.action} {step.target} - {step.description} "
                      f"(dur: {step.estimated_duration}s, conf: {step.confidence:.2f})")
        else:
            print(f"  Failed: {result.errors}")

        if result.warnings:
            print(f"  Warnings: {result.warnings}")

        print(f"  Processing Time: {result.processing_time:.3f}s")

    # Example: Plan refinement
    print(f"\n--- Plan Refinement Example ---")
    original_result = planner.create_task_plan("Go to kitchen and pick up the red cup")
    if original_result.success and original_result.task_plan:
        print(f"Original plan has {len(original_result.task_plan.steps)} steps")

        # Provide feedback that the navigation took longer than expected
        feedback = {
            "duration_feedback": {
                "step_1": {"actual_duration": 8.0, "expected_duration": 5.0, "adjustment_ratio": 1.6}
            }
        }

        refined_result = planner.refine_plan(original_result.task_plan, feedback)
        if refined_result.success and refined_result.task_plan:
            print(f"Refined plan has {len(refined_result.task_plan.steps)} steps")
            print(f"Refined duration: {refined_result.task_plan.estimated_total_duration:.2f}s")
        else:
            print("Refinement failed")

    # Example: Plan optimization
    print(f"\n--- Plan Optimization Example ---")
    if original_result.success and original_result.task_plan:
        optimizer = PlanOptimizer()
        optimized_plan = optimizer.optimize_plan(original_result.task_plan)
        print(f"Original duration: {original_result.task_plan.estimated_total_duration:.2f}s")
        print(f"Optimized duration: {optimized_plan.estimated_total_duration:.2f}s")
        print(f"Improvement: {(original_result.task_plan.estimated_total_duration - optimized_plan.estimated_total_duration)/original_result.task_plan.estimated_total_duration*100:.1f}%")

    print("\nLLM Cognitive Planning example completed!")


if __name__ == "__main__":
    main()