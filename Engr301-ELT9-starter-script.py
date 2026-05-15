############################################################
#################### IMPORT LIBRARIES ######################
############################################################
from machine import ADC, I2C, Pin
from picozero import Button
from ssd1306 import SSD1306_I2C
from math import log
from time import sleep, ticks_ms, ticks_diff  # <<< DO NOT MODIFY >>>
sleep(1) # required for stability          # <<< DO NOT MODIFY >>>

# Imports for MQTT communication           # <<< DO NOT MODIFY >>>
import network                             # <<< DO NOT MODIFY >>>
import json                                # <<< DO NOT MODIFY >>>
from umqtt.robust import MQTTClient        # <<< DO NOT MODIFY >>>

import random

############################################################
################# SPECIFY PINS AND OBJECTS #################
############################################################
thermistor = ADC(28)

# OLED object
display_width = 128
display_height = 64
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
display = SSD1306_I2C(display_width, display_height, i2c)

x_joy = ADC(27)
y_Joy = ADC(26)
Button_Joy = Button(18)

############################################################
##################### OTHER SETUP STUFF ####################
############################################################

# Wi-Fi and MQTT settings
SSID = "WilfongEngr301" # Raspberry Pi 4 Wi-Fi name                               # <<< DO NOT MODIFY >>>
PASSWORD = "BoilerUp" # Raspberry Pi 4 Wi-Fi password, WPA/WPA2 security          # <<< DO NOT MODIFY >>>
MQTT_BROKER = "10.42.0.1"  # Raspberry Pi 4's IP                                  # <<< DO NOT MODIFY >>>
TOPIC = "pico/data" # "pico/data" is just a label                                 # <<< DO NOT MODIFY >>>
                    # It helps organize messages, like folders in a file system.  # <<< DO NOT MODIFY >>>
                    # The TOPIC could be any string, but leave it as "pico/data"  # <<< DO NOT MODIFY >>>

# SENSOR_ID = "Team02"  # !!!-- CHANGE THIS AS DIRECTED BY DR. WILFONG --!!!

SENSOR_ID = "Team02"

 # Connect to Wi-Fi                                          # <<< DO NOT MODIFY >>>
wlan = network.WLAN(network.STA_IF)                         # <<< DO NOT MODIFY >>>
wlan.active(True)                                           # <<< DO NOT MODIFY >>>
wlan.config(pm = 0xa11140) # disable Wi-Fi low power mode   # <<< DO NOT MODIFY >>>
wlan.connect(SSID, PASSWORD)                                # <<< DO NOT MODIFY >>>

print("Attempting to connect to Wi-Fi")
while not wlan.isconnected():                               # <<< DO NOT MODIFY >>>
    pass                                                   # <<< DO NOT MODIFY >>>

sleep(2)  # Extra delay for stability                       # <<< DO NOT MODIFY >>>
print("Connected to Wi-Fi!")

# Connect to MQTT broker with reconnect support         # <<< DO NOT MODIFY >>>
client = MQTTClient(f"client_{SENSOR_ID}", MQTT_BROKER) # <<< DO NOT MODIFY >>>
client.DEBUG = True                                     # <<< DO NOT MODIFY >>>

# Try to connect to MQTT broker                         # <<< DO NOT MODIFY >>>
try:                                                    # <<< DO NOT MODIFY >>>
   client.connect()                                    # <<< DO NOT MODIFY >>> 
   print("Connected to MQTT broker!")
except Exception as e:                                             # <<< DO NOT MODIFY >>>
   print("Failed to connect to MQTT broker:", e)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        wlan.config(pm=0xa11140)  # disable Wi-Fi low power mode
    except Exception:
        pass

    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        print("Attempting to connect to Wi-Fi")
        while not wlan.isconnected():
            sleep(0.1)
        sleep(2)
        print("Connected to Wi-Fi!")
    return wlan


def connect_mqtt():
    mqtt_client = MQTTClient(f"client_{SENSOR_ID}", MQTT_BROKER)
    mqtt_client.DEBUG = True
    try:
        mqtt_client.connect()
        print("Connected to MQTT broker!")
    except Exception as e:
        print("Failed to connect to MQTT broker:", e)
        raise
    return mqtt_client


class _NullMQTTClient:
    def publish(self, *args, **kwargs):
        raise RuntimeError("MQTT client not connected")


# Establish connections (required for MQTT publish below)
try:
    wlan = connect_wifi()
    client = connect_mqtt()
except Exception as e:
    print("Startup connection failed:", e)
    client = _NullMQTTClient()

SENSOR_ID = "Team02"

# voltage divider
V_in = 3.3
R1 = 10000

# steinhart constants
A = 1.129e-3
B = 2.341e-4
C = 8.767e-8

def getTempC():
    adc_value = thermistor.read_u16()
    V_out = (V_in/65535) * adc_value
    Rt = (V_out * R1) / (V_in - V_out)
    TempK = 1 / (A + (B * log(Rt)) + (C*pow(log(Rt), 3)))
    temperature_sensor_reading = TempK - 273.15
    return temperature_sensor_reading

def askPassword(timeoutCheck):
    # Password flags
    left1_flag = False
    right1_flag = False
    left2_flag = False
    right2_flag = False
    
    display.text("Input the", 0, 10)
    display.text("password.", 0, 20)
    display.show()

    # Get user input and unlock if matched.
    while(left1_flag == False):
        x_joy_value = x_joy.read_u16()
        if (x_joy_value < 500):
            left1_flag = True
            print("Left Check!")
            sleep(0.2)
        if (timeoutCheck == True):
            broadcast_temp()

    while(right1_flag == False):
        x_joy_value = x_joy.read_u16()
        if (x_joy_value > 64000):
            right1_flag = True
            print("Right Check!")
            sleep(0.2)
        if (timeoutCheck == True):
            broadcast_temp()

    while(left2_flag == False):
        x_joy_value = x_joy.read_u16()
        if (x_joy_value < 500):
            left2_flag = True
            print("Left 2 Check!")
            sleep(0.2)
        if (timeoutCheck == True):
            broadcast_temp()

    while(right2_flag == False):
        x_joy_value = x_joy.read_u16()
        if (x_joy_value > 64000):
            right2_flag = True
            print("Right 2 Check!")
        if (timeoutCheck == True):
            broadcast_temp()
            
    
    return True

if askPassword(False) == True:
    display.fill(0)
    display.text("UNLOCKED", 0, 0)
    start_time = ticks_ms()
    display.show()
    sleep(1)

def broadcast_temp():
    sleep(0.5)
    temperature_sensor_reading = getTempC()
    message_data = {                                             # <<< DO NOT MODIFY >>>
        "sensorID": SENSOR_ID,                                   # <<< DO NOT MODIFY >>>
        "temperatureReading": temperature_sensor_reading         # <<< DO NOT MODIFY >>>
    }                                                            # <<< DO NOT MODIFY >>>
    message_json = json.dumps(message_data)                      # <<< DO NOT MODIFY >>>

    try:                                                                       # <<< DO NOT MODIFY >>>
        client.publish(TOPIC, message_json, retain=True)                       # <<< DO NOT MODIFY >>>
        print(f"Published: {message_json}")
    except Exception as e:                                                     # <<< DO NOT MODIFY >>>
        print("Publish failed:", e)

# Define low and high joystick varaibles
JOY_LOW = 500
JOY_HIGH = 64000

# Translate joy values to directional input for system
def get_joy_dir(x_value, y_value):
    if y_value > JOY_HIGH:
        return "up"
    if y_value < JOY_LOW:
        return "down"
    if x_value < JOY_LOW:
        return "left"
    if x_value > JOY_HIGH:
        return "right"
    return None

#set user on main page
page = "main"
last_dir = None
prev_button_pressed = False

#create data file
file = open("data.txt", "w")
file.close()

############################################################
####################### INFINITE LOOP ######################
############################################################

while True:
    
    #get joystick values
    x_joy_value = x_joy.read_u16()
    y_joy_value = y_Joy.read_u16()
    dir_now = get_joy_dir(x_joy_value, y_joy_value)

    button_pressed = Button_Joy.is_pressed
    button_rising = button_pressed and not prev_button_pressed
    prev_button_pressed = button_pressed
    
    #get temperature values for C and F
    tempC = getTempC()
    tempF = (tempC * 9/5) + 32
    
    # append data to file previously opened
    file = open("data.txt", "a")
    file.write(str(tempC))
    file.write('\n')
    file.close()

    # Straight from stackoverflow, joystick only triggers when right on the edge
    dir_edge = None
    if dir_now is None:
        last_dir = None
    elif last_dir is None:
        dir_edge = dir_now
        last_dir = dir_now

    # Navigation
    if page == "main":
        if dir_edge == "up":
            start_time = ticks_ms() # reset timeout timer on page change
            page = "tempC"
        elif dir_edge == "left":
            start_time = ticks_ms() # reset timeout timer on page change
            page = "tempF"
        elif dir_edge == "right":
            start_time = ticks_ms() # reset timeout timer on page change
            page = "status"
    else:
        # Press button to go back. 
        if button_rising:
            start_time = ticks_ms() # reset timeout timer on page change
            page = "main"
    
    # Show pages
    display.fill(0)
    if page == "main":
        display.text("Main Page", 0, 0)
        display.text("Up: Temp C", 0, 15)
        display.text("Left: Temp F", 0, 30)
        display.text("Right: Status", 0, 45)
    elif page == "tempC":
        display.text("Temp C Menu", 0, 0)
        display.text(str(round(tempC, 2)) + " C", 0, 20)
        display.text("Press to back", 0, 50)
    elif page == "tempF":
        display.text("Temp F Menu", 0, 0)
        display.text(str(round(tempF, 2)) + " F", 0, 20)
        display.text("Press to back", 0, 50)
    elif page == "status":
        display.text("Status Menu", 0, 0)
        display.text("WiFi: Connected", 0, 20)
        display.text("MQTT: Connected", 0, 35)
        display.text("Press to back", 0, 50)
    display.show()

    end_time = ticks_ms()
    deltaTime = ticks_diff(end_time, start_time) / 1000
    print(deltaTime)
    while (deltaTime > 10):
        display.fill(0)
        display.text("TIMEOUT", 0, 40)
        timeoutCheck = True
        display.show()
        broadcast_temp()
        if askPassword(True) == True:
            start_time = ticks_ms()
            break
        sleep(0.1)
    broadcast_temp()
    sleep(0.1)


