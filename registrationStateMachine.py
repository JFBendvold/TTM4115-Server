import paho.mqtt.client as mqtt
import stmpy
import logging
from threading import Thread
import json

# TODO: choose proper MQTT broker address
MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883

# TODO: choose proper topics for communication
MQTT_TOPIC_INPUT = 'ttm4115/team_18/command'
MQTT_TOPIC_OUTPUT = 'ttm4115/team_18/answer'

existing_timers = []

class RegistrationLogic:
    """
    State Machine for a named timer.

    This is the support object for a state machine that models a single timer.
    """
    def __init__(self, name, duration, component):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.duration = duration
        self.component = component

        # TODO: build the transitions
        # t0 initial transition off

        states = [{'name' : 'idle'}, {'name' : 'enter'}, {'name' : 'verification'}, {'name' : 'verification_failed'}, {'name' : 'user_created'}]

        t0 = {
            'source' : 'initial',
            'target' : 'idle',
            'effect' : 'prompt_registration'
        }

        t1 = {
            'trigger' : 'start_registration',
            'source' : 'initial',
            'target' : 'enter',
            'effect' : 'show_input_field' 
        }

        t2 = {
            'trigger' : 'submit',
            'source' : 'enter',
            'target' : 'verification',
            'effect' : 'start_timer("t"); send_verification_code'
        }

        t3 = {
            'trigger' : 'not_verified',
            'source' : 'verification',
            'target' : 'verification failed',   
            'effect' : 'report_status'
        }

        t4 = {
            'trigger' : 'verified',
            'source' : 'verification',
            'target' : 'user created',   
            'effect' : 'report_status'
        }

        t5 = {
            'trigger' : 'cancel',
            'source' : 'enter',
            'target' : 'on',   
            'effect' : 'report_status'
        }

        self.stm = stmpy.Machine(name=name, transitions=[t0, t1, t2, t3], obj=self)
    
    # TODO define functions as transition effetcs
    
    def start_self(self):
        self.stm.start_timer('t', self.duration)
        print(f"Started timer {self.name} with duration {self.duration}")

    def remove_self(self):
        existing_timers.remove(self.name)
        print("removed: ", existing_timers)
        message = f'Timer {self.name} complete'
        self.component.mqtt_client.publish(MQTT_TOPIC_OUTPUT, message)
        self.stm.terminate()
       
    def cancel_timer(self):
        existing_timers.remove(self.name)
        print("Timer cancelled", self.name)
        message = f'Timer {self.name} cancelled'
        self.component.mqtt_client.publish(MQTT_TOPIC_OUTPUT, message)
        self.stm.terminate()
    
    def report_status(self):
        print(f"reporting status for timer {self.name}")
        time = int(self.stm.get_timer('t'))
        message = f'Timer {self.name} has {time} left!'
        self.component.mqtt_client.publish(MQTT_TOPIC_OUTPUT, message)

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
        """
        Processes incoming MQTT messages.

        We assume the payload of all received MQTT messages is an UTF-8 encoded
        string, which is formatted as a JSON object. The JSON object contains
        a field called `command` which identifies what the message should achieve.

        As a reaction to a received message, we can for example do the following:

        * create a new state machine instance to handle the incoming messages,
        * route the message to an existing state machine session,
        * handle the message right here,
        * throw the message away.

        """
        self._logger.debug('Incoming message to topic {}'.format(msg.topic))

        # TODO unwrap JSON-encoded payload
        payload = json.loads(msg.payload.decode('utf-8'))
        
        # TODO extract command
        command = payload['command']

        # TODO determine what to do
        if command == 'new_timer':
            self._logger.debug('Creating new timer')
            name = payload['name']
            duration = payload['duration']
            # Try function to attempt to create timer, if success append to list of active timers
            try:
                timer = RegistrationLogic(name, duration, self)
                self.stm_driver.add_machine(timer.stm)
                if (existing_timers.__contains__(timer.name)) == False:
                    existing_timers.append(timer.name)
                    print("added: ",existing_timers)
            except Exception as e:
                # If timer already exists (already_exist.contain(name)), return error message
                self._logger.error('Timer already exists', e)
                
        elif command == 'cancel_timer':
            self._logger.debug('Cancelling timer')
            name = payload['name']
            try:
                for t in existing_timers:
                    if t == name:
                        self.stm_driver.send('cancel', t)
            except Exception as e:
                self._logger.error('Timer does not exist', e)
                    
            # Try function to attempt to cancel timer, if success remove from list of active timers
            # If timer does not exist (not_exist.contain(name)), return error message
        elif command == 'status_all_timers':
            self._logger.debug('Status of all timers')
            try:
                for timer in existing_timers:
                    self.stm_driver.send('status', timer)
                    self._logger.debug('Timer: ' + timer + ' ACTIVE ')
            except:
                self._logger.error('No active timers')
    
        elif command == 'status_single_timer':
            self._logger.debug('Status of single timer')
            name = payload['name']
            try:
                print("Existing timer: " + existing_timers[0])
                if existing_timers.__contains__(name):
                    self.stm_driver.send('status', name)
                    self._logger.debug('Timer: ' + name + ' ACTIVE ')
                else:
                    self._logger.error('Timer: ' + name + ' INACTIVE ')
            except:
                self._logger.error('Timer: ' + name + ' INACTIVE ')
        else:
            self._logger.error('Unknown command')


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