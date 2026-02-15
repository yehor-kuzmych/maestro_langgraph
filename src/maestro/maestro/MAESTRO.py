#!/usr/bin/env python3
import os
# import sys
# sys.path.append('') #  Add the location of this package on your computer
import maestro.utils as utils 
from maestro.ChatBot import chatter, sentiment_analysis, check_busy
# import utils
# from simple_state_machine import StateMachine
# from ChatBot import chatter
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from threading import Thread
from ast import literal_eval

from rooted_interfaces.rooted_interfaces.sensors_interface import SensorReader
from rooted_interfaces.rooted_interfaces.vision_interface import Cameras
from rooted_interfaces.rooted_interfaces.busy_interface import BusyInterface
from rooted_interfaces.rooted_interfaces.llm_interface import LLMinterface
from rooted_interfaces.rooted_interfaces.tts_interface import TTSinterface
from rooted_interfaces.rooted_interfaces.memory_interface import MemoryAccess
from rooted_interfaces.rooted_interfaces.navigation_interface import NavigationCommandSender

from time import time
from beepy import beep
from random import choice
from threading import Thread
import json
from StateMachines import problem_state_machine, busy_state_machine, dialogue_state_machine
from rcl_interfaces.msg import ParameterDescriptor


def emotion_2_prompt(emotion):
    i = emotion.index(max(emotion[:-1]))
    return [" in a happy tone", "", " in a calm tone", " in a calming tone", " to cheer up",""][i]


def process_notifications(notifications):
    gib = "I need your help, the soil has "
    for i, N in enumerate(notifications):
        gib += str(notifications[N][0]) + " " + N + ", " + str(notifications[N][1])+str(notifications[N][2])+  ", content "
        if i>0 and i<len(notifications)-1: gib+= " and "
    return gib


class PersonDetector(Node):
    def __init__(self, busy_state_machine, dialogue_state_machine):
        super().__init__('maestro_person_detector')
        self.vision_control = Cameras("maestro_person_detector_camera_reader")
        self.person_detect_alarm = self.create_publisher(String, 'seenTopic', 10)
        self.busy_state_machine = busy_state_machine
        self.dialogue_state_machine = dialogue_state_machine

    def get_vision(self):
        response = "" #get_image_array().astype(np.uint8)
        self.vision_control.send_request(3)
        while rclpy.ok():
            rclpy.spin_once(self.vision_control)
            if self.vision_control.future.done():
                try:
                    response = self.vision_control.future.result().image
                except Exception as e:
                    self.vision_control.get_logger().info(
                        'Service call failed %r' % (e,))
                else:
                    return response
                
    def detection_routine(self): #  TODO: this is probably going to lead the node to hog the camera for itself only... better modify this to make the detector pause for some time between detection requests.
        if (self.dialogue_state_machine.get_current_state() == "Silent" and 
            self.busy_state_machine.get_current_state() == "Free"):
            result = self.get_vision()
            if result == True or result == "True":
                self.person_detect_alarm.publish("Seen")
            else:
                pass


class MAESTRO(Node):
    def __init__(self, busy_state_machine, problem_state_machine, dialogue_state_machine):
        super().__init__('plantroid')

        # defining subscribers
        self.subscription = self.create_subscription(String,
                                                     'messageTopic',
                                                     self.cb_function_conversation,
                                                     10)
        self.subscription_notifications = self.create_subscription(String,
                                                                   'notificationTopic',
                                                                   self.cb_function_notification,
                                                                   10)
        self.subscription_human_seen = self.create_subscription(String,
                                                                'seenTopic',
                                                                self.cb_function_seen,
                                                                10)

        self.busy_state_listener = self.create_subscription(String,
                                                            'busy_state_publisher',
                                                             self.cb_function_busy_listener,
                                                             10)

        self.subscription
        self.subscription_notifications
        self.subscription_human_seen
        self.busy_state_listener
        
        # defining publishers 
        self.publisher = self.create_publisher(String, 'ListenBlockTopic', 10)
        self.publisher_emotion = self.create_publisher(String, 'emotionTopic', 10)

        # service interfaces
        self.vision_control = Cameras("maestro_camera_reader")
        self.busy_interface = BusyInterface("mestro_busy_interface")
        self.sensor_reader = SensorReader("maestro_sensor_reader")
        self.llm = LLMinterface("maestro_llm_interface")
        self.tts = TTSinterface("maestro_tts_interface")
        self.memory_access = MemoryAccess("maestro_memory_interface")
        self.robot_mover = NavigationCommandSender("maestro_navigation_commander")        

        # load parameters from launchfile.
        logging_descriptor = ParameterDescriptor(description='Variable that defines whether or not the robot should stoer conversation logs or not.')
        self.declare_parameter('store_chat_log', '', logging_descriptor) 
        self.logging = self.get_parameter('store_chat_log').value
        
        detect_descriptor = ParameterDescriptor(description='Variable that defines whether the robot should keep eye contact while talking or not.')
        self.declare_parameter('keep_eye_contact', '', detect_descriptor)        
        self.detect_person = self.get_parameter('keep_eye_contact').value        

        pc_mode_descriptor = ParameterDescriptor(description='Defines whether the node should run on embarked or PC mode.')
        self.declare_parameter('pc_mode', '', pc_mode_descriptor)        
        self.pc_mode = self.get_parameter('pc_mode').value

        store_emotion_descriptor = ParameterDescriptor(description='Variable that defines whether the robot should store emotion changes caused by its speech or not.')
        self.declare_parameter('store_emotion_change', '', store_emotion_descriptor)        
        self.store_emotion = self.get_parameter('store_emotion_change').value

        robot_name_descriptor = ParameterDescriptor(description='Name of the robot.')
        self.declare_parameter('robot_name', '', robot_name_descriptor)
        self.robot_name = self.get_parameter('robot_name').value
        
        # definition of important internal variables 
        self.busy = self.check_busy()
        self.notifications = {}
        self.time_last_seen = -float("inf")
        self.busy_state_machine = busy_state_machine
        self.problem_state_machine = problem_state_machine
        self.dialogue_state_machine = dialogue_state_machine
        self.current_emotion = "neutral"
        self.last_time_seen = float("inf")
        self.timeout_timer = None
        self.timeout_duration = 20.0

        # loading external information 
        self.dialogues = {}
        diag_file_loc_descriptor = ParameterDescriptor(description='Location of the file that contains the dialogue of your robot.')
        self.declare_parameter('dialogue_json', '', diag_file_loc_descriptor)
        dialogue_file_location = self.get_parameter('dialogue_json').value

        try:
            with open(dialogue_file_location, 'r') as f:
                self.dialogues = json.load(f)
        except Exception as e:
            self.get_logger.error(str(e))

    def cb_function_conversation(self, subscribedData):
        if self.timeout_timer is not None:
            self.timeout_timer.cancel()
        data = subscribedData.data.split(";")
        human_speech = data[0]
        speaker_voice_emotion = data[2]
        content_emotion = sentiment_analysis(data[0])        
        event = self.dialogue_initialization_routine(human_speech)

        face_emotion = self.get_face_emotion()        
        decided_emotion = self.emotion_fusion([speaker_voice_emotion, content_emotion, face_emotion])
        # response_emotion = decided_emotion #  Uncoment this line if you desire the robot to copy the emotion of the human, "mirror strategy". Comment line below.
        response_emotion = {"neutral":"neutral","happy":"happy","sad":"happy","anger":"neutral","surprise":"neutral"}[decided_emotion] # Uncoment this line if you want the robot to try to improve human emotional state. Comment line above
        self.current_emotion = response_emotion
        self.get_logger().info('Subscribed: ' + data[0])
        beep(1)
        response = str(self.assign_prosody(self.generate_response(data[0], response_emotion), response_emotion))
        self.set_face(response_emotion)

        if self.logging:
            emotion_delta = tuple()
            if self.store_emotion:
                final_face_emotion = self.get_face_emotion()
                emotion_delta = (decided_emotion, final_face_emotion)
            self.store_dialogue_exchange(data, response, time(), f"{emotion_delta}")
    
        self.tts.send_request(model="espeak_ng", prompt=response)
        while rclpy.ok():
            rclpy.spin_once(self.tts)
            if self.tts.future.done():
                try:
                    response = self.tts.future.result()
                except Exception as e:
                    self.tts.get_logger().info(
                        'Service call failed %r' % (e,))
                else:
                    break  
        self.dialogue_state_machine.transition("robot_finished") #  All states after robot finish talking transition to Goodbye through robot_finished.
        self.dialogue_finalization_routine(human_speech) # check if the goodbye speech is happening twice. if it is, remove farewell giving from this routine 

    def cb_function_notification(self, subscribedData):
        self.problem_state_machine.transition("problem_detected")
        data = subscribedData.data
        data_breakdown = data.split(":")
        self.notifications[data_breakdown[0]] = data_breakdown[1:]
        if "water" in self.notifications:
            self.set_face("thirsty")
        else:
            self.set_face("sad")
        print (self.notifications)
        self.get_logger().info('Subscribed: ' + data)

    def cb_function_seen(self, subscribedData):
            self.dialogue_state_machine.transition("saw_human")
            data = subscribedData.data
            if len(self.notifications)>0 and self.busy_state_machine.get_current_state()=="Free":
                self.last_time_seen = time()
                send_hello = String()
                send_hello.data = "Hello;None;happy"
                self.cb_function_conversation(send_hello) #TODO: adjust so it does not disturb the dialogue flow. 

    def cb_function_busy_listener(self, msg):
        busy = literal_eval(msg.data)
        if busy:
            self.busy_state_machine.transition("move")
        else:
            self.busy_state_machine.transition("finished")

    def cb_timeout(self):
        self.get_logger().info("Timeout reached! Saying goodbye...")
        self.dialogue_state_machine.transition("timeout")
        bye_speech = "see you later!"
        
        if self.dialogue_state_machine.get_current_state()=="ClearProblem":
            self.notifications = {}
            bye_speech = chatter(" ", self.dialogues.get("ClearProblem"))
            self.dialogue_state_machine.transition("robot_finished")
        else:
            bye_speech = bye_speech = chatter(" ", self.dialogues.get("Goodbye"))
        self.dialogue_state_machine.transition("dialogue_end")
        self.tts.send_request(model="espeak_ng", prompt=str([[150,150,150], bye_speech]))
        while rclpy.ok():
            rclpy.spin_once(self.tts)
            if self.tts.future.done():
                try:
                    response = self.tts.future.result()
                except Exception as e:
                    self.tts.get_logger().info(
                        'Service call failed %r' % (e,))
                else:
                    break
        self.dialogue_state_machine.reset()

    def avoidEcho(self):
        msg = String()
        msg.data = " "
        self.publisher.publish(msg)
        self.get_logger().info("Changing listen blocking state.")

    def busy_request(self, request):
        self.busy_interface.send_request(request)
        while rclpy.ok():
            rclpy.spin_once(self.busy_interface)
            if self.busy_interface.future.done():
                try:
                    response = self.busy_interface.future.result().result
                except Exception as e:
                    self.busy_interface.get_logger().info(
                        'Service call failed %r' % (e,))
                else:
                    return literal_eval(response)

    def check_busy(self):
        busy = self.busy_request("get")

    def set_busy(self): self.busy_request("set_busy")

    def set_idle(self): self.busy_request("set_idle")

    def get_vision(self):
        response = "" #get_image_array().astype(np.uint8)
        self.vision_control.send_request(8)
        while rclpy.ok():
            rclpy.spin_once(self.vision_control)
            if self.vision_control.future.done():
                try:
                    response = self.vision_control.future.result().image
                except Exception as e:
                    self.vision_control.get_logger().info(
                        'Service call failed %r' % (e,))
                else:
                    return response

    def set_face(self, emotion):
        msg = String()
        msg.data = emotion
        self.publisher_emotion.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)

    def get_face_emotion(self):
        response = False #get_image_array().astype(np.uint8)
        self.vision_control.send_request(0)
        while rclpy.ok():
            rclpy.spin_once(self.vision_control)
            if self.vision_control.future.done():
                try:
                    response = self.vision_control.future.result().image
                except Exception as e:
                    self.vision_control.get_logger().info(
                        'Service call failed %r' % (e,))
                else:
                    print(response)
                    response = literal_eval(response)
                break
        return response

    def get_sensor(self, num):
        response = 0
        self.sensor_reader.send_request(num)
        while rclpy.ok():
            rclpy.spin_once(self.sensor_reader)
            if self.sensor_reader.future.done():
                try:
                    response = self.sensor_reader.future.result().sensor_reading
                except Exception as e:
                    self.vision_control.get_logger().info(
                        'Service call failed %r' % (e,))
                else:
                    print(response)
                    response = literal_eval(response)
                break
        return response

    def emotion_fusion(self,emotion_list): return max(set([(i, emotion_list.count(i)) for i in set(emotion_list)]),key=lambda x:x[1])[0]

    def get_llm_response(self, msg):
        self.llm.send_request(model="llama3", prompt=msg)
        while rclpy.ok():
            rclpy.spin_once(self.llm)
            if self.llm.future.done():
                try:
                    msg = self.llm.future.result().response
                except Exception as e:
                    self.llm.get_logger().info('Service call failed %r' % (e,))
                else:
                    msg = str(msg)
                break
        return msg 
    
    def generate_response(self, data, response_emotion):
        basic_prompts = self.dialogues.get(self.dialogue_state_machine.get_current_state())        
        response = chatter(data, pairs=basic_prompts)
        #human_content_emotion = GPTJ(data, port=5052)
        #print(content_emotion)
        addendum = response_emotion
        if response:
            if "wikipedia:" in response:
                response = response.split(":")[1]
                response = utils.wikipedia_query(response)

            elif "dictionary:" in response:
                response = response.split(":")[1]
                response = utils.dictionary_query(response)

            elif "sensor:" in response:
                split = response.split(":")
                sensor_reading = self.get_sensor(int(split[1]))
                sensor_dict = {0:"right ear light", 1:"tail light",
                               2:"left ear light", 3:"soil moisture", 4:"temperature", 
                               5:"None", 6:"Salinity", 7:"pH", 8:"Nitrogen", 9:"Phosphorus", 10:"Potassium"}
                unit_dict = {0:"lux", 1:"lux",2:"lux", 3:" per cent", 4:" Degrees Celsius", 5:"", 
                             6:" deciSiemes per centimeter", 7:"", 8:" miligrams per kilogram of soil", 
                             9:" miligrams per kilogram of soil", 10:" miligrams per kilogram of soil"}                               
                response = "current "+sensor_dict[int(split[1])]+" sensor reading is "+str(sensor_reading)+unit_dict[int(split[1])]

            elif response == "vision_check":
                response = self.get_vision()

            elif response =="not_proc":
                response = process_notifications(self.notifications)
                print(response)
                self.notifications = {}

            response = f"Briefly and politely paraphrase the following text in a {addendum} tone: {response}"
            response = self.get_llm_response(response)

        else:
            response = self.get_llm_response(data)
        return response

    def assign_prosody(self, utterance, method="random"):
        if not isinstance(utterance, list):
            utterance = [utterance]
        prosody = []
        if method == "random":
            return [(i,[choice(range(10,200)),choice(range(80,450)),choice(range(0,99))]) for i in utterance]
        elif method == "angry":
            return ([(i,[180,200,55]) for i in utterance])
        elif method == "happy":
            return ([(i,[160,140,65]) for i in utterance])
        elif method == "neutral":
            return ([(i,[150,100,45]) for i in utterance])
        elif method == "surprise":
            return ([(i,[200,80,65]) for i in utterance])
        elif method == "sadness":
            return ([(i,[80,80,35]) for i in utterance])
        else:
            return ([(i,[150,100,45]) for i in utterance])

    def store_dialogue_exchange(self, humam_input, robot_output, time_stamp, emotion):
        command = f"INSERT INTO conversation (input, response, time, emotion) VALUES ({humam_input}, {robot_output}, {time_stamp}, {emotion})"
        self.memory_access.send_request("/home/plantroid/plantroid_ws/src/robot_memory/db/conversation_history.db", command)
        while rclpy.ok():
            rclpy.spin_once(self.memory_access)
            if self.memory_access.future.done():
                try:
                    response = self.memory_access.future.result().result
                except Exception as e:
                    self.memory_access.get_logger().info(
                        'Service call failed %r' % (e,))
                else:
                    pass
                break        
 
    def dialogue_initialization_routine(self, human_speech):
        
        transitions = ["alone", "dialogue_end", "saw_human", "heard_human", 
                        "yes","no", "no_problem", "busy", "idle", 
                        "problem_detected", "dialogue_init", "human_question",
                        "robot_finished"]
        event = "alone"
        while event in transitions: 
            current_state = self.dialogue_state_machine.get_current_state() 
            if current_state == "Silent" and event in ["busy", "no_problem"]: 
                break
            else:
                if event == "alone":
                    event = chatter(human_speech, self.dialogues.get(current_state))

                elif current_state == "CheckProblemAndBusy":
                    if len(self.notifications) > 0 and self.busy_state_machine.get_current_state()=="Free":
                        event = "problem_detected"
                    else:
                        event = "busy"

                elif current_state == "BusyCheck":
                    if self.busy_state_machine.get_current_state()=="Free":
                        event = "idle"
                        event = self.dialogue_state_machine.transition(event)
                        self.robot_mover.send_move_order("human")
                    else:
                        event = "busy"

                elif current_state == "ClearProblem":
                    event = "robot_finished"
                    self.notifications = {}

                else:
                    event = chatter(event, self.dialogues.get(current_state))

                self.dialogue_state_machine.transition(event)
        return event 
    
    def dialogue_finalization_routine(self, human_speech, event = None):
        current_state = self.dialogue_state_machine.get_current_state()
        if "Wait" in current_state:
            self.timeout_timer = self.create_timer(self.timeout_duration, self.cb_timeout)
        elif "Ask" in current_state and event == "no":
            self.timeout_timer = self.create_timer(self.timeout_duration, 0.02)
        

def maestro():
    ROS_interface = MAESTRO(busy_state_machine, problem_state_machine, dialogue_state_machine)
    rclpy.spin(ROS_interface)
    ROS_interface.destroy_node()


def person_detection(busy_state_machine, dialogue_state_machine):
    detector = PersonDetector(busy_state_machine, dialogue_state_machine)
    rclpy.spin(detector)
    detector.destroy_node()


def main():
    rclpy.init()
    maestro_thread = Thread(target = maestro,
                            args = ())
    person_detection_thread = Thread(target = person_detection,
                                     args=(busy_state_machine, 
                                           dialogue_state_machine))
    maestro_thread.start()
    person_detection_thread.start()
    rclpy.shutdown()


if __name__ == '__main__':
    main()