FROM osrf/ros:humble-desktop

# Install all dependencies
RUN apt-get update && apt-get install -y \
    ros-humble-turtlebot3* \
    ros-humble-slam-toolbox \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# Set environment
ENV TURTLEBOT3_MODEL=waffle_pi
ENV ROS_DOMAIN_ID=0

# Create workspace and copy project
WORKDIR /ros2_ws
COPY . /ros2_ws/

# Build the package
RUN bash -c "source /opt/ros/humble/setup.bash && colcon build --packages-select my_robot"

# Source everything on startup
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> ~/.bashrc && \
    echo "export TURTLEBOT3_MODEL=waffle_pi" >> ~/.bashrc