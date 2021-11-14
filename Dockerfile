FROM duckietown/rpi-duckiebot-base
 
#
# Identify the maintainer of an image
LABEL maintainer="Juan Miguel Serrano Rodríguez (juan11iguel@gmail.com)"
 
#
# Copy seed file to calibrations folder 
COPY duckiebot_random_seed.yaml in /data/config/calibrations/

# Copy modified inverse_kinematics_node program
COPY inverse_kinematics_node in /home/software/catkin_ws/src/06-kinematics/dagu_car/src/ 

# Copy modified lane_controller_node program
COPY lane_controller_node in /home/software/catkin_ws/src/10-lane-control/lane_control/scripts/