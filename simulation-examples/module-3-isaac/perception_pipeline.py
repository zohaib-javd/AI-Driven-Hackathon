#!/usr/bin/env python3
"""
Module 3: Isaac ROS Perception Pipeline
Physical AI & Humanoid Robotics Textbook

This example demonstrates the perception pipeline integration with:
- NVIDIA Isaac ROS DNN Inference
- Object Detection (YOLO/SSD)
- Depth Estimation
- Semantic Segmentation
- AprilTag Detection for ground truth

Usage:
    ros2 run my_robot_pkg perception_pipeline

Prerequisites:
    - ROS 2 Humble
    - Isaac ROS packages
    - NVIDIA GPU with CUDA
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, CameraInfo
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from geometry_msgs.msg import PoseStamped, TransformStamped
from tf2_ros import TransformBroadcaster
from cv_bridge import CvBridge
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class DetectedObject:
    """Represents a detected object with 3D position."""
    class_name: str
    confidence: float
    bbox_2d: Tuple[int, int, int, int]  # x, y, width, height
    position_3d: Optional[Tuple[float, float, float]] = None
    distance: float = 0.0


class PerceptionPipeline(Node):
    """
    Integrated perception pipeline for humanoid robot.

    Combines multiple perception modalities:
    - RGB camera for object detection
    - Depth camera for 3D localization
    - Semantic segmentation for scene understanding
    """

    # Class labels for COCO dataset (common for YOLO/SSD)
    COCO_CLASSES = {
        0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle',
        39: 'bottle', 41: 'cup', 42: 'fork', 43: 'knife',
        44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple',
        56: 'chair', 57: 'couch', 58: 'potted_plant', 59: 'bed',
        60: 'dining_table', 62: 'tv', 63: 'laptop', 64: 'mouse',
        65: 'remote', 66: 'keyboard', 67: 'cell_phone', 73: 'book',
    }

    # Objects of interest for manipulation tasks
    GRASPABLE_OBJECTS = {'cup', 'bottle', 'apple', 'banana', 'remote', 'book', 'cell_phone'}

    def __init__(self):
        super().__init__('perception_pipeline')

        # Configuration
        self.declare_parameter('detection_threshold', 0.5)
        self.declare_parameter('depth_scale', 1000.0)  # mm to meters
        self.declare_parameter('camera_frame', 'camera_link')

        self.detection_threshold = self.get_parameter('detection_threshold').value
        self.depth_scale = self.get_parameter('depth_scale').value
        self.camera_frame = self.get_parameter('camera_frame').value

        # CV Bridge
        self.bridge = CvBridge()

        # TF Broadcaster for object positions
        self.tf_broadcaster = TransformBroadcaster(self)

        # State
        self.latest_rgb: Optional[np.ndarray] = None
        self.latest_depth: Optional[np.ndarray] = None
        self.camera_info: Optional[CameraInfo] = None
        self.detected_objects: List[DetectedObject] = []

        # QoS for sensor data
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # Subscribers
        self.rgb_sub = self.create_subscription(
            Image,
            '/camera/color/image_raw',
            self.rgb_callback,
            sensor_qos
        )

        self.depth_sub = self.create_subscription(
            Image,
            '/camera/aligned_depth_to_color/image_raw',
            self.depth_callback,
            sensor_qos
        )

        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            '/camera/color/camera_info',
            self.camera_info_callback,
            10
        )

        # Subscribe to Isaac ROS detection output
        self.detection_sub = self.create_subscription(
            Detection2DArray,
            '/detectnet/detections',
            self.detection_callback,
            10
        )

        # Publishers
        self.object_poses_pub = self.create_publisher(
            PoseStamped,
            '/perception/object_pose',
            10
        )

        # Timer for processing
        self.create_timer(0.1, self.process_perception)

        self.get_logger().info('Perception Pipeline initialized')
        self.get_logger().info(f'Detection threshold: {self.detection_threshold}')

    def rgb_callback(self, msg: Image):
        """Receive RGB image."""
        try:
            self.latest_rgb = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'RGB conversion error: {e}')

    def depth_callback(self, msg: Image):
        """Receive depth image."""
        try:
            if msg.encoding == '16UC1':
                self.latest_depth = self.bridge.imgmsg_to_cv2(msg, '16UC1')
            elif msg.encoding == '32FC1':
                depth_float = self.bridge.imgmsg_to_cv2(msg, '32FC1')
                self.latest_depth = (depth_float * self.depth_scale).astype(np.uint16)
            else:
                self.get_logger().warn(f'Unknown depth encoding: {msg.encoding}')
        except Exception as e:
            self.get_logger().error(f'Depth conversion error: {e}')

    def camera_info_callback(self, msg: CameraInfo):
        """Receive camera intrinsics."""
        self.camera_info = msg

    def detection_callback(self, msg: Detection2DArray):
        """Process detections from Isaac ROS DetectNet."""
        self.detected_objects.clear()

        for detection in msg.detections:
            # Get best hypothesis
            if not detection.results:
                continue

            best = max(detection.results, key=lambda r: r.hypothesis.score)

            if best.hypothesis.score < self.detection_threshold:
                continue

            # Get class name
            class_id = int(best.hypothesis.class_id) if best.hypothesis.class_id.isdigit() else -1
            class_name = self.COCO_CLASSES.get(class_id, best.hypothesis.class_id)

            # Get bounding box
            bbox = detection.bbox
            x = int(bbox.center.position.x - bbox.size_x / 2)
            y = int(bbox.center.position.y - bbox.size_y / 2)
            w = int(bbox.size_x)
            h = int(bbox.size_y)

            obj = DetectedObject(
                class_name=class_name,
                confidence=best.hypothesis.score,
                bbox_2d=(x, y, w, h)
            )

            self.detected_objects.append(obj)

    def process_perception(self):
        """Main perception processing loop."""
        if not self.detected_objects:
            return

        if self.latest_depth is None or self.camera_info is None:
            return

        # Camera intrinsics
        fx = self.camera_info.k[0]
        fy = self.camera_info.k[4]
        cx = self.camera_info.k[2]
        cy = self.camera_info.k[5]

        for obj in self.detected_objects:
            # Get depth at object center
            x, y, w, h = obj.bbox_2d
            center_x = x + w // 2
            center_y = y + h // 2

            # Sample depth in a small region for robustness
            depth_region = self.latest_depth[
                max(0, center_y - 5):min(self.latest_depth.shape[0], center_y + 5),
                max(0, center_x - 5):min(self.latest_depth.shape[1], center_x + 5)
            ]

            valid_depths = depth_region[depth_region > 0]
            if len(valid_depths) == 0:
                continue

            depth_mm = np.median(valid_depths)
            depth_m = depth_mm / self.depth_scale

            # Convert to 3D coordinates (camera frame)
            z = depth_m
            x_3d = (center_x - cx) * z / fx
            y_3d = (center_y - cy) * z / fy

            obj.position_3d = (x_3d, y_3d, z)
            obj.distance = math.sqrt(x_3d**2 + y_3d**2 + z**2)

            # Publish object pose
            self.publish_object_pose(obj)

            # Broadcast TF for visualization
            self.broadcast_object_tf(obj)

        # Log detected objects
        self.log_detections()

    def publish_object_pose(self, obj: DetectedObject):
        """Publish object pose as PoseStamped."""
        if obj.position_3d is None:
            return

        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = self.camera_frame

        pose.pose.position.x = obj.position_3d[0]
        pose.pose.position.y = obj.position_3d[1]
        pose.pose.position.z = obj.position_3d[2]

        # Identity orientation (facing camera)
        pose.pose.orientation.w = 1.0

        self.object_poses_pub.publish(pose)

    def broadcast_object_tf(self, obj: DetectedObject):
        """Broadcast object position as TF for RViz visualization."""
        if obj.position_3d is None:
            return

        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = self.camera_frame
        t.child_frame_id = f'detected_{obj.class_name}'

        t.transform.translation.x = obj.position_3d[0]
        t.transform.translation.y = obj.position_3d[1]
        t.transform.translation.z = obj.position_3d[2]
        t.transform.rotation.w = 1.0

        self.tf_broadcaster.sendTransform(t)

    def log_detections(self):
        """Log detected objects summary."""
        if not self.detected_objects:
            return

        graspable = [o for o in self.detected_objects if o.class_name in self.GRASPABLE_OBJECTS]
        humans = [o for o in self.detected_objects if o.class_name == 'person']

        self.get_logger().info(
            f'Detected: {len(self.detected_objects)} objects, '
            f'{len(graspable)} graspable, {len(humans)} humans'
        )

        # Log closest graspable object
        if graspable:
            closest = min(graspable, key=lambda o: o.distance if o.distance > 0 else float('inf'))
            if closest.position_3d:
                self.get_logger().info(
                    f'Closest graspable: {closest.class_name} at {closest.distance:.2f}m '
                    f'({closest.confidence*100:.1f}% confidence)'
                )

    def get_closest_object(self, class_filter: Optional[str] = None) -> Optional[DetectedObject]:
        """Get the closest detected object, optionally filtered by class."""
        candidates = self.detected_objects

        if class_filter:
            candidates = [o for o in candidates if o.class_name == class_filter]

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda o: o.distance if o.distance > 0 else float('inf')
        )


def main(args=None):
    """Run perception pipeline node."""
    rclpy.init(args=args)

    node = PerceptionPipeline()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down perception pipeline')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
