from flask import Flask, request, jsonify, render_template
import logging
import bcrypt
import sqlite3
from secrets import token_hex
import paho.mqtt.client as mqtt
import json

MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883
MQTT_TOPIC_INPUT = 'ttm4115/team_18/command'
MQTT_TOPIC_OUTPUT = 'ttm4115/team_18/answer'

class RegistrationCommandSenderComponent:
    """
    CLI or programmatic interface to send registration commands via MQTT.
    """

    def on_connect(self, client, userdata, flags, rc):
        self._logger.debug(f'MQTT connected with result code {rc}')

    def on_message(self, client, userdata, msg):
        # Optional: handle messages from server if needed
        self._logger.debug(f'Message received on topic {msg.topic}: {msg.payload.decode()}')

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._logger.info('Starting Registration Command Sender (no GUI)')

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        self.mqtt_client.loop_start()

    def publish_command(self, command: dict):
        payload = json.dumps(command)
        self._logger.info(f"Publishing command: {payload}")
        self.mqtt_client.publish(MQTT_TOPIC_INPUT, payload=payload, qos=2)

    def register_user(self, username: str, password: str):
        command = {"command": "register", "name": username, "password": password}
        self.publish_command(command)

    def verify_user(self, username: str, code: str):
        command = {"command": "verify", "name": username, "code": code}
        self.publish_command(command)

    def cancel_registration(self, username: str):
        command = {"command": "cancel", "name": username}
        self.publish_command(command)

    def stop(self):
        self.mqtt_client.loop_stop()

# --- Logging Setup ---
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s'
)


app = Flask(__name__)

# In-memory storage for temporary verification codes
verification_codes = {}

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    return render_template('index.html')


from flask import Flask, request, jsonify, render_template
import logging
import bcrypt
import sqlite3
from secrets import token_hex

app = Flask(__name__)

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for temporary verification codes
verification_codes = {}

# Initialize SQLite database connection function
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/get_verification_code', methods=['POST'])
def get_verification_code():
    try:
        data = request.json
        username = data.get('user')

        if not username:
            return jsonify({"error": "Username is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT * FROM brukere WHERE navn = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User does not exist"}), 404

        # Generate a new verification code
        verification_code = token_hex(2)
        verification_codes[username] = verification_code

        logger.info(f"New verification code for {username}: {verification_code}")
        return jsonify({"Code": verification_code}), 200
    except Exception as e:
        logger.error(f"Error generating verification code: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/get_scooters', methods=['GET'])
def get_scooter():
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row  # Makes row access easier as dictionaries
        cursor = conn.cursor()

        # Fetch all scooter data from the database
        cursor.execute("SELECT * FROM scootere")
        scooters = cursor.fetchall()
        conn.close()

        # Prepare response data
        scooter_list = []
        for sco in scooters:
            scooter_data = {
                "id": sco["id"],
                "latitude": sco["latitude"],
                "longitude": sco["longitude"],
                "available": bool(sco["available"])
            }
            scooter_list.append(scooter_data)

        return jsonify({"scooters": scooter_list}), 200

    except Exception as e:
        logger.error(f"Error fetching scooters: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/take_task', methods=['POST'])
def take_task():
    try:
        data = request.json
        task_id = data.get('task_id')
        username = data.get('user')  # Username provided in the request

        if not task_id or not username:
            return jsonify({"error": "Task ID and Username are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch user ID from username
        cursor.execute("SELECT id FROM brukere WHERE navn = ?", (username,))
        user = cursor.fetchone()
        
        if user is None:
            return jsonify({"error": "User does not exist"}), 404

        user_id = user[0]

        # Check if the task is available (not taken)
        cursor.execute("SELECT * FROM oppgaver WHERE id = ? AND brukerid == 0", (task_id,))
        task = cursor.fetchone()

        if task is None:
            return jsonify({"error": "Task is either taken or does not exist"}), 404

        # Update the task to assign it to the user
        cursor.execute("UPDATE oppgaver SET brukerid = ? WHERE id = ?", (user_id, task_id))
        conn.commit()
        conn.close()

        logger.info(f"Task {task_id} successfully taken by user {username}.")
        return jsonify({"message": f"Task {task_id} successfully taken by user {username}"}), 200

    except Exception as e:
        logger.error(f"Error taking task: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/get_tasks', methods=['GET'])
def get_tasks():
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch all tasks with their associated scooters
        query = """
        SELECT oppgaver.id as task_id, oppgaver.scooterid, oppgaver.latitude as target_latitude, oppgaver.longitude as target_longitude,
               oppgaver.reward, scootere.latitude as current_latitude, scootere.longitude as current_longitude
        FROM oppgaver
        INNER JOIN scootere ON oppgaver.scooterid = scootere.id
        WHERE oppgaver.brukerid == 0;
        """

        cursor.execute(query)
        tasks = cursor.fetchall()
        conn.close()

        # Prepare response data in the desired format
        task_list = []
        for task in tasks:
            task_data = {
                "id": task["task_id"],
                "scooterId": str(task["scooterid"]),
                "currentLocation": {
                    "latitude": task["current_latitude"],
                    "longitude": task["current_longitude"]
                },
                "targetLocation": {
                    "latitude": task["target_latitude"],
                    "longitude": task["target_longitude"]
                },
                "distance": calculate_distance(task["current_latitude"],task["current_longitude"],task["target_latitude"],task["target_longitude"]),  # We can calculate this if needed.
                "reward": task["reward"]
            }
            task_list.append(task_data)

        return jsonify({"tasks": task_list}), 200

    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        return jsonify({"error": str(e)}), 500




@app.route('/api/unlock', methods=['POST'])
def unlock():
    try:
        data = request.json
        scooter_id = data.get('scooter_id')
        username = data.get('user')

        if not scooter_id or not username:
            return jsonify({"error": "Scooter ID and Username are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the scooter exists
        cursor.execute("SELECT * FROM scootere WHERE id = ?", (scooter_id,))
        scooter = cursor.fetchone()

        if scooter is None:
            return jsonify({"error": "Scooter not found"}), 404

        # Unlock the scooter (set available = False)
        cursor.execute("UPDATE scootere SET available = ? WHERE id = ?", (False, scooter_id))
        conn.commit()
        conn.close()
        logger.info(f"Scooter {scooter_id} successfully unlocked by {username}.")
        return jsonify({"message": f"Scooter {scooter_id} successfully unlocked"}), 200

    except Exception as e:
        logger.error(f"Error unlocking scooter: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/lock', methods=['POST'])
def lock():
    try:
        data = request.json
        scooter_id = data.get('scooter_id')
        username = data.get('user')

        if not scooter_id or not username:
            return jsonify({"error": "Scooter ID and Username are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the scooter exists
        cursor.execute("SELECT * FROM scootere WHERE id = ?", (scooter_id,))
        scooter = cursor.fetchone()

        if scooter is None:
            return jsonify({"error": "Scooter not found"}), 404

        # Lock the scooter (set available = True)
        cursor.execute("UPDATE scootere SET available = ? WHERE id = ?", (True, scooter_id))
        conn.commit()
        conn.close()

        logger.info(f"Scooter {scooter_id} successfully locked by {username}.")
        return jsonify({"message": f"Scooter {scooter_id} successfully locked"}), 200

    except Exception as e:
        logger.error(f"Error locking scooter: {e}")
        return jsonify({"error": str(e)}), 500


from math import radians, cos, sin, sqrt, atan2

# Helper function to calculate distance between two coordinates using the Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in kilometers

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c * 1000  # Convert to meters
    return distance


@app.route('/api/verify_task_completion', methods=['POST'])
def verify_task_completion():
    try:
        data = request.json
        task_id = data.get('task_id')
        username = data.get('user')
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if not task_id or not username or latitude is None or longitude is None:
            return jsonify({"error": "Task ID, Username, latitude, and longitude are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch user ID from username
        cursor.execute("SELECT id, reward FROM brukere WHERE navn = ?", (username,))
        user = cursor.fetchone()

        if user is None:
            return jsonify({"error": "User does not exist"}), 404

        user_id, user_reward = user

        # Fetch the task from the database
        cursor.execute("SELECT latitude, longitude, reward FROM oppgaver WHERE id = ? AND brukerid = ?", (task_id, user_id))
        task = cursor.fetchone()

        if task is None:
            return jsonify({"error": "Task not found or not assigned to this user"}), 404

        target_latitude, target_longitude, reward = task

        # Check if the provided location is within the acceptable radius (e.g., 10 meters)
        distance = calculate_distance(target_latitude, target_longitude, latitude, longitude)
        if distance <= 10:  # Within 10 meters radius
            # Remove the task from the database
            cursor.execute("DELETE FROM oppgaver WHERE id = ?", (task_id,))

            # Update user reward
            new_reward = user_reward + reward
            cursor.execute("UPDATE brukere SET reward = ? WHERE id = ?", (new_reward, user_id))

            conn.commit()
            conn.close()

            logger.info(f"Task {task_id} completed by user {username}. Reward added: {reward}")
            return jsonify({"message": f"Task completed successfully. Reward added: {reward}"}), 200
        else:
            conn.close()
            return jsonify({"error": f"Task completion failed. You are {distance:.2f} meters away from the target location."}), 400

    except Exception as e:
        logger.error(f"Error verifying task completion: {e}")
        return jsonify({"error": str(e)}), 500




@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('user')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        # Check if user already exists
        cur.execute("SELECT * FROM brukere WHERE navn = ?", (username,))
        if cur.fetchone():
            return jsonify({"error": "User already exists"}), 400

        # Store the user in the database
        cur.execute("INSERT INTO brukere (navn, passord, reward) VALUES (?, ?, ?)", (username, hashed_password,0))
        conn.commit()
        conn.close()

        # Generate a verification code
        verification_code = token_hex(2)
        verification_codes[username] = verification_code

        logger.info(f"Verification code for {username}: {verification_code}")
        
        return jsonify({"Code": f"{verification_code}"}), 200
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    try:
        data = request.json
        username = data.get('user')
        code = data.get('code')

        if not username or not code:
            return jsonify({"error": "Username and code are required"}), 400

        expected_code = verification_codes.get(username)

        if expected_code == code:
            del verification_codes[username]
            logger.info(f"User {username} successfully verified.")
            return jsonify({"message": "User registered successfully."}), 200
        else:
            return jsonify({"error": "Invalid verification code"}), 400
    except Exception as e:
        logger.error(f"Error verifying code: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('user')
        password = data.get('password')

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT passord FROM brukere WHERE navn = ?", (username,))
        row = cur.fetchone()
        conn.close()

        if row and bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8')):
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_user_reward', methods=['POST'])
def get_user_reward():
    try:
        data = request.json
        username = data.get('user')

        if not username:
            return jsonify({"error": "Username is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the user's reward points
        cursor.execute("SELECT reward FROM brukere WHERE navn = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if result is None:
            return jsonify({"error": "User not found"}), 404

        user_reward = result[0] if result[0] is not None else 0  # Handle NoneType case

        return jsonify({"reward": user_reward}), 200

    except Exception as e:
        logger.error(f"Error fetching user reward: {e}")
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
