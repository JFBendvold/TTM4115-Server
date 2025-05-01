import paho.mqtt.client as mqtt
import json
import logging
import sqlite3
import random

# MQTT Setup
MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883
MQTT_TOPIC_STATUS = 'ttm4115/team_18/status'
MQTT_TOPIC_COMMAND = 'ttm4115/team_18/command'

# Task location base
BASE_LATITUDE = 63.41535
BASE_LONGITUDE = 10.40657

class TaskScooterDBComponent:
    """
    Listens for MQTT updates, updates scooters, creates tasks, 
    and responds to 'get_status_all' intelligently.
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._logger.info('Starting Task/Scooter DB Component')

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

        # Subscribe to topics
        self.mqtt_client.subscribe(MQTT_TOPIC_STATUS)
        self.mqtt_client.subscribe(MQTT_TOPIC_COMMAND)

        self.mqtt_client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        self._logger.info(f'MQTT connected with result code {rc}')

    def on_message(self, client, userdata, msg):
        try:
            self._logger.info(f"Received message on {msg.topic}")
            payload = json.loads(msg.payload.decode('utf-8'))

            if msg.topic.endswith("/command"):
                if isinstance(payload, dict) and payload.get("command") == "get_status_all":
                    self._handle_get_status_all()
                else:
                    self._handle_status_update(payload)

        except Exception as e:
            self._logger.error(f"Failed to process message: {e}")

    def _handle_status_update(self, status_data):
        try:
            con = sqlite3.connect("database.db")
            cur = con.cursor()

            for scooter_key, statuses in status_data.items():
                scooter_id = int(scooter_key[1:])

                if "RESERVED" in statuses:
                    cur.execute("""
                        UPDATE scootere
                        SET available = 0
                        WHERE id = ?
                    """, (scooter_id,))
                    self._logger.info(f"Scooter {scooter_id} is RESERVED -> unavailable")
                    continue
                else:
                    cur.execute("""
                        UPDATE scootere
                        SET available = 1
                        WHERE id = ?
                    """, (scooter_id,))
                    self._logger.info(f"Scooter {scooter_id} marked as available")

            if "MUST_MOVE" in statuses:
                # Check if a task already exists for this scooter
                cur.execute("SELECT 1 FROM oppgaver WHERE scooterid = ?", (scooter_id,))
                task_exists = cur.fetchone()

                if not task_exists:
                    task = (
                        scooter_id,
                        0,
                        BASE_LATITUDE + random.uniform(-0.005, 0.005),
                        BASE_LONGITUDE + random.uniform(-0.005, 0.005),
                        random.uniform(5.0, 20.0),
                        random.randint(10, 50)
                    )
                    cur.execute("""
                        INSERT INTO oppgaver (scooterid, brukerid, latitude, longitude, radius, reward)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, task)
                    self._logger.info(f"Created task for scooter {scooter_id}")
                else:
                    self._logger.info(f"Task already exists for scooter {scooter_id}, skipping creation.")


            con.commit()
            con.close()

        except Exception as e:
            self._logger.error(f"Database update error: {e}")

    def _handle_get_status_all(self):
        try:
            con = sqlite3.connect("database.db")
            cur = con.cursor()

            # Fetch scooters
            cur.execute("SELECT id, available FROM scootere")
            scooters = cur.fetchall()

            # Fetch scooters with active tasks
            cur.execute("SELECT DISTINCT scooterid FROM oppgaver")
            scooters_with_tasks = {row[0] for row in cur.fetchall()}

            con.close()

            status_payload = {}

            for scooter_id, available in scooters:
                statuses = []

                if available == 0:
                    statuses.append("RESERVED")

                if scooter_id in scooters_with_tasks:
                    statuses.append("MUST_MOVE")
                    statuses.append("MISPARKED")
                if len(statuses) != 0:
                     status_payload[f"s{scooter_id}"] = statuses

            self._publish_command(status_payload)

        except Exception as e:
            self._logger.error(f"Failed to fetch and send status: {e}")

    def _publish_command(self, payload):
        try:
            message = json.dumps(payload)
            self._logger.info(f"Publishing to /status: {message}")
            self.mqtt_client.publish(MQTT_TOPIC_STATUS, message, qos=2)
        except Exception as e:
            self._logger.error(f"Failed to publish command: {e}")

    def stop(self):
        self.mqtt_client.loop_stop()

# Logging Setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s'
)

# Run the component
if __name__ == '__main__':
    component = TaskScooterDBComponent()
    print("Listening for /status and /command... Press Ctrl+C to quit.\n")
    try:
        while True:
            pass  # or: time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        component.stop()
