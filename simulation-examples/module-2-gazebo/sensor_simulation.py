#!/usr/bin/env python3
"""
Module 2: Digital Twin - Sensor Simulation Example
Physical AI & Humanoid Robotics Textbook

This example demonstrates simulated sensor data processing for:
- LiDAR (distance measurements)
- IMU (orientation and acceleration)
- RGB-D Camera (color and depth)

These sensors form the perception foundation for humanoid robots.

Usage:
    ros2 run my_robot_pkg sensor_simulation

Prerequisites:
    - ROS 2 Humble or later
    - Gazebo with robot model spawned
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Imu, Image, CameraInfo
from geometry_msgs.msg import Vector3, Quaternion
from cv_bridge import CvBridge
import numpy as np
import math


class LidarProcessor(Node):
    """Process LiDAR scan data for obstacle detection."""

    def __init__(self):
        super().__init__('lidar_processor')

        # Subscribe to laser scan
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        # Configuration
        self.obstacle_threshold = 1.0  # meters
        self.sector_count = 8  # Divide 360° into sectors

        self.get_logger().info('LiDAR Processor started')

    def scan_callback(self, msg: LaserScan):
        """Process incoming laser scan data."""
        ranges = np.array(msg.ranges)

        # Replace inf values with max range
        ranges = np.where(np.isinf(ranges), msg.range_max, ranges)

        # Find minimum distance
        min_distance = np.min(ranges)
        min_angle_idx = np.argmin(ranges)
        min_angle = msg.angle_min + min_angle_idx * msg.angle_increment

        # Divide into sectors for directional awareness
        sector_size = len(ranges) // self.sector_count
        sectors = {}
        sector_names = ['Front', 'Front-Right', 'Right', 'Back-Right',
                       'Back', 'Back-Left', 'Left', 'Front-Left']

        for i in range(self.sector_count):
            start = i * sector_size
            end = start + sector_size
            sector_ranges = ranges[start:end]
            sector_min = np.min(sector_ranges)
            sectors[sector_names[i]] = sector_min

        # Log obstacle warnings
        if min_distance < self.obstacle_threshold:
            direction = sector_names[min_angle_idx // sector_size]
            self.get_logger().warn(
                f'Obstacle detected! Distance: {min_distance:.2f}m, '
                f'Direction: {direction}'
            )

        # Log sector summary
        self.get_logger().info(
            f'Sector distances: '
            f'F:{sectors["Front"]:.2f} R:{sectors["Right"]:.2f} '
            f'B:{sectors["Back"]:.2f} L:{sectors["Left"]:.2f}'
        )


class IMUProcessor(Node):
    """Process IMU data for robot orientation and balance."""

    def __init__(self):
        super().__init__('imu_processor')

        # Subscribe to IMU data
        self.subscription = self.create_subscription(
            Imu,
            '/imu/data',
            self.imu_callback,
            10
        )

        # State tracking
        self.is_tilted = False
        self.tilt_threshold = 15.0  # degrees

        self.get_logger().info('IMU Processor started')

    def imu_callback(self, msg: Imu):
        """Process IMU data for orientation."""
        # Extract orientation quaternion
        q = msg.orientation
        roll, pitch, yaw = self.quaternion_to_euler(q.x, q.y, q.z, q.w)

        # Convert to degrees
        roll_deg = math.degrees(roll)
        pitch_deg = math.degrees(pitch)
        yaw_deg = math.degrees(yaw)

        # Check for dangerous tilt
        total_tilt = math.sqrt(roll_deg**2 + pitch_deg**2)

        if total_tilt > self.tilt_threshold:
            if not self.is_tilted:
                self.get_logger().warn(
                    f'Robot tilting! Roll: {roll_deg:.1f}°, Pitch: {pitch_deg:.1f}°'
                )
                self.is_tilted = True
        else:
            if self.is_tilted:
                self.get_logger().info('Robot stabilized')
                self.is_tilted = False

        # Extract linear acceleration
        accel = msg.linear_acceleration
        accel_magnitude = math.sqrt(accel.x**2 + accel.y**2 + accel.z**2)

        # Detect falls or impacts
        if accel_magnitude > 15.0:  # Significantly more than 9.81 m/s²
            self.get_logger().error(
                f'High acceleration detected! Magnitude: {accel_magnitude:.2f} m/s²'
            )

    @staticmethod
    def quaternion_to_euler(x, y, z, w):
        """Convert quaternion to Euler angles (roll, pitch, yaw)."""
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return roll, pitch, yaw


class DepthCameraProcessor(Node):
    """Process RGB-D camera data for perception."""

    def __init__(self):
        super().__init__('depth_camera_processor')

        self.bridge = CvBridge()

        # Subscribers
        self.rgb_sub = self.create_subscription(
            Image,
            '/camera/color/image_raw',
            self.rgb_callback,
            10
        )

        self.depth_sub = self.create_subscription(
            Image,
            '/camera/depth/image_raw',
            self.depth_callback,
            10
        )

        # State
        self.latest_rgb = None
        self.latest_depth = None

        self.get_logger().info('Depth Camera Processor started')

    def rgb_callback(self, msg: Image):
        """Process RGB image."""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            self.latest_rgb = cv_image

            # Log image stats
            height, width = cv_image.shape[:2]
            self.get_logger().debug(f'RGB frame received: {width}x{height}')

        except Exception as e:
            self.get_logger().error(f'RGB conversion error: {e}')

    def depth_callback(self, msg: Image):
        """Process depth image."""
        try:
            # Depth images are typically 16-bit or 32-bit float
            if msg.encoding == '16UC1':
                cv_depth = self.bridge.imgmsg_to_cv2(msg, '16UC1')
                # Convert from mm to meters
                depth_meters = cv_depth.astype(np.float32) / 1000.0
            elif msg.encoding == '32FC1':
                depth_meters = self.bridge.imgmsg_to_cv2(msg, '32FC1')
            else:
                self.get_logger().warn(f'Unknown depth encoding: {msg.encoding}')
                return

            self.latest_depth = depth_meters

            # Calculate scene statistics
            valid_depth = depth_meters[depth_meters > 0]
            if len(valid_depth) > 0:
                min_depth = np.min(valid_depth)
                max_depth = np.max(valid_depth)
                mean_depth = np.mean(valid_depth)

                # Get center depth (what's directly in front)
                h, w = depth_meters.shape
                center_depth = depth_meters[h//2, w//2]

                self.get_logger().info(
                    f'Depth: min={min_depth:.2f}m, max={max_depth:.2f}m, '
                    f'center={center_depth:.2f}m'
                )

        except Exception as e:
            self.get_logger().error(f'Depth conversion error: {e}')

    def get_obstacle_distance(self, x: int, y: int) -> float:
        """Get distance to obstacle at specific pixel coordinates."""
        if self.latest_depth is None:
            return -1.0

        h, w = self.latest_depth.shape
        if 0 <= x < w and 0 <= y < h:
            return float(self.latest_depth[y, x])
        return -1.0


class SensorFusion(Node):
    """Combine multiple sensor inputs for robust perception."""

    def __init__(self):
        super().__init__('sensor_fusion')

        # Sensor states
        self.lidar_obstacles = {}
        self.robot_orientation = (0.0, 0.0, 0.0)  # roll, pitch, yaw
        self.front_distance = 0.0

        # Subscribers
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10
        )
        self.imu_sub = self.create_subscription(
            Imu, '/imu/data', self.imu_callback, 10
        )

        # Timer for fusion updates
        self.create_timer(0.1, self.fusion_callback)

        self.get_logger().info('Sensor Fusion node started')

    def scan_callback(self, msg: LaserScan):
        """Update obstacle information from LiDAR."""
        ranges = np.array(msg.ranges)
        ranges = np.where(np.isinf(ranges), msg.range_max, ranges)

        # Front sector (approximately -30° to +30°)
        total_rays = len(ranges)
        front_start = total_rays // 12 * 11  # Start near 0°
        front_end = total_rays // 12

        front_ranges = np.concatenate([ranges[front_start:], ranges[:front_end]])
        self.front_distance = np.min(front_ranges)

    def imu_callback(self, msg: Imu):
        """Update robot orientation from IMU."""
        q = msg.orientation
        roll, pitch, yaw = self.quaternion_to_euler(q.x, q.y, q.z, q.w)
        self.robot_orientation = (roll, pitch, yaw)

    def fusion_callback(self):
        """Periodic sensor fusion update."""
        roll, pitch, yaw = self.robot_orientation

        # Determine robot state
        tilt = math.sqrt(roll**2 + pitch**2)
        is_stable = tilt < math.radians(10)
        is_path_clear = self.front_distance > 0.5

        status = []
        if is_stable:
            status.append('STABLE')
        else:
            status.append('UNSTABLE')

        if is_path_clear:
            status.append('PATH_CLEAR')
        else:
            status.append('OBSTACLE_AHEAD')

        self.get_logger().info(
            f'Status: {", ".join(status)} | '
            f'Front: {self.front_distance:.2f}m | '
            f'Tilt: {math.degrees(tilt):.1f}°'
        )

    @staticmethod
    def quaternion_to_euler(x, y, z, w):
        """Convert quaternion to Euler angles."""
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (w * y - z * x)
        pitch = math.asin(max(-1, min(1, sinp)))

        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return roll, pitch, yaw


def main(args=None):
    """Run sensor fusion node."""
    rclpy.init(args=args)

    node = SensorFusion()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
