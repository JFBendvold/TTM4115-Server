import paho.mqtt.client as mqtt
import stmpy
import logging
from threading import Thread
import json
from secrets import token_hex
# TODO: choose proper MQTT broker address
MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883

# TODO: choose proper topics for communication
MQTT_TOPIC_INPUT = 'ttm4115/team_18/command'
MQTT_TOPIC_OUTPUT = 'ttm4115/team_18/answer'

existing_registrations = {}

import sqlite3
import bcrypt

class RegistrationLogic:
    def __init__(self, name, duration, component):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.duration = duration
        self.component = component
        self.username = None
        self.plain_password = None
        self.verification_code = None

        states = [
            {'name': 'idle'},
            {'name': 'enter'},
            {'name': 'verification'},
            {'name': 'verification_failed'},
            {'name': 'user_created'}
        ]

        
        t0 = {'source': 'initial', 'target': 'idle', 'effect': 'prompt_registration'}
        t1 = {'trigger': 'start_registration', 'source': 'idle', 'target': 'verification', 'effect': 'show_input_field'}
        t3 = {'trigger': 'not_verified', 'source': 'verification', 'target': 'verification', 'effect': 'verification_failed'}
        t4 = {'trigger': 'verified', 'source': 'verification', 'target': 'idle', 'effect': 'create_user'}
        t5 = {'trigger': 'cancel', 'source': 'verification', 'target': 'idle'}
        

        self.stm = stmpy.Machine(name=name, states=states, transitions=[t0,t1,t3,t4,t5], obj=self)

    def prompt_registration(self):
        self._logger.info(f"User {self.username} prompted to register.")

    def show_input_field(self):
        self._logger.info(f"User {self.username} is entering data.")

    def start_verification(self):
        self.send_verification_code()

    def send_verification_code(self):
        # You would store and send a real code here
        MQTT_BROKER = 'mqtt20.iik.ntnu.no'
        MQTT_PORT = 1883
        MQTT_TOPIC_INPUT = 'ttm4115/team_18/command'
        MQTT_TOPIC_OUTPUT = 'ttm4115/team_18/answer'

        mqtt_client = mqtt.Client()
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        mqtt_client.loop_start()
        token = token_hex(16)
        payload = {"verification_code": token}
        payload = json.dumps(payload)
        mqtt_client.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=2)
        self._logger.info(f"Verification code sent to user {self.username} (simulated).")
        self.verification_code = token

    def verification_failed(self):
        MQTT_BROKER = 'mqtt20.iik.ntnu.no'
        MQTT_PORT = 1883
        MQTT_TOPIC_INPUT = 'ttm4115/team_18/command'
        MQTT_TOPIC_OUTPUT = 'ttm4115/team_18/answer'

        mqtt_client = mqtt.Client()
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        mqtt_client.loop_start()
        payload = {"verification_failed": "Wrong verification code"}
        payload = json.dumps(payload)
        mqtt_client.publish(MQTT_TOPIC_OUTPUT, payload=payload, qos=2)
        self.send_verification_code()



    def get_verification_code(self):
        return self.verification_code
    
    def create_user(self):
        hashed_pw = bcrypt.hashpw(self.plain_password.encode('utf-8'), bcrypt.gensalt())
        try:
            con = sqlite3.connect("database.db")
            cur = con.cursor()
            cur.execute("INSERT INTO brukere VALUES (?, ?, ?, ?)", (None, self.username, hashed_pw, 0))
            con.commit()
            cur.execute("SELECT * FROM brukere")
            a = cur.fetchall()
            print(a)
            con.close()
            self._logger.info(f"User {self.username} created in database.")
        except Exception as e:
            self._logger.error(f"Failed to insert user: {e}")



class RegistrationComponent:
    """
    The component to manage named timers in a voice assistant.

    This component connects to an MQTT broker and listens to commands.
    To interact with the component, do the following:

    * Connect to the same broker as the component. You find the broker address
    in the value of the variable `MQTT_BROKER`.
    * Subscribe to the topic in variable `MQTT_TOPIC_OUTPUT`. On this topic, the
    component sends its answers.
    * Send the messages listed below to the topic in variable `MQTT_TOPIC_INPUT`.

        {"command": "new_timer", "name": "spaghetti", "duration":50}

        {"command": "status_all_timers"}

        {"command": "status_single_timer", "name": "spaghetti"}

    """
    def finish_timer(self):
        """
        Function to be called when a timer expires.

        This function is called by the state machine when the timer expires.
        """

    def on_connect(self, client, userdata, flags, rc):
        # we just log that we are connected
        self._logger.debug('MQTT connected to {}'.format(client))
    def on_message(self, client, userdata, msg):
        self._logger.debug('Incoming message to topic {}'.format(msg.topic))
        payload = json.loads(msg.payload.decode('utf-8'))
        command = payload['command']
        name = payload['name']
        
        if command == 'register':

            self._logger.debug(f'Starting registration for user: {name}')
            duration = 60
            registration = RegistrationLogic(name, duration, self)
            registration.username = name
            registration.plain_password = payload.get('password')

            if registration.name not in existing_registrations.keys():
                registration.send_verification_code()
                existing_registrations[registration.name] = registration.get_verification_code()
                self.stm_driver.add_machine(registration.stm)
                self.stm_driver.send('start_registration', name)
                print(existing_registrations)
            else:
                self._logger.warning(f'User {name} is already in registration process.')
            
        elif command == 'verify':
            code = payload.get('code')
            name = payload.get('name')
            correct_code = existing_registrations[name]
            # Simulate correct code (in real implementation you'd store and check it)
            if code == correct_code:
                self.stm_driver.send('verified', name)
                del existing_registrations[name]
            else:
                self._logger.debug("hei")
                self.stm_driver.send('not_verified', name)

        elif command == 'cancel':
            if name in existing_registrations:
                self.stm_driver.send('cancel', name)
                del existing_registrations[name]
            else:
                self._logger.warning(f'No ongoing registration for {name}.')

        else:
            self._logger.error(f'Unknown command: {command}')



    def __init__(self):
        """
        Start the component.

        ## Start of MQTT
        We subscribe to the topic(s) the component listens to.
        The client is available as variable `self.client` so that subscriptions
        may also be changed over time if necessary.

        The MQTT client reconnects in case of failures.

        ## State Machine driver
        We create a single state machine driver for STMPY. This should fit
        for most components. The driver is available from the variable
        `self.driver`. You can use it to send signals into specific state
        machines, for instance.

        """
        # get the logger object for the component
        self._logger = logging.getLogger(__name__)
        print('logging under name {}.'.format(__name__))
        self._logger.info('Starting Component')

        # create a new MQTT client
        self._logger.debug('Connecting to MQTT broker {} at port {}'.format(MQTT_BROKER, MQTT_PORT))
        self.mqtt_client = mqtt.Client()
        # callback methods
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        # Connect to the broker
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        # subscribe to proper topic(s) of your choice
        self.mqtt_client.subscribe(MQTT_TOPIC_INPUT)
        # start the internal loop to process MQTT messages
        self.mqtt_client.loop_start()

        # we start the stmpy driver, without any state machines for now
        self.stm_driver = stmpy.Driver()
        self.stm_driver.start(keep_active=True)
        self._logger.debug('Component initialization finished')

    def stop(self):
        """
        Stop the component.
        """
        # stop the MQTT client
        self.mqtt_client.loop_stop()

        # stop the state machine Driver
        self.stm_driver.stop()


# logging.DEBUG: Most fine-grained logging, printing everything
# logging.INFO:  Only the most important informational log items
# logging.WARN:  Show only warnings and errors.
# logging.ERROR: Show only error messages.
debug_level = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(debug_level)
ch = logging.StreamHandler()
ch.setLevel(debug_level)
formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

t = RegistrationComponent()