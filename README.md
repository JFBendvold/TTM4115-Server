# 🛴 E-Scooter Server

This is the backend for the E-Scooter rental system, handling **scooter state machines**, **quests**, and **MQTT communication**. Users can complete quests by redistributing scooters and earn rewards.  

## ⚙️ Tech Stack
- **Python** (backend logic)
- **Stmpy** (state machines)
- **paho-mqtt** (MQTT messaging)

## 📂 Project Structure
/e-scooter-server 
│── /src 
│ ├── /controllers # Handles users, quests, and scooters 
│ ├── /models # Defines user, quest, and scooter data 
│ ├── /services # MQTT and reward logic 
│ ├── main.py # Entry point 
│ ├── config.yaml # Configuration settings 
│── requirements.txt # Dependencies 
│── README.md # This file

## 🚀 Getting Started
1. Set up environment (.venv)
2. **Install dependencies**  
        pip install -r requirements.txt
3. Run the server
        python src/main.py

## 📡 MQTT Topics
* scooter/status/{id} – Scooter state updates
* quest/accept/{id} – Quest acceptance
* quest/complete/{id} – Quest completion