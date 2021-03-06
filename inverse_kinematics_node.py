#!/usr/bin/env python
# -*- coding: utf_8 -*-
import rospy
from duckietown_msgs.msg import WheelsCmdStamped, Twist2DStamped, BoolStamped
from duckietown_msgs.srv import SetValueRequest, SetValueResponse, SetValue
from std_srvs.srv import EmptyRequest, EmptyResponse, Empty
from numpy import *
import yaml
import time
import os.path
from duckietown_utils import get_duckiefleet_root
import random

# Inverse Kinematics Node
# Author: Robert Katzschmann, Shih-Yuan Liu

class InverseKinematicsNode(object):
    def __init__(self):
        # Get node name and vehicle name
        self.node_name = rospy.get_name()
        self.veh_name = self.node_name.split("/")[1]

        # Set parameters using yaml file
        self.readParamFromFile()

        # Set local variable by reading parameters
        self.gain = self.setup_parameter("~gain", 0.6)
        self.trim = self.setup_parameter("~trim", 0.0)
        self.baseline = self.setup_parameter("~baseline", 0.1)
        self.radius = self.setup_parameter("~radius", 0.0318)
        self.k = self.setup_parameter("~k", 27.0)
        self.limit = self.setup_parameter("~limit", 1.0)
        self.limit_max = 1.0
        self.limit_min = 0.0

        self.v_max = 999.0     # TODO: Calculate v_max !
        self.omega_max = 999.0     # TODO: Calculate v_max !

        # Prepare services
        self.srv_set_gain = rospy.Service("~set_gain", SetValue, self.cbSrvSetGain)
        self.srv_set_trim = rospy.Service("~set_trim", SetValue, self.cbSrvSetTrim)
        self.srv_set_baseline = rospy.Service("~set_baseline", SetValue, self.cbSrvSetBaseline)
        self.srv_set_radius = rospy.Service("~set_radius", SetValue, self.cbSrvSetRadius)
        self.srv_set_k = rospy.Service("~set_k", SetValue, self.cbSrvSetK)
        self.srv_set_limit = rospy.Service("~set_limit", SetValue, self.cbSrvSetLimit)
        self.srv_save = rospy.Service("~save_calibration", Empty, self.cbSrvSaveCalibration)

        # Setup the publisher and subscriber
        self.sub_car_cmd = rospy.Subscriber("~car_cmd", Twist2DStamped, self.car_cmd_callback)
        self.sub_actuator_limits_received = rospy.Subscriber("~actuator_limits_received", BoolStamped, self.updateActuatorLimitsReceived, queue_size=1)
        self.pub_wheels_cmd = rospy.Publisher("~wheels_cmd", WheelsCmdStamped, queue_size=1)
        self.pub_actuator_limits = rospy.Publisher("~actuator_limits", Twist2DStamped, queue_size=1)

        self.msg_actuator_limits = Twist2DStamped()
        self.msg_actuator_limits.v = self.v_max     # TODO: Calculate v_max !
        self.msg_actuator_limits.omega = self.omega_max     # TODO: Calculate omega_max !
        self.actuator_limits_received = False
        self.pub_actuator_limits.publish(self.msg_actuator_limits)

        rospy.loginfo("[%s] Initialized.", self.node_name)
        self.printValues()

    def readParamFromFile(self):
        # Check file existence
        fname = self.getFilePath(self.veh_name)
        # Use default.yaml if file doesn't exsit
        if not os.path.isfile(fname):
            rospy.logwarn("[%s] %s does not exist. Using default.yaml." %(self.node_name,fname))
            fname = self.getFilePath("default")

        with open(fname, 'r') as in_file:
            try:
                yaml_dict = yaml.load(in_file)
            except yaml.YAMLError as exc:
                rospy.logfatal("[%s] YAML syntax error. File: %s fname. Exc: %s" %(self.node_name, fname, exc))
                rospy.signal_shutdown()
                return

        # Set parameters using value in yaml file
        if yaml_dict is None:
            # Empty yaml file
            return
        for param_name in ["gain", "trim", "baseline", "k", "radius", "limit"]:
            param_value = yaml_dict.get(param_name)
            if param_name is not None:
                rospy.set_param("~"+param_name, param_value)
            else:
                # Skip if not defined, use default value instead.
                pass

    def getFilePath(self, name):
        return (get_duckiefleet_root()+'/calibrations/kinematics/' + name + ".yaml")

    def updateActuatorLimitsReceived(self, msg_actuator_limits_received):
        self.actuator_limits_received = msg_actuator_limits_received.data

    def saveCalibration(self):
        # Write to yaml
        data = {
            "calibration_time": time.strftime("%Y-%m-%d-%H-%M-%S"),
            "gain": self.gain,
            "trim": self.trim,
            "baseline": self.baseline,
            "radius": self.radius,
            "k": self.k,
            "limit": self.limit,
        }

        # Write to file
        file_name = self.getFilePath(self.veh_name)
        with open(file_name, 'w') as outfile:
            outfile.write(yaml.dump(data, default_flow_style=False))
        # Printout
        self.printValues()
        rospy.loginfo("[%s] Saved to %s" %(self.node_name, file_name))

    def cbSrvSaveCalibration(self, req):
        self.saveCalibration()
        return EmptyResponse()

    def cbSrvSetGain(self, req):
        self.gain = req.value
        self.printValues()
        self.msg_actuator_limits.v = self.v_max     # TODO: Calculate v_max !
        self.msg_actuator_limits.omega = self.omega_max     # TODO: Calculate omega_max !
        self.pub_actuator_limits.publish(self.msg_actuator_limits)
        return SetValueResponse()

    def cbSrvSetTrim(self, req):
        self.trim = req.value
        self.printValues()
        self.msg_actuator_limits.v = self.v_max     # TODO: Calculate v_max !
        self.msg_actuator_limits.omega = self.omega_max     # TODO: Calculate omega_max !
        self.pub_actuator_limits.publish(self.msg_actuator_limits)
        return SetValueResponse()

    def cbSrvSetBaseline(self, req):
        self.baseline = req.value
        self.printValues()
        self.msg_actuator_limits.v = self.v_max     # TODO: Calculate v_max !
        self.msg_actuator_limits.omega = self.omega_max     # TODO: Calculate omega_max !
        self.pub_actuator_limits.publish(self.msg_actuator_limits)
        return SetValueResponse()

    def cbSrvSetRadius(self, req):
        self.radius = req.value
        self.printValues()
        self.msg_actuator_limits.v = self.v_max     # TODO: Calculate v_max !
        self.msg_actuator_limits.omega = self.omega_max     # TODO: Calculate omega_max !
        self.pub_actuator_limits.publish(self.msg_actuator_limits)
        return SetValueResponse()

    def cbSrvSetK(self, req):
        self.k = req.value
        self.printValues()
        self.msg_actuator_limits.v = self.v_max     # TODO: Calculate v_max !
        self.msg_actuator_limits.omega = self.omega_max     # TODO: Calculate omega_max !
        self.pub_actuator_limits.publish(self.msg_actuator_limits)
        return SetValueResponse()

    def cbSrvSetLimit(self, req):
        self.limit = self.setLimit(req.value)
        self.printValues()
        self.msg_actuator_limits.v = self.v_max     # TODO: Calculate v_max !
        self.msg_actuator_limits.omega = self.omega_max     # TODO: Calculate omega_max !
        self.pub_actuator_limits.publish(self.msg_actuator_limits)
        return SetValueResponse()

    def setLimit(self, value):
        if value > self.limit_max:
            rospy.logwarn("[%s] limit (%s) larger than max at %s" % (self.node_name, value, self.limit_max))
            limit = self.limit_max
        elif value < self.limit_min:
            rospy.logwarn("[%s] limit (%s) smaller than allowable min at %s" % (self.node_name, value, self.limit_min))
            limit = self.limit_min
        else:
            limit = value
        return limit

    def printValues(self):
        rospy.loginfo("[%s] gain: %s trim: %s baseline: %s radius: %s k: %s limit: %s" % (self.node_name, self.gain, self.trim, self.baseline, self.radius, self.k, self.limit))

    def car_cmd_callback(self, msg_car_cmd):
        if not self.actuator_limits_received:
            self.pub_actuator_limits.publish(self.msg_actuator_limits)

        # Modificado para que el valor adecuado no sea el valor por defecto 
        # de gain = 1 y trim = 0 
        file_name = get_duckiefleet_root() + '/calibrations/' + 'duckiebot_random_seed' + ".yaml"

        # Open configuration
        with open(file_name, 'r') as archivo:
            config = yaml.safe_load(archivo)
        
        random.seed(config['seed'])

        opciones = [-15, -12, -10, -8, 8, 10, 12, 15]
        offset_introducido = random.choice(opciones)
        # offset_introducido = minimo + (value * (maximo - minimo))

        # assuming same motor constants k for both motors
        k_r = self.k + offset_introducido
        k_l = self.k - offset_introducido

        k_r_inv = (self.gain + self.trim) / k_r
        k_l_inv = (self.gain - self.trim) / k_l

        omega_r = (msg_car_cmd.v + 0.5 * msg_car_cmd.omega * self.baseline) / self.radius
        omega_l = (msg_car_cmd.v - 0.5 * msg_car_cmd.omega * self.baseline) / self.radius

        # conversion from motor rotation rate to duty cycle
        # u_r = (gain + trim) (v + 0.5 * omega * b) / (r * k_r)
        u_r = omega_r * k_r_inv
        # u_l = (gain - trim) (v - 0.5 * omega * b) / (r * k_l)
        u_l = omega_l * k_l_inv

        # limiting output to limit, which is 1.0 for the duckiebot
        u_r_limited = max(min(u_r, self.limit), -self.limit)
        u_l_limited = max(min(u_l, self.limit), -self.limit)

        # Put the wheel commands in a message and publish
        msg_wheels_cmd = WheelsCmdStamped()
        msg_wheels_cmd.header.stamp = msg_car_cmd.header.stamp
        msg_wheels_cmd.vel_right = u_r_limited
        msg_wheels_cmd.vel_left = u_l_limited
        self.pub_wheels_cmd.publish(msg_wheels_cmd)

    def setup_parameter(self, param_name, default_value):
        value = rospy.get_param(param_name, default_value)
        # Write to parameter server for transparency
        rospy.set_param(param_name, value)
        rospy.loginfo("[%s] %s = %s " % (self.node_name, param_name, value))
        return value

if __name__ == '__main__':
    rospy.init_node('inverse_kinematics_node', anonymous=False)
    inverse_kinematics_node = InverseKinematicsNode()
    rospy.spin()
