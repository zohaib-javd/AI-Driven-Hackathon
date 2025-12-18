#!/usr/bin/env python3
"""
Module 1: ROS 2 Basics - Simple Node Example
Physical AI & Humanoid Robotics Textbook

This example demonstrates creating a basic ROS 2 node using rclpy.
It publishes a counter message to a topic every second.

Usage:
    ros2 run my_robot_pkg simple_node

Prerequisites:
    - ROS 2 Humble or later
    - Python 3.10+
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, String


class SimpleCounterNode(Node):
    """A simple ROS 2 node that publishes a counter value.

    This node demonstrates the fundamental concepts of ROS 2:
    - Node creation
    - Publishing messages to topics
    - Using timers for periodic callbacks
    - Logging
    """

    def __init__(self):
        # Initialize the node with name 'simple_counter'
        super().__init__('simple_counter')

        # Create a publisher
        # Topic: /counter
        # Message type: Int32
        # Queue size: 10
        self.publisher_ = self.create_publisher(Int32, 'counter', 10)

        # Create a timer (1 second interval)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

        # Initialize counter
        self.count = 0

        # Log startup message
        self.get_logger().info('Simple Counter Node has started!')
        self.get_logger().info('Publishing to topic: /counter')

    def timer_callback(self):
        """Timer callback function - executes every second."""
        # Create message
        msg = Int32()
        msg.data = self.count

        # Publish message
        self.publisher_.publish(msg)

        # Log the published value
        self.get_logger().info(f'Published: {self.count}')

        # Increment counter
        self.count += 1


def main(args=None):
    """Main entry point for the ROS 2 node."""
    # Initialize ROS 2 Python client library
    rclpy.init(args=args)

    # Create our node
    node = SimpleCounterNode()

    try:
        # Spin the node (keeps it running and processing callbacks)
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Node stopped by user')
    finally:
        # Clean up
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
