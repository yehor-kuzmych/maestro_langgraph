#!/usr/bin/env python3
import tensorflow as tf
import cv2
import numpy as np
import os
import tflite_runtime.interpreter as tflite

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# file is too big for github, you need to give your own path to the model
# model_location = "/home/plantroid/vgg16_vis_nav_2.h5"
# modelH5_location = "/home/plantroid/dev_ws/src/plantroid/plantroid/stitched10_model_meeting_room.h5" #stitched_model_all_environments.h5
# model_location = "/home/plantroid/dev_ws/src/plantroid/plantroid/stitched_model16.tflite"
# model_location = "/home/plantroid/dev_ws/src/plantroid/plantroid/stitched_model10.tflite"

## Path to the Keras H5 model file
modelH5_location = "/home/plantroid/dev_ws/src/plantroid/plantroid/stitched_model_meeting_prunning.h5"
## Path to the TensorFlow Lite model file
model_location = "/home/plantroid/dev_ws/src/plantroid/plantroid/pruned.tflite"

## Load the Keras model from the specified file path
mynetH5 = tf.keras.models.load_model(modelH5_location, compile=False)

def NeuralNavigationH5(vision, theta, theta_line, distance):
    """!
    Perform neural navigation using a Keras H5 model.
    
    @param vision (<np.array>): Input vision data, normalized.
    @param theta (<float>): Current angle of the robot.
    @param theta_line (<float>): Line angle for reference.
    @param distance (<float>): Distance to the target.
    @return: <float> Output angle calculated by the model.
    """
    model = mynetH5
    return model([np.array([vision / 255]), 
                  np.array([[(theta_line + np.pi) / (2 * np.pi), (theta + np.pi) / (2 * np.pi), distance / 23.1]])])[0][0] * 2 * np.pi - np.pi

## Initialize the TensorFlow Lite interpreter with the specified model path
mynet = tflite.Interpreter(model_path=model_location, num_threads=1)

# gpu_options = tf.lite.experimental.GpuDelegateOptionsV2()
# gpu_delegate = tf.lite.experimental.GpuDelegateV2(options=gpu_options)
# mynet.modify_graph_with_delegate(gpu_delegate)

# Allocate tensors for the TensorFlow Lite interpreter
mynet.allocate_tensors()
## Input details of the TensorFlow Lite model
input_details = mynet.get_input_details()
## Output details of the TensorFlow Lite model
output_details = mynet.get_output_details()

def NeuralNavigation(vision, theta, theta_line, distance):
    """!
    Perform neural navigation using a TensorFlow Lite model.
    
    @param vision <np.array>: Input vision data, normalized.
    @param theta <float>: Current angle of the robot.
    @param theta_line <float>: Line angle for reference.
    @param distance <float>: Distance to the target.
    @return: <float> Output angle calculated by the model.
    """
    vision_input = np.array([vision / 255], dtype=np.float32)
    vector_input = np.array([[(theta_line + np.pi) / (2 * np.pi), (theta + np.pi) / (2 * np.pi), distance / 23.1]], dtype=np.float32)

    mynet.set_tensor(input_details[0]['index'], vision_input)
    mynet.set_tensor(input_details[1]['index'], vector_input)
    mynet.invoke()

    output_data = mynet.get_tensor(output_details[0]['index'])
    
    return output_data[0][0] * 2 * np.pi - np.pi

# while 1: print("I'm working")
