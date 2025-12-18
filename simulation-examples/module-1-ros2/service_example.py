#!/usr/bin/env python3
"""
Module 1: ROS 2 Services - Request/Response Example
Physical AI & Humanoid Robotics Textbook

This example demonstrates ROS 2 services for synchronous
request/response communication between nodes.

Usage:
    # Terminal 1 - Run the service server
    python service_example.py server

    # Terminal 2 - Run the service client
    python service_example.py client 5 3

Prerequisites:
    - ROS 2 Humble or later
    - Python 3.10+
"""

import rclpy
from rclpy.node import Node
from example_interfaces.srv import AddTwoInts


class AddTwoIntsServer(Node):
    """Service server that adds two integers."""

    def __init__(self):
        super().__init__('add_two_ints_server')

        # Create service
        self.srv = self.create_service(
            AddTwoInts,
            'add_two_ints',
            self.add_two_ints_callback
        )

        self.get_logger().info('Add Two Ints Service is ready')
        self.get_logger().info('Service name: /add_two_ints')

    def add_two_ints_callback(self, request, response):
        """Service callback - adds two integers and returns the sum."""
        response.sum = request.a + request.b

        self.get_logger().info(
            f'Request received: {request.a} + {request.b} = {response.sum}'
        )

        return response


class AddTwoIntsClient(Node):
    """Service client that sends requests to add two integers."""

    def __init__(self):
        super().__init__('add_two_ints_client')

        # Create client
        self.client = self.create_client(AddTwoInts, 'add_two_ints')

        # Wait for service to be available
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for service...')

        self.get_logger().info('Service found!')

    def send_request(self, a: int, b: int) -> int:
        """Send a request to the service and return the result."""
        # Create request
        request = AddTwoInts.Request()
        request.a = a
        request.b = b

        self.get_logger().info(f'Sending request: {a} + {b}')

        # Call service (synchronously)
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        result = future.result()
        self.get_logger().info(f'Result: {result.sum}')

        return result.sum


class RobotCommandService(Node):
    """Example: A more practical service for robot commands."""

    def __init__(self):
        super().__init__('robot_command_service')

        # This would use a custom service type in a real application
        # For demonstration, we'll create a simple command handler
        self.commands_received = 0

        self.get_logger().info('Robot Command Service initialized')

    def handle_command(self, command: str) -> dict:
        """Handle a robot command and return status."""
        self.commands_received += 1

        valid_commands = ['move_forward', 'move_backward', 'turn_left',
                         'turn_right', 'stop', 'grab', 'release']

        if command in valid_commands:
            self.get_logger().info(f'Executing command: {command}')
            return {
                'success': True,
                'message': f'Command "{command}" executed',
                'command_id': self.commands_received
            }
        else:
            self.get_logger().warning(f'Unknown command: {command}')
            return {
                'success': False,
                'message': f'Unknown command: {command}',
                'command_id': self.commands_received
            }


def run_server():
    """Run the service server."""
    rclpy.init()
    node = AddTwoIntsServer()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Server shutting down')
    finally:
        node.destroy_node()
        rclpy.shutdown()


def run_client(a: int, b: int):
    """Run the service client with given numbers."""
    rclpy.init()
    node = AddTwoIntsClient()

    try:
        result = node.send_request(a, b)
        print(f'Result: {a} + {b} = {result}')
    except Exception as e:
        node.get_logger().error(f'Service call failed: {e}')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Server: python service_example.py server")
        print("  Client: python service_example.py client <a> <b>")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == 'server':
        run_server()
    elif mode == 'client':
        if len(sys.argv) != 4:
            print("Usage: python service_example.py client <a> <b>")
            sys.exit(1)
        try:
            a = int(sys.argv[2])
            b = int(sys.argv[3])
            run_client(a, b)
        except ValueError:
            print("Error: a and b must be integers")
            sys.exit(1)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
