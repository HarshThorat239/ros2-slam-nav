import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
import math

class PatrolNode(Node):

    def __init__(self):
        super().__init__('patrol_node')

        self._client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Three waypoints spread around the TurtleBot3 world
        self.waypoints = [
            (1.5,  0.0),
            (0.0,  1.5),
            (-1.5, 0.0),
        ]

        self.current = 0
        self.get_logger().info('Patrol node started — waiting for Nav2...')
        self._client.wait_for_server()
        self.get_logger().info('Nav2 ready — starting patrol!')
        self.send_goal()

    def send_goal(self):
        x, y = self.waypoints[self.current]
        self.get_logger().info(f'Heading to waypoint {self.current + 1}: ({x}, {y})')

        goal = NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.w = 1.0
        goal.pose = pose

        self._client.send_goal_async(goal).add_done_callback(self.goal_accepted)

    def goal_accepted(self, future):
        handle = future.result()
        handle.get_result_async().add_done_callback(self.goal_reached)

    def goal_reached(self, future):
        self.get_logger().info(f'Reached waypoint {self.current + 1}!')
        self.current = (self.current + 1) % len(self.waypoints)
        self.send_goal()


def main(args=None):
    rclpy.init(args=args)
    node = PatrolNode()
    rclpy.spin(node)


if __name__ == '__main__':
    main()