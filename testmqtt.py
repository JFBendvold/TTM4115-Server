# send_status_test.py
import paho.mqtt.client as mqtt
import json
import time

MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883
MQTT_TOPIC_STATUS = 'ttm4115/team_18/status'


MQTT_TOPIC_COMMAND = 'ttm4115/team_18/command'

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode('utf-8'))
    print(f"Received reply: {json.dumps(payload, indent=2)}")

def request_status():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.subscribe(MQTT_TOPIC_COMMAND)
    client.loop_start()

    request = {"command": "get_status_all"}
    message = json.dumps(request)
    print(f"Sending get_status_all request to {MQTT_TOPIC_COMMAND}")
    client.publish(MQTT_TOPIC_COMMAND, message, qos=2)

    time.sleep(5)
    client.loop_stop()


def send_status():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()

    payload = {
        "s0": ["MISPARKED", "MUST_MOVE"],  # Available + must move
        "s1": ["MISPARKED"],                # Available
        "s2": ["RESERVED"],                 # Reserved -> unavailable
        "s3": ["MUST_MOVE"]                 # Must move
    }

    message = json.dumps(payload)
    print(f"Sending to {MQTT_TOPIC_STATUS}: {message}")
    client.publish(MQTT_TOPIC_STATUS, message, qos=2)

    time.sleep(2)
    client.loop_stop()

if __name__ == "__main__":
    send_status()
    request_status()
