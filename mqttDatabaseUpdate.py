import paho.mqtt.client as mqtt
import json
import logging
import sqlite3

# MQTT Setup
MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883
MQTT_TOPIC_INPUT = 'ttm4115/team_18/command'

class TaskScooterDBComponent:
    """
    Listens for MQTT messages and updates tasks (oppgaver) or scooter availability (scootere).
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._logger.info('Starting Task/Scooter DB Component')

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        self.mqtt_client.subscribe(MQTT_TOPIC_INPUT)
        self.mqtt_client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        self._logger.info(f'MQTT connected with result code {rc}')

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            command = payload.get("command")

            if command == "new_task":
                self._handle_new_task(payload)
            elif command == "update_scooter":
                self._handle_update_scooter(payload)
            else:
                self._logger.warning(f"Unknown command: {command}")

        except Exception as e:
            self._logger.error(f"Failed to process message: {e}")

    def _handle_new_task(self, data):
        try:
            con = sqlite3.connect("database.db")
            cur = con.cursor()
            cur.execute("""
                INSERT INTO oppgaver (scooterid, brukerid, latitude, longitude, radius, reward)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data["scooterid"],
                data["brukerid"],
                data["latitude"],
                data["longitude"],
                data["radius"],
                data["reward"]
            ))
            con.commit()
            con.close()
            self._logger.info(f"Inserted new task for scooter {data['scooterid']}")
        except Exception as e:
            self._logger.error(f"Error inserting task: {e}")

    def _handle_update_scooter(self, data):
        try:
            con = sqlite3.connect("database.db")
            cur = con.cursor()
            cur.execute("""
                UPDATE scootere
                SET available = ?
                WHERE id = ?
            """, (
                data["available"],
                data["id"]
            ))
            con.commit()
            con.close()
            self._logger.info(f"Updated scooter {data['id']} availability to {data['available']}")
        except Exception as e:
            self._logger.error(f"Error updating scooter: {e}")

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
    try:
        input("Listening for commands... Press Enter to quit.\n")
    finally:
        component.stop()
