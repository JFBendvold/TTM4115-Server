import paho.mqtt.client as mqtt
import logging
from threading import Thread
import json
from appJar import gui

MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883
MQTT_TOPIC_INPUT = 'ttm4115/team_18/command'
MQTT_TOPIC_OUTPUT = 'ttm4115/team_18/answer'


class RegistrationCommandSenderComponent:
    """
    GUI and MQTT client to send registration commands.
    """

    def on_connect(self, client, userdata, flags, rc):
        self._logger.debug('MQTT connected to {}'.format(client))

    def on_message(self, client, userdata, msg):
        # Optionally handle server messages (e.g. success/failure feedback)
        pass

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        print('logging under name {}.'.format(__name__))
        self._logger.info('Starting Registration Command Sender')

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        self.mqtt_client.loop_start()

        self.create_gui()

    def create_gui(self):
        self.app = gui("Registration Interface")

        def publish_command(command):
            payload = json.dumps(command)
            self._logger.info(f"Publishing: {command}")
            self.mqtt_client.publish(MQTT_TOPIC_INPUT, payload=payload, qos=2)

        # --- Registration Fields ---
        self.app.startLabelFrame("Register New User")
        self.app.addLabelEntry("Username")
        self.app.addSecretEntry("Password")
        def register_user(btn):
            username = self.app.getEntry("Username")
            password = self.app.getEntry("Password")
            command = {"command": "register", "name": username, "password": password}
            publish_command(command)
        self.app.addButton("Register", register_user)
        self.app.stopLabelFrame()

        # --- Verification ---
        self.app.startLabelFrame("Verify Code")
        self.app.addLabelEntry("Verification Code")
        def verify_user(btn):
            username = self.app.getEntry("Username")
            code = self.app.getEntry("Verification Code")
            command = {"command": "verify", "name": username, "code": code}
            publish_command(command)
        self.app.addButton("Verify", verify_user)
        self.app.stopLabelFrame()

        # --- Cancel Registration ---
        self.app.startLabelFrame("Cancel Registration")
        def cancel_user(btn):
            username = self.app.getEntry("Username")
            command = {"command": "cancel", "name": username}
            publish_command(command)
        self.app.addButton("Cancel Registration", cancel_user)
        self.app.stopLabelFrame()

        self.app.go()

    def stop(self):
        self.mqtt_client.loop_stop()


# Logging Setup
debug_level = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(debug_level)
ch = logging.StreamHandler()
ch.setLevel(debug_level)
formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Run the component
t = RegistrationCommandSenderComponent()
