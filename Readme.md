# ROS2 SLAM + Autonomous Navigation in Gazebo

A fully autonomous robot simulation built with ROS2. The robot starts in an unknown environment with no map, builds one using LiDAR and SLAM, then navigates to goals and patrols waypoints completely on its own — no keyboard, no joystick.

This is the same core architecture used in warehouse robots, autonomous vacuum cleaners, and self-driving vehicles.

---

## Demo

The robot goes through three stages:

1. Explores an unknown room and builds a map from scratch using LiDAR
2. Navigates autonomously to any goal point on the map
3. Patrols three waypoints in an infinite loop using a custom ROS2 node

---

## How it works

```
LiDAR sensor readings
        ↓
   SLAM Toolbox  →  builds the occupancy grid map
        ↓
   Nav2 stack    →  plans and executes paths on that map
        ↓
 patrol.py node  →  decides which goals to go to and when
```

Everything runs on ROS2 — a messaging framework where each component (sensor, mapper, planner, controller) runs as its own process and communicates by publishing and subscribing to topics.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| ROS2 Humble | Robot operating framework |
| Gazebo | Physics simulation |
| RViz2 | Visualisation |
| SLAM Toolbox | Graph-based LiDAR SLAM |
| Nav2 | Autonomous navigation stack |
| TurtleBot3 | Robot model (Waffle Pi) |

---

## Project Structure

```
ros2-slam-nav/
├── src/
│   └── my_robot/
│       ├── my_robot/
│       │   ├── __init__.py
│       │   └── patrol.py       ← custom patrol node
│       ├── launch/
│       ├── resource/
│       ├── package.xml
│       ├── setup.cfg
│       └── setup.py
├── maps/
│   ├── turtlebot3_world.pgm    ← saved map image
│   └── turtlebot3_world.yaml   ← map metadata
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## The Three Phases

### Phase 1 — SLAM (build the map)

The robot starts with zero knowledge of its environment. SLAM Toolbox listens to the LiDAR sensor, which shoots laser beams in all directions and measures how far they travel before hitting a wall or object. From those readings it builds an occupancy grid — a 2D map where every cell is marked free, occupied, or unknown.

The hard part: to build a map you need to know where you are, but to know where you are you need a map. SLAM solves both simultaneously.

```bash
# Terminal 1 — launch simulation
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# Terminal 2 — start SLAM
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true

# Terminal 3 — drive the robot to explore
ros2 run turtlebot3_teleop teleop_keyboard

# Terminal 4 — save the map when done
ros2 run nav2_map_server map_saver_cli -f maps/turtlebot3_world
```

### Phase 2 — Nav2 (autonomous navigation)

Load the saved map and send the robot to any goal. The Nav2 stack handles two layers:

- **Global planner** — looks at the whole map and plots the shortest safe route, like Google Maps
- **Local controller** — executes the route in real time, swerving around obstacles that appear suddenly

```bash
# Terminal 1 — launch simulation
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# Terminal 2 — launch Nav2 with saved map
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
  use_sim_time:=true \
  map:=maps/turtlebot3_world.yaml
```

Then in RViz2:
1. Click **2D Pose Estimate** and set the robot's starting position
2. Click **Nav2 Goal** and watch the robot drive there on its own

### Phase 3 — Behaviour Tree (patrol logic)

A custom ROS2 node (`patrol.py`) gives the robot decision-making logic. Instead of waiting for a human to click goals, the robot patrols three waypoints in an infinite loop automatically.

```bash
# Build the package
colcon build --packages-select my_robot
source install/setup.bash

# Run the patrol node (with Gazebo + Nav2 already running)
ros2 run my_robot patrol
```

The node connects to Nav2's `navigate_to_pose` action and loops through three waypoints indefinitely. It also subscribes to the `/scan` LiDAR topic — if any object is detected within 0.3m directly ahead, the robot reverses, stops, and waits for the path to clear before resuming patrol automatically.

---

## Setup and Installation

### Prerequisites

- Ubuntu 22.04 (or WSL2 with Ubuntu 22.04)
- ROS2 Humble
- TurtleBot3 packages
- SLAM Toolbox
- Nav2

### Install dependencies

```bash
sudo apt update
sudo apt install ros-humble-turtlebot3* \
                 ros-humble-slam-toolbox \
                 ros-humble-navigation2 \
                 ros-humble-nav2-bringup \
                 python3-colcon-common-extensions
```

### Environment setup

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle_pi

# Add to ~/.bashrc to persist
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "export TURTLEBOT3_MODEL=waffle_pi" >> ~/.bashrc
```

### Clone and build

```bash
git clone https://github.com/your-username/ros2-slam-nav.git
cd ros2-slam-nav
colcon build --packages-select my_robot
source install/setup.bash
```

---

## Running with Docker

The easiest way to run this project without installing ROS2 manually.

### Prerequisites

- Docker
- Docker Compose
- An X11 display server
  - **Windows (WSL2):** Install [VcXsrv](https://sourceforge.net/projects/vcxsrv/) and launch it with "Disable access control" checked
  - **Linux:** X11 is built in

### Run

```bash
git clone https://github.com/your-username/ros2-slam-nav.git
cd ros2-slam-nav
docker compose up --build
```

Then in separate terminals:

```bash
# Terminal 1 — Gazebo simulation
docker exec -it ros2_slam_nav bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# Terminal 2 — Nav2 with saved map
docker exec -it ros2_slam_nav bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
  use_sim_time:=true \
  map:=/ros2_ws/maps/turtlebot3_world.yaml

# Terminal 3 — Patrol node
docker exec -it ros2_slam_nav bash
ros2 run my_robot patrol
```

---

## Key Concepts

**Occupancy grid** — the map format used by SLAM and Nav2. Every cell is one of three states: free (white), occupied (black), or unknown (grey). Each cell represents a 5cm × 5cm area of the real world.

**Graph-based SLAM** — as the robot moves, SLAM Toolbox creates nodes (snapshots of position + LiDAR scan) connected by edges (movement between positions). When the robot revisits a known location, loop closure corrects any accumulated drift.

**Action server** — Nav2 exposes navigation as a ROS2 action, meaning you can send a goal, get feedback while it's executing, and a result when it's done. The patrol node uses this interface to chain waypoints together.

---

## What's next

- Expand to more waypoints
- Test with a different Gazebo world
- Port to real hardware