import rclpy
import time
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, Twist
from sensor_msgs.msg import LaserScan

class PatrolNode(Node):

    def __init__(self):
        super().__init__('patrol_node')
        

        self._client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Three waypoints spread around the TurtleBot3 world
        self.waypoints = [
            (0.5,  0.0),
            (0.0,  0.5),
            (-0.5, 0.0),
        ]

        self.current = 0
        self.obstacle_detected = False
        self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.get_logger().info('Patrol node started — waiting for Nav2...')
        self._cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
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
         result = future.result()
         status = result.status

         if status == 4:  # 4 = SUCCEEDED
                self.get_logger().info(f'Reached waypoint {self.current + 1}!')
                self.current = (self.current + 1) % len(self.waypoints)
                self.send_goal()
         else:
                self.get_logger().warn(f'Goal failed with status {status}, retrying...')
                time.sleep(1.0)
                self.send_goal()

    def scan_callback(self, msg):
         # check if any obstacles are within 0.3m in front of the robot
         total = len(msg.ranges)
         front = list(msg.ranges[:30]) + list(msg.ranges[-30:])
    
         for distance in front:
            if 0 < distance < 0.3:
                if not self.obstacle_detected:
                 self.get_logger().warn('Obstacle ahead! Stopping...')
                 self.obstacle_detected = True
                 self.reverse_robot()
                return

         if self.obstacle_detected:
            self.obstacle_detected = False
            self.get_logger().info('Obstacle cleared — resuming!')
            self.send_goal()
        
    def reverse_robot(self):
        twist = Twist()
        twist.linear.x = -0.2  # Move backward
        self._cmd_pub.publish(twist)
        time.sleep(1.0)  # Move back for 1 second
        self.stop_robot()  # Stop after reversing

    def stop_robot(self):
        twist = Twist()
        self._cmd_pub.publish(twist)

        

def main(args=None):
    rclpy.init(args=args)
    node = PatrolNode()
    rclpy.spin(node)


if __name__ == '__main__':
    main()