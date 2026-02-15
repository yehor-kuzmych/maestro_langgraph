#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rcl_interfaces.msg import ParameterDescriptor
from ast import literal_eval

from rooted_interfaces.tts_interface import TTSinterface
from rooted_interfaces.busy_interface import BusyInterface

from .graph import process_message, set_chains, set_tracker
from .chains import DialogueChains
from .sensor_tracker import SensorTracker


class MaestroLangGraphNode(Node):

    def __init__(self):
        super().__init__('maestro_langgraph')

        model_descriptor = ParameterDescriptor(
            description='Model name for dialogue generation (used by Ollama; LM Studio uses loaded model)'
        )
        self.declare_parameter('model_name', 'qwen2:0.5b', model_descriptor)
        self.model_name = self.get_parameter('model_name').value

        backend_descriptor = ParameterDescriptor(
            description='LLM backend: "ollama" or "lmstudio"'
        )
        self.declare_parameter('backend', 'ollama', backend_descriptor)
        self.backend = self.get_parameter('backend').value

        base_url_descriptor = ParameterDescriptor(
            description='LLM server URL (auto-detected if empty)'
        )
        self.declare_parameter('base_url', '', base_url_descriptor)
        base_url = self.get_parameter('base_url').value or None

        chains = DialogueChains(
            model_name=self.model_name,
            base_url=base_url,
            backend=self.backend,
        )
        set_chains(chains)
        self.get_logger().info(f'Initialized LangGraph dialogue with backend: {self.backend}, model: {self.model_name}')

        self.subscription = self.create_subscription(
            String,
            'messageTopic',
            self.cb_function_conversation,
            10
        )

        self.subscription_notifications = self.create_subscription(
            String,
            'notificationTopic',
            self.cb_function_notification,
            10
        )

        self.subscription_human_seen = self.create_subscription(
            String,
            'seenTopic',
            self.cb_function_seen,
            10
        )

        self.busy_state_listener = self.create_subscription(
            String,
            'busy_state_publisher',
            self.cb_function_busy_listener,
            10
        )

        self.publisher_listen_block = self.create_publisher(String, 'ListenBlockTopic', 10)
        self.publisher_emotion = self.create_publisher(String, 'emotionTopic', 10)

        self.tts = TTSinterface("maestro_langgraph_tts")

        self.busy_interface = BusyInterface("maestro_langgraph_busy")

        self.notifications = {}
        self.robot_busy = False
        self.conversation_history = []

        self.sensor_tracker = SensorTracker()
        set_tracker(self.sensor_tracker)

        self._check_busy()

        self.get_logger().info('MaestroLangGraph node initialized')

    def cb_function_conversation(self, msg: String):
        parts = msg.data.split(";")
        human_speech = parts[0]
        voice_emotion = parts[2] if len(parts) > 2 else "neutral"

        self.get_logger().info(f'Received: "{human_speech}" (emotion: {voice_emotion})')

        self._publish_listen_block()

        result = process_message(
            message=human_speech,
            voice_emotion=voice_emotion,
            history=self.conversation_history,
            robot_busy=self.robot_busy,
            notifications=self.notifications,
            sensor_tracker_state=self.sensor_tracker.to_state(),
        )

        if result.get("sensor_tracker_state"):
            self.sensor_tracker.load_state(result["sensor_tracker_state"])

        self.conversation_history = result.get("conversation_history", [])

        response = result.get("response", "")
        emotion = result.get("response_emotion", "neutral")
        prosody = result.get("prosody", (150, 100, 45))
        robot_status = result.get("robot_status", "free")
        user_response = result.get("user_response_type")

        self.get_logger().info(f'Response: "{response}" (emotion: {emotion}, status: {robot_status})')

        if user_response == "committed":
            pending = result.get("pending_issue")
            if pending:
                sensor_type = pending.get("sensor_type")
                self._clear_notification_for_sensor(sensor_type)

        self._publish_emotion(emotion)

        self._send_tts(response, prosody)

    def cb_function_notification(self, msg: String):
        parts = msg.data.split(":")
        if len(parts) >= 3:
            sensor_name = parts[0]
            self.notifications[sensor_name] = parts[1:]
            self.get_logger().info(f'Notification: {sensor_name} = {parts[1:]}')

    def cb_function_seen(self, msg: String):
        self.get_logger().info('Person detected')

    def cb_function_busy_listener(self, msg: String):
        try:
            busy = literal_eval(msg.data)
            self.robot_busy = bool(busy)
        except (ValueError, SyntaxError):
            self.robot_busy = msg.data.lower() == "true"
        self.get_logger().info(f'Robot busy state changed: {self.robot_busy}')

    def _busy_request(self, request: str):
        self.busy_interface.send_request(request)
        while rclpy.ok():
            rclpy.spin_once(self.busy_interface)
            if self.busy_interface.future.done():
                try:
                    response = self.busy_interface.future.result().result
                    return literal_eval(response)
                except Exception as e:
                    self.get_logger().warning(f'Busy service call failed: {e}')
                    return None

    def _check_busy(self):
        result = self._busy_request("get")
        if result is not None:
            self.robot_busy = bool(result)
            self.get_logger().debug(f'Checked busy state: {self.robot_busy}')

    def _set_busy(self):
        self._busy_request("set_busy")
        self.robot_busy = True
        self.get_logger().info('Robot set to busy')

    def _set_idle(self):
        self._busy_request("set_idle")
        self.robot_busy = False
        self.get_logger().info('Robot set to idle')

    def clear_notifications(self):
        self.notifications = {}
        self.get_logger().info('Notifications cleared')

    def _clear_notification_for_sensor(self, sensor_type: str):
        if not sensor_type:
            return

        mapping = {
            "moisture": ["moisture", "soil_moisture"],
            "temperature": ["temperature", "temp"],
            "light": ["light", "lux"],
            "pH": ["ph", "acidity"],
        }

        keys_to_remove = mapping.get(sensor_type, [])
        for key in list(self.notifications.keys()):
            if key.lower() in keys_to_remove:
                del self.notifications[key]

        self.get_logger().info(f'Cleared notifications for {sensor_type}')

    def _publish_listen_block(self):
        msg = String()
        msg.data = " "
        self.publisher_listen_block.publish(msg)

    def _publish_emotion(self, emotion: str):
        msg = String()
        msg.data = emotion
        self.publisher_emotion.publish(msg)
        self.get_logger().debug(f'Published emotion: {emotion}')

    def _send_tts(self, text: str, prosody: tuple):
        tts_input = str([(text, list(prosody))])

        self.tts.send_request(model="espeak_ng", prompt=tts_input)

        while rclpy.ok():
            rclpy.spin_once(self.tts)
            if self.tts.future.done():
                try:
                    self.tts.future.result()
                except Exception as e:
                    self.get_logger().error(f'TTS failed: {e}')
                break


def main(args=None):
    rclpy.init(args=args)

    node = MaestroLangGraphNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
