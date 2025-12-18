"""
ROS 2 Action Sequence Generator for VLA Pipeline

This module generates ROS 2 action sequences from the multi-step plans
created by the LLM cognitive planning system.
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
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ROSActionType(Enum):
    """Types of ROS 2 actions"""
    NAVIGATION = "navigation"
    MANIPULATION = "manipulation"
    PERCEPTION = "perception"
    CONTROL = "control"
    CUSTOM = "custom"


class ActionExecutionStatus(Enum):
    """Status of action execution"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class ROSAction:
    """Represents a ROS 2 action"""
    action_id: str
    action_type: ROSActionType
    action_name: str
    package: str
    node_name: str
    service_name: Optional[str] = None
    action_server: Optional[str] = None
    parameters: Dict[str, Any] = None
    timeout: float = 30.0
    retry_count: int = 1
    pre_conditions: List[str] = None
    post_conditions: List[str] = None
    callbacks: Dict[str, str] = None  # Maps callback names to function names


@dataclass
class ROSActionSequence:
    """Represents a sequence of ROS 2 actions"""
    sequence_id: str
    name: str
    actions: List[ROSAction]
    created_at: float
    metadata: Dict[str, Any]


@dataclass
class ActionGenerationResult:
    """Result of action generation"""
    success: bool
    action_sequence: Optional[ROSActionSequence]
    confidence: float
    errors: List[str]
    warnings: List[str]
    processing_time: float


class ROSActionGenerator:
    """
    Generator for ROS 2 action sequences from high-level plans
    """

    def __init__(self):
        self.action_templates = self._load_action_templates()
        self.ros_interface = ROSInterface()
        self.action_validator = ROSActionValidator()

    def _load_action_templates(self) -> Dict[str, Any]:
        """Load templates for common ROS 2 actions"""
        return {
            "navigate_to": {
                "action_type": ROSActionType.NAVIGATION,
                "package": "nav2_msgs",
                "action_name": "NavigateToPose",
                "node_name": "bt_navigator",
                "service_name": "navigate_to_pose",
                "parameters": ["target_pose", "behavior_tree"],
                "required_fields": ["target_pose.pose.position.x", "target_pose.pose.position.y", "target_pose.pose.orientation.z"]
            },
            "grasp_object": {
                "action_type": ROSActionType.MANIPULATION,
                "package": "manipulation_msgs",
                "action_name": "GraspObject",
                "node_name": "manipulation_controller",
                "service_name": "grasp_object",
                "parameters": ["object_id", "grasp_pose", "gripper_force"],
                "required_fields": ["object_id", "grasp_pose"]
            },
            "place_object": {
                "action_type": ROSActionType.MANIPULATION,
                "package": "manipulation_msgs",
                "action_name": "PlaceObject",
                "node_name": "manipulation_controller",
                "service_name": "place_object",
                "parameters": ["object_id", "place_pose", "release_force"],
                "required_fields": ["object_id", "place_pose"]
            },
            "detect_object": {
                "action_type": ROSActionType.PERCEPTION,
                "package": "vision_msgs",
                "action_name": "DetectObjects",
                "node_name": "object_detector",
                "service_name": "detect_objects",
                "parameters": ["roi", "class_names", "min_confidence"],
                "required_fields": []
            },
            "move_joints": {
                "action_type": ROSActionType.MANIPULATION,
                "package": "control_msgs",
                "action_name": "FollowJointTrajectory",
                "node_name": "joint_trajectory_controller",
                "service_name": "follow_joint_trajectory",
                "parameters": ["trajectory", "joint_names", "points"],
                "required_fields": ["trajectory.joint_names", "trajectory.points"]
            },
            "stop_robot": {
                "action_type": ROSActionType.CONTROL,
                "package": "std_srvs",
                "action_name": "Trigger",
                "node_name": "robot_controller",
                "service_name": "stop_motion",
                "parameters": [],
                "required_fields": []
            }
        }

    def generate_action_sequence(self, plan_steps: List[Dict[str, Any]],
                                robot_config: Dict[str, Any] = None) -> ActionGenerationResult:
        """
        Generate a ROS 2 action sequence from plan steps

        Args:
            plan_steps: List of plan steps from cognitive planner
            robot_config: Configuration for the specific robot

        Returns:
            ActionGenerationResult with the generated sequence
        """
        start_time = time.time()
        errors = []
        warnings = []

        try:
            actions = []

            for i, step in enumerate(plan_steps):
                action = self._generate_single_action(step, i, robot_config)
                if action:
                    actions.append(action)
                else:
                    errors.append(f"Failed to generate action for step {i}: {step}")

            if not actions:
                return ActionGenerationResult(
                    success=False,
                    action_sequence=None,
                    confidence=0.0,
                    errors=errors or ["No actions generated"],
                    warnings=warnings,
                    processing_time=time.time() - start_time
                )

            # Validate the entire sequence
            validation_result = self.action_validator.validate_sequence(actions)
            if not validation_result['is_valid']:
                warnings.extend(validation_result['issues'])

            # Create action sequence
            sequence = ROSActionSequence(
                sequence_id=f"ros_seq_{int(time.time())}_{hash(str(plan_steps)) % 10000}",
                name=f"generated_sequence_{len(actions)}_actions",
                actions=actions,
                created_at=time.time(),
                metadata={
                    "num_actions": len(actions),
                    "robot_config_used": robot_config is not None,
                    "generation_timestamp": time.time()
                }
            )

            # Calculate confidence based on successful generation
            success_rate = (len(actions) / len(plan_steps)) if plan_steps else 1.0
            confidence = 0.5 + (0.5 * success_rate)  # Base 0.5 + success contribution

            return ActionGenerationResult(
                success=True,
                action_sequence=sequence,
                confidence=confidence,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            errors.append(f"Action generation failed: {str(e)}")
            logger.error(f"Error generating ROS action sequence: {e}")
            return ActionGenerationResult(
                success=False,
                action_sequence=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

    def _generate_single_action(self, step: Dict[str, Any], step_index: int,
                              robot_config: Dict[str, Any] = None) -> Optional[ROSAction]:
        """Generate a single ROS action from a plan step"""
        try:
            # Determine the action type based on the step action
            action_name = step.get('action', '').lower()
            target = step.get('target', '')
            parameters = step.get('parameters', {})
            original_description = step.get('description', '')

            # Map the plan action to a ROS action template
            ros_action_template = self._match_to_ros_template(action_name)

            if not ros_action_template:
                logger.warning(f"No ROS template found for action: {action_name}")
                return None

            # Create ROS action parameters based on plan parameters
            ros_params = self._map_parameters(
                ros_action_template, parameters, target, robot_config
            )

            # Determine node and service names based on robot configuration
            node_name = self._get_node_name(ros_action_template, robot_config)
            service_name = self._get_service_name(ros_action_template, robot_config)

            # Set appropriate timeout based on action type
            timeout = self._get_timeout(ros_action_template.get('action_type'))

            action = ROSAction(
                action_id=f"ros_action_{step_index}",
                action_type=ros_action_template['action_type'],
                action_name=ros_action_template['action_name'],
                package=ros_action_template['package'],
                node_name=node_name,
                service_name=service_name,
                action_server=ros_action_template.get('action_server'),
                parameters=ros_params,
                timeout=timeout,
                retry_count=step.get('retry_count', 1),
                pre_conditions=step.get('pre_conditions', []),
                post_conditions=step.get('post_conditions', []),
                callbacks=step.get('callbacks', {})
            )

            return action

        except Exception as e:
            logger.error(f"Error generating ROS action for step {step_index}: {e}")
            return None

    def _match_to_ros_template(self, action_name: str) -> Optional[Dict[str, Any]]:
        """Match a high-level action name to a ROS template"""
        # Direct match
        if action_name in self.action_templates:
            return self.action_templates[action_name]

        # Pattern matching for variations
        action_lower = action_name.lower()

        # Navigation actions
        if any(nav_word in action_lower for nav_word in ['navigate', 'go_to', 'move_to', 'travel', 'path']):
            return self.action_templates.get('navigate_to')

        # Manipulation actions
        if any(manip_word in action_lower for manip_word in ['grasp', 'pick', 'lift', 'place', 'put', 'manipulate']):
            if any(place_word in action_lower for place_word in ['place', 'put', 'drop', 'set']):
                return self.action_templates.get('place_object')
            else:
                return self.action_templates.get('grasp_object')

        # Perception actions
        if any(percept_word in action_lower for percept_word in ['detect', 'find', 'locate', 'perceive', 'see']):
            return self.action_templates.get('detect_object')

        # Joint control
        if any(joint_word in action_lower for joint_word in ['move_joints', 'move_joint', 'trajectory', 'pose']):
            return self.action_templates.get('move_joints')

        # Control actions
        if any(control_word in action_lower for control_word in ['stop', 'halt', 'pause', 'reset', 'calibrate']):
            return self.action_templates.get('stop_robot')

        return None

    def _map_parameters(self, template: Dict[str, Any], plan_params: Dict[str, Any],
                       target: str, robot_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Map plan parameters to ROS action parameters"""
        ros_params = {}

        # Add template-specific default parameters
        for param_name in template.get('parameters', []):
            # Try to get from plan parameters
            if param_name in plan_params:
                ros_params[param_name] = plan_params[param_name]
            # Or use defaults based on the target or other plan details
            else:
                mapped_param = self._infer_parameter(param_name, target, plan_params, robot_config)
                if mapped_param is not None:
                    ros_params[param_name] = mapped_param

        # Add target-specific parameters
        if target and target not in ros_params.values():
            # For navigation, target might be a pose
            if template['action_name'] == 'NavigateToPose':
                ros_params['target_pose'] = self._create_pose_from_target(target)
            # For manipulation, target might be an object
            elif template['action_name'] in ['GraspObject', 'PlaceObject']:
                ros_params['object_id'] = target

        return ros_params

    def _infer_parameter(self, param_name: str, target: str, plan_params: Dict[str, Any],
                        robot_config: Dict[str, Any] = None) -> Optional[Any]:
        """Infer parameter values from context"""
        # Default values based on parameter name
        if param_name == 'min_confidence':
            return plan_params.get('confidence', 0.7)
        elif param_name == 'gripper_force':
            return plan_params.get('grip_force', 50.0)  # Default grip force
        elif param_name == 'release_force':
            return plan_params.get('release_force', 10.0)  # Lower release force
        elif param_name == 'behavior_tree':
            # Default behavior tree based on action
            if 'navigate' in param_name.lower():
                return plan_params.get('behavior_tree', 'navigate_w_replanning_and_recovery.xml')
        elif param_name == 'class_names':
            # If target is specified, use it as class name
            if target and 'object' in target.lower():
                return [target.replace('object', '').strip()]

        # If robot config is provided, use it for inference
        if robot_config:
            if param_name in robot_config.get('defaults', {}):
                return robot_config['defaults'][param_name]

        return None

    def _create_pose_from_target(self, target: str) -> Dict[str, Any]:
        """Create a pose from a target location"""
        # This is a simplified implementation - in practice, you'd look up poses from a map
        # or use object detection to determine location
        location_map = {
            'kitchen': {'x': 1.0, 'y': 2.0, 'z': 0.0},
            'living_room': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'bedroom': {'x': -1.0, 'y': 2.0, 'z': 0.0},
            'office': {'x': 2.0, 'y': 1.0, 'z': 0.0}
        }

        # Try to match target to known locations
        for location, coords in location_map.items():
            if location in target.lower():
                return {
                    'pose': {
                        'position': {'x': coords['x'], 'y': coords['y'], 'z': coords['z']},
                        'orientation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}
                    }
                }

        # If no match, return a default pose
        return {
            'pose': {
                'position': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'orientation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}
            }
        }

    def _get_node_name(self, template: Dict[str, Any], robot_config: Dict[str, Any] = None) -> str:
        """Get appropriate node name based on template and robot configuration"""
        if robot_config and 'nodes' in robot_config:
            # Check if there's a specific node configured for this action
            for action_type, node_name in robot_config.get('action_to_node_mapping', {}).items():
                if template['action_name'] in action_type:
                    return node_name

        # Return default from template
        return template.get('node_name', 'default_controller')

    def _get_service_name(self, template: Dict[str, Any], robot_config: Dict[str, Any] = None) -> str:
        """Get appropriate service name based on template and robot configuration"""
        if robot_config and 'services' in robot_config:
            # Check if there's a specific service configured for this action
            for action_type, service_name in robot_config.get('action_to_service_mapping', {}).items():
                if template['action_name'] in action_type:
                    return service_name

        # Return default from template
        return template.get('service_name', f"execute_{template['action_name'].lower()}")

    def _get_timeout(self, action_type: ROSActionType) -> float:
        """Get appropriate timeout based on action type"""
        timeouts = {
            ROSActionType.NAVIGATION: 60.0,  # Navigation can take longer
            ROSActionType.MANIPULATION: 30.0,  # Manipulation tasks
            ROSActionType.PERCEPTION: 10.0,   # Perception is usually quick
            ROSActionType.CONTROL: 5.0,      # Control commands are fast
            ROSActionType.CUSTOM: 20.0       # Default for custom actions
        }

        return timeouts.get(action_type, 30.0)

    def generate_compound_action_sequence(self, high_level_task: str,
                                         sub_sequences: List[ROSActionSequence]) -> ActionGenerationResult:
        """
        Generate a compound action sequence from multiple sub-sequences

        Args:
            high_level_task: The overall task that the compound sequence should accomplish
            sub_sequences: List of action sequences to combine

        Returns:
            ActionGenerationResult with the compound sequence
        """
        start_time = time.time()
        errors = []
        warnings = []

        try:
            all_actions = []
            total_duration = 0.0

            # Combine all actions from sub-sequences
            for i, sub_seq in enumerate(sub_sequences):
                # Add dependency markers between sub-sequences
                for j, action in enumerate(sub_seq.actions):
                    new_action = action
                    # Add dependency on previous sub-sequence if not the first
                    if i > 0 and j == 0:
                        new_action.pre_conditions = new_action.pre_conditions or []
                        new_action.pre_conditions.append(f"completion_of_sequence_{i-1}")
                    all_actions.append(new_action)

                total_duration += getattr(sub_seq, 'estimated_duration', len(sub_seq.actions) * 5.0)

            if not all_actions:
                errors.append("No actions in compound sequence")
                return ActionGenerationResult(
                    success=False,
                    action_sequence=None,
                    confidence=0.0,
                    errors=errors,
                    warnings=warnings,
                    processing_time=time.time() - start_time
                )

            # Create compound sequence
            compound_sequence = ROSActionSequence(
                sequence_id=f"compound_{int(time.time())}_{hash(high_level_task) % 10000}",
                name=f"compound_sequence_for_{high_level_task}",
                actions=all_actions,
                created_at=time.time(),
                metadata={
                    "compound_task": high_level_task,
                    "num_subsequences": len(sub_sequences),
                    "num_actions": len(all_actions),
                    "total_estimated_duration": total_duration
                }
            )

            return ActionGenerationResult(
                success=True,
                action_sequence=compound_sequence,
                confidence=0.9,  # High confidence for compound sequences
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            errors.append(f"Compound sequence generation failed: {str(e)}")
            logger.error(f"Error generating compound sequence: {e}")
            return ActionGenerationResult(
                success=False,
                action_sequence=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )


class ROSInterface:
    """
    Interface for interacting with ROS 2
    """

    def __init__(self):
        self.is_initialized = False
        self.current_node = None

    def initialize(self, node_name: str = "vla_ros_action_generator"):
        """Initialize the ROS 2 interface"""
        try:
            # Try to import ROS 2 libraries
            self.rclpy = importlib.util.find_spec("rclpy")
            if self.rclpy is not None:
                import rclpy
                rclpy.init()
                self.current_node = rclpy.create_node(node_name)
                self.is_initialized = True
                logger.info(f"ROS 2 interface initialized with node: {node_name}")
            else:
                logger.warning("ROS 2 not available, running in simulation mode")
                self.is_initialized = False

        except ImportError:
            logger.warning("ROS 2 not available, running in simulation mode")
            self.is_initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize ROS 2 interface: {e}")
            self.is_initialized = False

    def execute_action_sequence(self, sequence: ROSActionSequence) -> Dict[str, Any]:
        """Execute a sequence of ROS actions"""
        if not self.is_initialized:
            return self._simulate_execution(sequence)

        results = []
        start_time = time.time()

        for action in sequence.actions:
            result = self.execute_single_action(action)
            results.append(result)

        execution_time = time.time() - start_time

        return {
            'success': all(r['status'] == ActionExecutionStatus.SUCCESS for r in results),
            'results': results,
            'total_execution_time': execution_time,
            'sequence_id': sequence.sequence_id
        }

    def execute_single_action(self, action: ROSAction) -> Dict[str, Any]:
        """Execute a single ROS action"""
        if not self.is_initialized:
            return self._simulate_action_execution(action)

        try:
            # In a real implementation, this would call the actual ROS service/action
            # For now, we'll simulate it
            return self._simulate_action_execution(action)

        except Exception as e:
            logger.error(f"Error executing action {action.action_id}: {e}")
            return {
                'action_id': action.action_id,
                'status': ActionExecutionStatus.FAILED,
                'error': str(e),
                'execution_time': 0.0
            }

    def _simulate_execution(self, sequence: ROSActionSequence) -> Dict[str, Any]:
        """Simulate execution of action sequence"""
        results = []
        total_time = 0.0

        for action in sequence.actions:
            result = self._simulate_action_execution(action)
            results.append(result)
            total_time += result['execution_time']

        return {
            'success': all(r['status'] == ActionExecutionStatus.SUCCESS for r in results),
            'results': results,
            'total_execution_time': total_time,
            'sequence_id': sequence.sequence_id
        }

    def _simulate_action_execution(self, action: ROSAction) -> Dict[str, Any]:
        """Simulate execution of a single action"""
        # Simulate execution time based on timeout
        execution_time = min(action.timeout, 5.0)  # Cap at 5 seconds for simulation

        # Simulate success/failure based on confidence and timeout
        import random
        success_prob = min(1.0, action.timeout / 10.0)  # Higher timeout = higher success prob

        status = ActionExecutionStatus.SUCCESS if random.random() < success_prob else ActionExecutionStatus.FAILED

        return {
            'action_id': action.action_id,
            'status': status,
            'execution_time': execution_time,
            'details': f"Simulated execution of {action.action_name} in {action.package}"
        }

    def shutdown(self):
        """Shutdown the ROS interface"""
        if self.is_initialized and self.current_node:
            self.current_node.destroy_node()
            # rclpy.shutdown()  # Uncomment in real ROS environment


class ROSActionValidator:
    """
    Validator for ROS actions and sequences
    """

    def __init__(self):
        self.required_fields = {
            'NavigateToPose': ['target_pose.pose.position.x', 'target_pose.pose.position.y'],
            'GraspObject': ['object_id', 'grasp_pose'],
            'PlaceObject': ['object_id', 'place_pose'],
            'FollowJointTrajectory': ['trajectory.joint_names', 'trajectory.points']
        }

    def validate_action(self, action: ROSAction) -> Dict[str, Any]:
        """Validate a single ROS action"""
        issues = []
        warnings = []

        # Check required fields based on action name
        required_fields = self.required_fields.get(action.action_name, [])
        for field in required_fields:
            if not self._check_nested_field(action.parameters, field):
                issues.append(f"Missing required field '{field}' for action {action.action_name}")

        # Check parameter types
        for param_name, param_value in action.parameters.items():
            if param_name in ['target_pose', 'grasp_pose', 'place_pose']:
                if not self._validate_pose(param_value):
                    warnings.append(f"Pose parameter '{param_name}' may be malformed: {param_value}")

        # Check timeout bounds
        if action.timeout <= 0:
            warnings.append(f"Timeout should be positive, got {action.timeout}")

        if action.timeout > 300:  # 5 minutes
            warnings.append(f"Timeout {action.timeout}s seems excessive for most actions")

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'action_id': action.action_id
        }

    def validate_sequence(self, actions: List[ROSAction]) -> Dict[str, Any]:
        """Validate a sequence of ROS actions"""
        all_issues = []
        all_warnings = []
        valid_count = 0

        for action in actions:
            result = self.validate_action(action)
            if result['is_valid']:
                valid_count += 1
            all_issues.extend(result['issues'])
            all_warnings.extend(result['warnings'])

        return {
            'is_valid': len(all_issues) == 0,
            'issues': all_issues,
            'warnings': all_warnings,
            'valid_actions': valid_count,
            'total_actions': len(actions)
        }

    def _check_nested_field(self, data: Dict[str, Any], field_path: str) -> bool:
        """Check if a nested field exists in the data"""
        fields = field_path.split('.')
        current = data

        for field in fields:
            if isinstance(current, dict) and field in current:
                current = current[field]
            else:
                return False

        return current is not None

    def _validate_pose(self, pose_data: Any) -> bool:
        """Validate pose data structure"""
        if not isinstance(pose_data, dict):
            return False

        # Check for required pose structure
        required_keys = ['pose']
        for key in required_keys:
            if key not in pose_data:
                return False

        pose = pose_data['pose']
        if not isinstance(pose, dict):
            return False

        # Check position
        position = pose.get('position')
        if not position or not isinstance(position, dict):
            return False

        required_pos_fields = ['x', 'y', 'z']
        for field in required_pos_fields:
            if field not in position:
                return False

        # Check orientation
        orientation = pose.get('orientation')
        if not orientation or not isinstance(orientation, dict):
            return False

        required_orient_fields = ['x', 'y', 'z', 'w']
        for field in required_orient_fields:
            if field not in orientation:
                return False

        return True


class ActionSequenceOptimizer:
    """
    Optimizer for ROS action sequences
    """

    def __init__(self):
        self.resource_requirements = {
            'manipulator': ['grasp_object', 'place_object', 'move_joints'],
            'navigation': ['navigate_to'],
            'camera': ['detect_object'],
            'gripper': ['grasp_object', 'place_object']
        }

    def optimize_sequence(self, sequence: ROSActionSequence, objective: str = 'time') -> ROSActionSequence:
        """Optimize action sequence based on objective"""
        actions = sequence.actions

        if objective == 'time':
            optimized_actions = self._optimize_for_time(actions)
        elif objective == 'resource_utilization':
            optimized_actions = self._optimize_for_resource_utilization(actions)
        elif objective == 'safety':
            optimized_actions = self._optimize_for_safety(actions)
        else:
            optimized_actions = actions  # No optimization

        return ROSActionSequence(
            sequence_id=f"optimized_{sequence.sequence_id}",
            name=f"optimized_{sequence.name}",
            actions=optimized_actions,
            created_at=time.time(),
            metadata={
                **sequence.metadata,
                "optimization_applied": objective,
                "optimization_timestamp": time.time()
            }
        )

    def _optimize_for_time(self, actions: List[ROSAction]) -> List[ROSAction]:
        """Optimize sequence for minimum execution time"""
        # For time optimization, we might want to:
        # 1. Group similar actions to reduce setup time
        # 2. Parallelize actions that use different resources

        # Simple approach: group actions by type
        navigation_actions = [a for a in actions if a.action_type == ROSActionType.NAVIGATION]
        manipulation_actions = [a for a in actions if a.action_type == ROSActionType.MANIPULATION]
        perception_actions = [a for a in actions if a.action_type == ROSActionType.PERCEPTION]
        control_actions = [a for a in actions if a.action_type == ROSActionType.CONTROL]
        other_actions = [a for a in actions if a.action_type not in [ROSActionType.NAVIGATION,
                                                                      ROSActionType.MANIPULATION,
                                                                      ROSActionType.PERCEPTION,
                                                                      ROSActionType.CONTROL]]

        # Arrange in logical order: navigate -> perceive -> manipulate -> control
        return navigation_actions + perception_actions + manipulation_actions + control_actions + other_actions

    def _optimize_for_resource_utilization(self, actions: List[ROSAction]) -> List[ROSAction]:
        """Optimize sequence for resource utilization"""
        # Schedule actions to maximize resource utilization
        # This would involve more complex resource allocation algorithms

        # For now, just return the original sequence
        # In practice, this would use algorithms like bin packing for resource allocation
        return actions

    def _optimize_for_safety(self, actions: List[ROSAction]) -> List[ROSAction]:
        """Optimize sequence for safety"""
        # Safety optimization might involve:
        # 1. Performing safety checks before critical actions
        # 2. Slowing down certain actions
        # 3. Adding verification steps

        # For now, we'll prioritize actions with higher safety ratings
        # (indicated by higher confidence)
        return sorted(actions, key=lambda x: x.parameters.get('safety_rating', 0.5), reverse=True)


def main():
    """Example usage of the ROS Action Generator"""
    print("ROS 2 Action Sequence Generator Example")

    # Initialize the generator
    generator = ROSActionGenerator()

    # Example plan steps from the cognitive planner
    example_plan_steps = [
        {
            "action": "navigate_to",
            "target": "kitchen",
            "parameters": {
                "location": "kitchen",
                "precision": "high"
            },
            "description": "Navigate to the kitchen area",
            "confidence": 0.9
        },
        {
            "action": "detect_object",
            "target": "red cup",
            "parameters": {
                "object_name": "red cup",
                "min_confidence": 0.8
            },
            "description": "Detect the red cup in the kitchen",
            "confidence": 0.85
        },
        {
            "action": "grasp_object",
            "target": "red cup",
            "parameters": {
                "object_id": "red cup",
                "grip_force": 60.0
            },
            "description": "Grasp the red cup",
            "confidence": 0.8
        },
        {
            "action": "navigate_to",
            "target": "living_room",
            "parameters": {
                "location": "living_room",
                "speed": "normal"
            },
            "description": "Navigate to the living room",
            "confidence": 0.9
        },
        {
            "action": "place_object",
            "target": "red cup",
            "parameters": {
                "object_id": "red cup",
                "place_location": "coffee_table"
            },
            "description": "Place the red cup on the coffee table",
            "confidence": 0.85
        }
    ]

    print("\n--- Action Sequence Generation ---")
    result = generator.generate_action_sequence(example_plan_steps)

    if result.success and result.action_sequence:
        seq = result.action_sequence
        print(f"Action sequence generated successfully!")
        print(f"  Sequence ID: {seq.sequence_id}")
        print(f"  Number of actions: {len(seq.actions)}")
        print(f"  Confidence: {result.confidence:.3f}")

        print("\n  Generated Actions:")
        for i, action in enumerate(seq.actions):
            print(f"    {i+1}. {action.action_name}")
            print(f"        Type: {action.action_type.value}")
            print(f"        Package: {action.package}")
            print(f"        Node: {action.node_name}")
            print(f"        Parameters: {action.parameters}")
            print(f"        Timeout: {action.timeout}s")

        # Example: Optimizing the sequence
        print(f"\n--- Action Sequence Optimization ---")
        optimizer = ActionSequenceOptimizer()

        # Optimize for time
        time_optimized = optimizer.optimize_sequence(seq, 'time')
        print(f"Time-optimized sequence has {len(time_optimized.actions)} actions")

        # Optimize for safety
        safety_optimized = optimizer.optimize_sequence(seq, 'safety')
        print(f"Safety-optimized sequence has {len(safety_optimized.actions)} actions")

        # Example: Simulating execution
        print(f"\n--- Action Sequence Simulation ---")
        ros_interface = ROSInterface()
        execution_result = ros_interface.execute_action_sequence(seq)

        print(f"Simulation completed:")
        print(f"  Success: {execution_result['success']}")
        print(f"  Total time: {execution_result['total_execution_time']:.2f}s")
        print(f"  Sequence ID: {execution_result['sequence_id']}")

        # Show individual action results
        for i, result in enumerate(execution_result['results'][:3]):  # Show first 3
            print(f"    Action {i+1}: {result['status'].value} in {result['execution_time']:.2f}s")

        if len(execution_result['results']) > 3:
            print(f"    ... and {len(execution_result['results']) - 3} more actions")

    else:
        print(f"Action generation failed: {result.errors}")
        if result.warnings:
            print(f"Warnings: {result.warnings}")

    # Example: Compound action sequence
    print(f"\n--- Compound Action Sequence Example ---")
    sub_sequence_1 = ROSActionSequence(
        sequence_id="seq_1",
        name="navigation_phase",
        actions=seq.actions[:2],  # First two actions
        created_at=time.time(),
        metadata={"phase": "navigation"}
    )

    sub_sequence_2 = ROSActionSequence(
        sequence_id="seq_2",
        name="manipulation_phase",
        actions=seq.actions[2:],  # Remaining actions
        created_at=time.time(),
        metadata={"phase": "manipulation"}
    )

    compound_result = generator.generate_compound_action_sequence(
        "fetch_and_deliver_cup", [sub_sequence_1, sub_sequence_2]
    )

    if compound_result.success and compound_result.action_sequence:
        comp_seq = compound_result.action_sequence
        print(f"Compound sequence generated:")
        print(f"  ID: {comp_seq.sequence_id}")
        print(f"  Actions: {len(comp_seq.actions)}")
        print(f"  Subsequences: {comp_seq.metadata['num_subsequences']}")

    print("\nROS 2 Action Sequence Generator example completed!")


if __name__ == "__main__":
    main()