#!/usr/bin/env python3
import os
os.environ["KIVY_NO_ARGS"] = "1"
from kivy.config import Config
Config.set('kivy', 'window', 'x11')
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
import rclpy
from rclpy.node import Node
from threading import Thread
from rooted_msgs.srv import Gesture
from std_msgs.msg import String
from time import time
from rcl_interfaces.msg import ParameterDescriptor
from rooted_interfaces.rooted_interfaces.gestures_interface import GestureRequests

s = "s0"
c = 0
is_talking = True
emotion_engine = None


class FaceController(Node):
    def __init__(self,initial_emotion="joy"):
        super().__init__('facial_expression_node')
        my_parameter_descriptor = ParameterDescriptor(description='Location of the folder containing the images that comnpose the face of your robot.')
        self.declare_parameter('image_folder', '', my_parameter_descriptor)
        self.gesture_com = GestureRequests("facial_expression_gesture_requester")
        self.image_folder = self.get_parameter('image_folder').value
        self.l_eye = "eye0_r.png"
        self.r_eye = "eye0.png"
        self.mouth = "empty.png"
        self.emotion = "empty.png"
        self.current_emotion = initial_emotion 
        self.emotion_table = {"fear":[["eye5_r.png", "eye5.png", "empty.png","empty.png"],["eye5_r.png", "eye5.png", "mouth1.png","empty.png"],["eye9_r.png", "eye9.png", "empty.png","empty.png"]], 
                              "anger":[["eye1_r.png", "eye1.png", "mouth2.png","emo0.png"],["eye1_r.png", "eye1.png", "mouth1.png","emo0.png"], ["eye9_r.png", "eye9.png", "mouth2.png","emo0.png"]],
                              "neutral":[["eye0_r.png", "eye0.png", "empty.png","empty.png"],["eye0_r.png", "eye0.png", "mouth0.png","empty.png"],["eye9_r.png", "eye9.png", "empty.png","empty.png"]],
                              "joy":[["eye7_r.png", "eye7.png", "empty.png","empty.png"],["eye7_r.png", "eye7.png", "mouth0.png","empty.png"],["eye9_r.png", "eye9.png", "empty.png","empty.png"]],
                              "love":[["eye7_r.png", "eye7.png", "empty.png","empty.png"],["eye7_r.png", "eye7.png", "mouth0.png","empty.png"],["eye9_r.png", "eye9.png", "empty.png","empty.png"]],
                              "neutral":[["eye0_r.png", "eye0.png", "empty.png","empty.png"],["eye0_r.png", "eye0.png", "mouth0.png","empty.png"],["eye9_r.png", "eye9.png", "empty.png","empty.png"]],
                              "sadness":[["eye2_r.png", "eye2.png", "empty.png","empty.png"],["eye2_r.png", "eye2.png", "mouth1.png","empty.png"], ["eye9_r.png", "eye9.png", "mouth1.png","empty.png"]],
                              "disgust":[["eye6_r.png", "eye6.png", "mouth1.png","empty.png"],["eye6_r.png", "eye6.png", "empty.png","empty.png"], ["eye9_r.png", "eye9.png", "mouth1.png","empty.png"]],
                              "surprise":[["eye10_r.png", "eye10.png", "mouth1.png","emo2.png"],["eye10_r.png", "eye10.png", "empty.png","emo2.png"], ["eye9_r.png", "eye9.png", "mouth1.png","emo2.png"]],
                              "dizzy":[["eye8_r.png", "eye8.png", "empty.png","empty.png"],["eye8_r.png", "eye8.png", "mouth0.png","empty.png"],["eye8_r.png", "eye8.png", "empty.png","empty.png"]],
                              "sleepy":[["eye9_r.png", "eye9.png", "empty.png","emo3.png"],["eye9_r.png", "eye9.png", "empty.png","emo3.png"], ["eye9_r.png", "eye9.png", "empty.png","emo3.png"]],
                              "thirsty":[["eye11_r.png", "eye11.png", "mouth1.png","emo1.png"],["eye11_r.png", "eye11.png", "empty.png","emo1.png"], ["eye9_r.png", "eye9.png", "mouth1.png","emo1.png"]],
                              "sweaty":[["eye3_r.png", "eye3.png", "mouth1.png","emo1.png"],["eye3_r.png", "eye3.png", "empty.png","emo1.png"], ["eye9_r.png", "eye9.png", "mouth1.png","emo1.png"]],
                              "confused":[["eye2_r.png", "eye3.png", "empty.png","emo4.png"],["eye2_r.png", "eye3.png", "mouth0.png","emo4.png"], ["eye9_r.png", "eye9.png", "empty.png","emo4.png"]],                         
        }

        self.subscription = self.create_subscription(String, 'IsTalkingTopic',
                                                     self.cb_function_message,
                                                     10)
        self.subscription
        self.emotion = self.create_subscription(String, 'emotionTopic',
                                                     self.cb_function_emotion,
                                                     10)

    def cb_function_message(self, Data):
        global is_talking
        reply = Data.data
        # reply = literal_eval(reply)
        print(reply)
        if reply == "talking":
            is_talking = True
        else:
            is_talking = False

    def cb_function_emotion(self, Data):
        if Data.data in ["fear", "anger", "joy","sadness", "disgust", 
                         "surprise", "dizzy", "sleepy", "thirsty",
                         "sweaty", "confused","neutral"]:
            self.current_emotion = Data.data
            if Data.data == "surprise":
                try:
                    self.gesture_comm.send_request("surprise")
                    t0 = time()
                    while time()-t0<3:pass
                except Exception as e:
                    print(f"Failed to move neck due to {e}!")

                self.current_emotion = "neutral"
        else: pass


class MyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        global emotion_engine
        self.frame = 0
        Clock.schedule_interval(self.mouther, 0.2)

    def build(self):
        global emotion_engine
        Window.clearcolor = (1, 1, 1, 1)
        while emotion_engine is None:
            print("Waiting for ROS2 node to start.")
        layout = FloatLayout()
        self.im_base = Image(source=emotion_engine.image_folder+'Base.png', pos_hint={'center_x': .5, 'center_y': .5}, size_hint=(1.5, 1.5))
        self.im_l_eye = Image(source=emotion_engine.image_folder+'eye0_r.png', pos_hint={'center_x': .65, 'center_y': .65}, size_hint=(1.5, 1.5))
        self.im_r_eye = Image(source=emotion_engine.image_folder+'eye9.png', pos_hint={'center_x': .35, 'center_y': .65}, size_hint=(1.5, 1.5))
        self.im_mouth = Image(source=emotion_engine.image_folder+'mouth3.png', pos_hint={'center_x': .5, 'center_y': .205}, size_hint=(1.5, 1.5))
        self.im_emotion = Image(source=emotion_engine.image_folder+'empty.png', pos_hint={'center_x': .85, 'center_y': .75}, size_hint=(1.5, 1.5))
    
        layout.add_widget(self.im_base)
        layout.add_widget(self.im_l_eye)
        layout.add_widget(self.im_r_eye)
        layout.add_widget(self.im_mouth)
        layout.add_widget(self.im_emotion)

        self.compose_face(emotion_engine.emotion_table[emotion_engine.current_emotion][0])
        
        return layout

    def mouther(self, dt):
        global is_talking
        global emotion_engine
        if is_talking:
            self.frame = 1 if self.frame == 0 else 0
        else:
            self.frame = 0
        
        try:
            self.compose_face(emotion_engine.emotion_table[emotion_engine.current_emotion][self.frame])
        except KeyError:
            pass

    def compose_face(self, lista):
        global emotion_engine
        self.im_l_eye.source = emotion_engine.image_folder + lista[0]
        self.im_r_eye.source = emotion_engine.image_folder + lista[1]
        self.im_mouth.source = emotion_engine.image_folder + lista[2]
        self.im_emotion.source = emotion_engine.image_folder + lista[3]


def ROS_main():
    rclpy.init()
    global emotion_engine
    emotion_engine = FaceController()
    rclpy.spin(emotion_engine)


def GUI_main():
    plantroid_GUI = MyApp()
    plantroid_GUI.run()


def main():
    thread1 = Thread(target=ROS_main,args=())
    thread1.start()
    GUI_main()

if __name__ == '__main__':
    main()