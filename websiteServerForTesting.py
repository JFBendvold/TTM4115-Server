from flask import Flask, request, jsonify, render_template
import logging
import bcrypt
import sqlite3
from secrets import token_hex

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
        cur.execute("INSERT INTO brukere (navn, passord) VALUES (?, ?)", (username, hashed_password))
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
