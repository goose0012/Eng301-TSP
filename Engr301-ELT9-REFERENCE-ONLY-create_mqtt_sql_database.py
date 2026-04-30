# Import libraries
import sqlite3

# Create the database file
db_path = "/home/admin/mqtt_data.db" # change path if needed
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create table with the necessary fields
cursor.execute("""
	CREATE TABLE IF NOT EXISTS temperatureData (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		sensorID TEXT,
		temperatureReading TEXT,
		timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
	);
""")

# Commit changes and close connection
conn.commit()

# Pre-populate SQL table with one entry
cursor.execute(
	"INSERT INTO temperatureData (sensorID, temperatureReading) VALUES (?,?)",
	("Team01",75)
)

# Commit changes and close connection
conn.commit()

conn.close()

# Enable Write Ahead Logging (WAL) mode
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode = WAL;")
conn.commit()
conn.close()
