#!/usr/bin/env python3
"""!
Camera server implementation using ROS2 to provide various image-related services.
"""

import os
import cv2
import rclpy
from rclpy.node import Node
from rooted_msgs.srv import MemoryRequest, Camera
from PIL import Image
from sensor_msgs.msg import Image as Img
from socket import *
from std_msgs.msg import String, Bool, Int8
import numpy as np
import face_recognition as fr
from cv_bridge import CvBridge
from vision_module.image_processing2 import get_dir_sunlight, get_dir_shadow
from rcl_interfaces.msg import ParameterDescriptor

class MemoryAccess(Node):
    """!
    Handles interaction with the memory reader service.
    """

    def __init__(self):
        """!
        Initializes the MemoryAccess node and sets up the memory reader client.
        """
        super().__init__('maestro_memory_access')
        self.cli = self.create_client(MemoryRequest, 'memory_reader')
        while not self.cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('Memory service not available, waiting again...')
        self.req = MemoryRequest.Request()

    def send_request(self, DB, command):
        """!
        Sends a request to the memory reader service.

        @param DB<str>: The database name.
        @param command<str>: The command to execute on the database.
        """
        self.req.db_name = DB
        self.req.command = command
        self.future = self.cli.call_async(self.req)

class CameraServer(Node):
    """!
    Provides a camera service to handle various image-related requests.
    """

    def __init__(self):
        """!
        Initializes the CameraServer node and sets up the required parameters and subscriptions.
        """
        super().__init__("camera_server")
        self.srv = self.create_service(Camera, "camera", self.handle_camera)
        self.current_emotion = "neutral"

        id_descriptor = ParameterDescriptor(description='Location of the human identity database.')
        self.declare_parameter('identity_db', '', id_descriptor)  
        self.identity_db = self.get_parameter('identity_db').value

        self.emotion_setter = self.create_subscription(String, 'set_emotion',
                                                       self.emotion_cb_function,
                                                       10)
        self.person_detected = True
        self.detection_setter = self.create_subscription(Bool, 'set_person_detection',
                                                          self.person_cb_function,
                                                          10)
        self.camera_setter = self.create_subscription(Int8, 'set_camera_number',
                                                      self.camera_cb_function,
                                                      10)
        
        pc_cam_descriptor = ParameterDescriptor(description='Describes which camera is being used - pc or gazebo.')
        self.declare_parameter('use_pc_camera', '', pc_cam_descriptor)  
        self.use_pc_camera = self.get_parameter('use_pc_camera').value
        self.camera_number = None
        self.camera_topic = None
        self.camera_source = None
        if self.use_pc_camera:
            self.camera_source = "PC"  # "Gazebo"

            cam_num_descriptor = ParameterDescriptor(description='Number of the PC camera to be used.')
            self.declare_parameter('pc_camera_number', '', cam_num_descriptor)  
            self.camera_number = self.get_parameter('pc_camera_number').value
        else:
            self.camera_source = "Gazebo"
            cam_topic_descriptor = ParameterDescriptor(description='Gazebo camera topic.')
            self.declare_parameter('camera_topic', '', cam_topic_descriptor)  
            self.camera_topic = self.get_parameter('camera_topic').value

        self.memory_access = MemoryAccess()

    def emotion_cb_function(self, msg):
        """!
        Callback to update the current emotion.

        @param msg<String>: Message containing the current emotion.
        """
        self.current_emotion = msg.data

    def person_cb_function(self, msg):
        """!
        Callback to update the person detection status.

        @param msg<Bool>: Message containing the detection status.
        """
        self.person_detected = msg.data

    def camera_cb_function(self, msg):
        """!
        Callback to update the camera number.

        @param msg<Int8>: Message containing the camera number.
        """
        self.person_detected = msg.data

    def handle_camera(self, req, resp):
        """!
        Handles camera requests and processes based on the requested image type.

        @param req<Camera.Request>: The request object containing the image type.
        @param resp<Camera.Response>: The response object to populate.
        """
        img = None

        if req.imagetype == 0:  # Returns OKAO vision emotion estimate.
            self.get_logger().info("Returning emotional analysis.")
            img = self.current_emotion

        elif req.imagetype == 1:  # Returns image of the OKAO camera.
            self.get_logger().info("Returning black and white image.")
            img = get_image_array(source=self.camera_topic,
                                  camera_number=self.camera_number,
                                  camera_img_topic=self.camera_source)

        elif req.imagetype == 2:
            img = get_image_array(source=self.camera_topic,
                                  camera_number=self.camera_number,
                                  camera_img_topic=self.camera_source)
            img = cv2.resize(img, (32, 24))
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        elif req.imagetype == 3:  # Returns person detection status.
            self.get_logger().info("Verifying if there are persons.")
            img = self.person_detected

        elif req.imagetype == 4:  # Returns sunlight position.
            self.get_logger().info("Returning sunlight position.")
            img = get_image_array(source=self.camera_topic,
                                  camera_number=self.camera_number,
                                  camera_img_topic=self.camera_source)
            img = get_dir_sunlight(img, None)

        elif req.imagetype == 5:  # Returns shadow position.
            self.get_logger().info("Returning shadow position.")
            img = get_image_array(source=self.camera_topic,
                                  camera_number=self.camera_number,
                                  camera_img_topic=self.camera_source)
            img = get_dir_shadow(img, None)

        elif req.imagetype == 6:  # Returns sunlight coordinates in the real world.
            self.get_logger().info("Returning light coordinates in the real world.")
            img = get_image_array(source=self.camera_topic,
                                  camera_number=self.camera_number,
                                  camera_img_topic=self.camera_source)
            Dy = 0.32 * 344 / (img[1] - 160)
            Dx = Dy * (img[0] - 120) / 266
            img = [Dx, Dy]

        elif req.imagetype == 7:  # Returns shadow coordinates in the real world.
            self.get_logger().info("Returning shadow coordinates in the real world.")
            img = get_image_array(source=self.camera_topic,
                                  camera_number=self.camera_number,
                                  camera_img_topic=self.camera_source)
            img = get_dir_shadow(img, None)
            Dy = 0.32 * 344 / (img[1] - 160)
            Dx = Dy * (img[0] - 120) / 266
            img = [Dx, Dy]

        elif req.imagetype == 8:
            try:
                self.get_logger().info("Processing external image transmission.")
                image = get_image_array(source=self.camera_topic,
                                        camera_number=self.camera_number,
                                        camera_img_topic=self.camera_source)
                image = Image.fromarray(image, "L")
                image.save("img.png", "PNG")
                response = ""
                img_bytes = open("img.png", "rb")
                clientSocket = socket(AF_INET, SOCK_STREAM)
                clientSocket.connect(("165.93.125.232", 5051))
                while True:
                    data = img_bytes.read(1024)
                    clientSocket.send(data)
                    if not data:
                        break

                while True:
                    self.get_logger().info("Waiting for server response.")
                    try:
                        response = clientSocket.recv(1024)
                    except Exception as e:
                        if e[0] == "time out":
                            break 
                    if not response:
                        pass
                    else:
                        response = response.decode("utf8")
                        break
                clientSocket.close()
                os.system("rm img.png")
                img = response  
            except Exception as e:
                self.get_logger().error(f"Error during image processing: {e}")

        elif req.imagetype == 9:  # Identity recognition.
            id_match = False
            matched_id = None
            unknown_face = np.array(image=get_image_array(source=self.camera_topic,
                                                          camera_number=self.camera_number,
                                                          camera_img_topic=self.camera_source))
            unknown_face = Image.fromarray(unknown_face)  
            id_face_list = []
            self.memory_access.send_request(self.identity_db, "SELECT ID, filepath FROM id_table")
            while rclpy.ok():
                rclpy.spin_once(self.memory_access)
                if self.memory_access.future.done():
                    try:
                        response = self.memory_access.future.result().result
                    except Exception as e:
                        self.memory_access.get_logger().info(
                            f"Service call failed {e}")
                    else:
                        id_face_list = response
                    break

            for ID, face_file in id_face_list:
                id_face = fr.load_image_file(face_file)
                id_face_encoding = fr.face_encodings(id_face)[0]
                unknown_face_encoding = fr.face_encodings(unknown_face)[0]
                id_match = fr.compare_faces([id_face_encoding], unknown_face_encoding)
                if id_match:
                    img = ID
                    break

        else:
            self.get_logger().error("Unknown request.")
        resp.image = str(img)
        return resp

class GazeboCameraClient(Node):
    """!
    Handles Gazebo camera image subscription and retrieval.
    """

    def __init__(self, camera_img_topic):
        """!
        Initializes the GazeboCameraClient.

        @param camera_img_topic<str>: The topic for Gazebo camera images.
        """
        super().__init__('gazebo_camera_reader')
        self.camera_img_topic = camera_img_topic
        self.cli = self.create_client(Img, self.camera_img_topic)
        self.gazebo_camera_interface = self.create_subscription(Img, self.camera_img_topic,
                                                                 self.camera_cb_function,
                                                                 10)
        self.br = CvBridge()
        self.latest_image = np.zeros((240, 320)).tolist()

    def camera_cb_function(self, msg):
        """!
        Callback to update the latest image from the Gazebo camera.

        @param msg<Img>: The ROS image message.
        """
        self.latest_image = msg.data
        return self.br.cv2_to_imgmsg(msg.data).tolist()


def get_image_array(source="PC", camera_number=0, camera_img_topic=""):
    """!
    Retrieves the image array from the specified source.

    @param source<str>: The image source ("PC" or "Gazebo").
    @param camera_number<int>: The PC camera number.
    @param camera_img_topic<str>: The Gazebo camera topic.
    @return: Image array.
    """
    img = np.zeros((240, 320)).tolist()
    if source == "PC":
        camera = cv2.VideoCapture(camera_number)
        return_value, img = camera.read()
        img = cv2.resize(img, (240, 320))
        img = img.tolist()
    else:
        GazeboCamera = GazeboCameraClient(camera_img_topic)
        rate = GazeboCamera.node.create_timer(1)
        rate.sleep()
        img = GazeboCamera.latest_image
    return img

def main():
    """!
    Main function to initialize and run the CameraServer node.
    """
    rclpy.init(args=None)
    s = CameraServer()
    print("Ready to send images.")
    rclpy.spin(s)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
