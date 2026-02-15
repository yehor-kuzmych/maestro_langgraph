#!/usr/bin/env python3
"""!
Camera service implementation using ROS2 to provide various image-related features, including thermal imaging, person detection, and identity recognition.
"""

import os
import rclpy
from rclpy.node import Node
from rooted_msgs.srv import MemoryRequest, Camera
from PIL import Image
from socket import *
import face_recognition as fr
from vision_module.ThermalCamera import ThermalCamera
from vision_module.OKAO.OKAO_vision_interface import get_emotions, get_image_array, detect_person
from vision_module.image_processing2 import get_dir_sunlight, get_dir_shadow
from rcl_interfaces.msg import ParameterDescriptor
import numpy as np

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
        id_descriptor = ParameterDescriptor(description='Location of the human identity database.')
        self.declare_parameter('identity_db', '', id_descriptor)  
        self.identity_db = self.get_parameter('identity_db').value

    def handle_camera(self, req, resp):
        """!
        Handles camera requests and processes based on the requested image type.

        @param req<Camera.Request>: The request object containing the image type.
        @param resp<Camera.Response>: The response object to populate.
        """
        img = None

        if req.imagetype == 0:  # Returns OKAO vision emotion estimate.
            self.get_logger().info("Returning emotional analysis.")
            img = get_emotions()

        elif req.imagetype == 1:  # Returns image of the OKAO camera.
            self.get_logger().info("Returning black and white image.")
            img = get_image_array().tolist()

        elif req.imagetype == 2:  # Returns thermal image.
            self.get_logger().info("Returning thermal image.")
            img = get_thermal_image()

        elif req.imagetype == 3:  # Returns person detection.
            self.get_logger().info("Verifying if there are persons.")
            img = detect_person()

        elif req.imagetype == 4:  # Returns sunlight position.
            self.get_logger().info("Returning sunlight position.")
            img = get_image_array()
            img = get_dir_sunlight(img, None)

        elif req.imagetype == 5:  # Returns shadow position.
            self.get_logger().info("Returning shadow position.")
            img = get_image_array()
            img = get_dir_shadow(img, None)

        elif req.imagetype == 6:  # Returns sunlight coordinates in the real world.
            self.get_logger().info("Returning light coordinates in the real world.")
            img = get_image_array()
            img = get_dir_sunlight(img, None)[0]
            Dy = 0.32 * 344 / (img[1] - 160)
            Dx = Dy * (img[0] - 120) / 266
            img = [Dx, Dy]

        elif req.imagetype == 7:  # Returns shadow coordinates in the real world.
            self.get_logger().info("Returning shadow coordinates in the real world.")
            img = get_image_array()
            img = get_dir_shadow(img, None)
            Dy = 0.32 * 344 / (img[1] - 160)
            Dx = Dy * (img[0] - 120) / 266
            img = [Dx, Dy]

        elif req.imagetype == 8:
            try:
                self.get_logger().info("Processing external image transmission.")
                image = get_image_array()
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
            unknown_face = np.array(get_image_array())
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


def get_thermal_image():
    """!
    Retrieves a thermal image from the ThermalCamera module.

    @return: Thermal image data.
    """
    tc = ThermalCamera()
    return tc.i2cRead()

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
