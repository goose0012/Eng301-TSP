import sqlite3
import paho.mqtt.client as mqtt
import json
import threading
import time
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import numpy as np

# === Settings ===
MQTT_BROKER = "localhost"
TOPIC = "pico/data"
DB_PATH = "/home/admin/mqtt_data.db"

# === Database connection with threading lock ===
db_lock = threading.Lock()
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# === MQTT Subscriber Function ===
def mqtt_subscriber():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("[MQTT] Connected successfully!")
            client.subscribe(TOPIC)
        else:
            print(f"[MQTT] Connection failed with code {rc}")
    
    # Define allowed sensorIDs
    ALLOWED_SENSOR_ID = {"Team01", "Team02", "Team03", "Team04", "Team05", "Team06", "Team07", "Team08", "Team09", "Team10"}
    def on_message(client, userdata, message):
        try:
            payload = message.payload.decode('utf-8')
            data = json.loads(payload)

            # --- Validate payload structure ---
            if not isinstance(data, dict):
                print(f"[ERROR] Invalid payload format: not a JSON object")
                return

            sensor = data.get("sensorID")
            temp = data.get("temperatureReading")

            # Validate sensorID
            if not isinstance(sensor, str) or not sensor.strip():
                print(f"[ERROR] Invalid or missing sensorID: {sensor}")
                return
            
            # Enforce whitelist
            if sensor not in ALLOWED_SENSOR_ID:
                print(f"[ERROR] Unauthorized sensorID: {sensor}")
                return

            # Validate temperatureReading
            try:
                temp = float(temp)
            except (ValueError, TypeError):
                print(f"[ERROR] Invalid temperature value from {sensor}: {temp}")
                return

            # Optional: sanity check on temp value range
            if not (0 <= temp <= 100):
                print(f"[WARNING] Unusual temperature value from {sensor}: {temp}")
                return # don't add this unusual temp value to database

            # --- If all validations pass ---
            print(f"[MQTT] Valid message received from {sensor}: {temp:.2f}°C")

            with db_lock:
                cursor.execute(
                    "INSERT INTO temperatureData (sensorID, temperatureReading) VALUES (?, ?)",
                    (sensor, temp)
                )
                conn.commit()

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON decode error: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
        

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_BROKER, 1883, keepalive=60)
            client.loop_forever()
        except Exception as e:
            print(f"[MQTT] Connection error: {e}")
            time.sleep(5)  # Retry after delay

# === Start Subscriber Thread ===
subscriber_thread = threading.Thread(target=mqtt_subscriber, daemon=True)
subscriber_thread.start()

# === Dashboard in Main Thread ===
plt.ion()
fig, ax = plt.subplots()
sensor_order = ["Team01", "Team02", "Team03", "Team04", "Team05", "Team06", "Team07", "Team08", "Team09"]
heatmap_min_value = 20
heatmap_max_value = 27
heatmap_type = 'RdYlBu_r'
grid_values = np.zeros((3,3)) # 3x3 grid initized to zeros
heatmap = ax.imshow(grid_values, cmap=heatmap_type, vmin=heatmap_min_value, vmax=heatmap_max_value) #adjust ranges later

plt.colorbar(heatmap, ax=ax)

try:
    while True:
        grid_values = np.zeros((3,3)) # 3x3 grid initized to zeros
        
        with db_lock:
            cursor.execute("""
                SELECT sensorID, temperatureReading
                FROM (
                    SELECT sensorID, temperatureReading, 
                            ROW_NUMBER() OVER (PARTITION BY sensorID ORDER BY timestamp DESC) as rn
                    FROM temperatureData
                ) sub
                WHERE rn = 1
            """)
            data = cursor.fetchall()
        
        # map sensor readings to the grid
        user_to_value = {row[0]: float(row[1]) for row in data if row[0] in sensor_order}
        
        for idx, sensor in enumerate(sensor_order):
            row = idx // 3
            col = idx % 3
            value = user_to_value.get(sensor, np.nan) # use NaN if missing
            grid_values[row,col] = value
            
        ax.clear()
        heatmap = ax.imshow(grid_values, cmap=heatmap_type, vmin=heatmap_min_value, vmax=heatmap_max_value) #adjust ranges later
        
        #add text labels
        for i in range(3):
            for j in range(3):
                idx = i * 3 + j
                sensor = sensor_order[idx]
                value = grid_values[i,j]
                label = f"{value:.1f}" if not np.isnan(value) else "NaN"
                
                #sensor ID above
                txt1 = ax.text(j,i - 0.1, sensor, ha='center', va='center', color='white', fontsize=12, weight='bold')
                txt1.set_path_effects([path_effects.Stroke(linewidth=1.5, foreground='black'), path_effects.Normal()])
                
                #temp value below
                txt2 = ax.text(j,i + 0.1, label, ha='center', va='center', color='white', fontsize=12)
                txt2.set_path_effects([path_effects.Stroke(linewidth=1.5, foreground='black'), path_effects.Normal()])
        
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("Live temp heatmap")
        
        
        plt.draw()
        plt.pause(5)

except KeyboardInterrupt:
    print("\n[INFO] Shutting down...")
    conn.close()
    print("[INFO] Database connection closed.")
