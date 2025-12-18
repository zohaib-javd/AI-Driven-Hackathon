#!/usr/bin/env python3
"""
Module 1: ROS 2 Topics - Publisher/Subscriber Example
Physical AI & Humanoid Robotics Textbook

This example demonstrates the publisher/subscriber pattern in ROS 2,
which is the primary method for inter-node communication.

Usage:
    # Terminal 1 - Run the publisher
    ros2 run my_robot_pkg talker

    # Terminal 2 - Run the subscriber
    ros2 run my_robot_pkg listener

Prerequisites:
    - ROS 2 Humble or later
    - Python 3.10+
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist


class TalkerNode(Node):
    """Publisher node that sends messages to a topic."""

    def __init__(self):
        super().__init__('talker')

        # Create publisher for /chatter topic
        self.publisher_ = self.create_publisher(String, 'chatter', 10)

        # Create timer for periodic publishing
        self.timer = self.create_timer(0.5, self.publish_message)
        self.count = 0

        self.get_logger().info('Talker node started')

    def publish_message(self):
        """Publish a message to the chatter topic."""
        msg = String()
        msg.data = f'Hello, ROS 2! Message #{self.count}'

        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')

        self.count += 1


class ListenerNode(Node):
    """Subscriber node that receives messages from a topic."""

    def __init__(self):
        super().__init__('listener')

        # Create subscription to /chatter topic
        self.subscription = self.create_subscription(
            String,
            'chatter',
            self.message_callback,
            10  # Queue size
        )

        self.get_logger().info('Listener node started')

    def message_callback(self, msg: String):
        """Callback function for received messages."""
        self.get_logger().info(f'I heard: "{msg.data}"')


class VelocityPublisher(Node):
    """Example: Publishing velocity commands for robot movement."""

    def __init__(self):
        super().__init__('velocity_publisher')

        # Twist message for velocity commands
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.publish_velocity)

        # Movement parameters
        self.linear_speed = 0.5  # m/s
        self.angular_speed = 0.0  # rad/s

        self.get_logger().info('Velocity publisher started')
        self.get_logger().info('Publishing to /cmd_vel')

    def publish_velocity(self):
        """Publish velocity command."""
        msg = Twist()

        # Linear velocity (forward/backward)
        msg.linear.x = self.linear_speed
        msg.linear.y = 0.0
        msg.linear.z = 0.0

        # Angular velocity (rotation)
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = self.angular_speed

        self.publisher_.publish(msg)

    def set_velocity(self, linear: float, angular: float):
        """Set the velocity values."""
        self.linear_speed = linear
        self.angular_speed = angular
        self.get_logger().info(f'Velocity set: linear={linear}, angular={angular}')


def run_talker():
    """Run the talker (publisher) node."""
    rclpy.init()
    node = TalkerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


def run_listener():
    """Run the listener (subscriber) node."""
    rclpy.init()
    node = ListenerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


def run_velocity_demo():
    """Run a velocity command demo."""
    rclpy.init()
    node = VelocityPublisher()

    try:
        # Move forward for 3 seconds
        node.set_velocity(0.5, 0.0)
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Stop the robot
        node.set_velocity(0.0, 0.0)
        rclpy.spin_once(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == 'talker':
            run_talker()
        elif mode == 'listener':
            run_listener()
        elif mode == 'velocity':
            run_velocity_demo()
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python pubsub_example.py [talker|listener|velocity]")
    else:
        print("Usage: python pubsub_example.py [talker|listener|velocity]")
