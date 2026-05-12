############################################################
#################### IMPORT LIBRARIES ######################
############################################################
from machine import ADC, I2C, Pin
from picozero import Button
from ssd1306 import SSD1306_I2C
from math import log
from time import sleep, ticks_ms, ticks_diff  # <<< DO NOT MODIFY >>>
sleep(5) # required for stability          # <<< DO NOT MODIFY >>>

# Imports for MQTT communication           # <<< DO NOT MODIFY >>>
import network                             # <<< DO NOT MODIFY >>>
import json                                # <<< DO NOT MODIFY >>>
from umqtt.robust import MQTTClient        # <<< DO NOT MODIFY >>>

# Imports the library to make a random number. This is used to
#    create a psuedo temperature value to transmit for demo
#    purposes. You don't need this library for the project.
import random

############################################################
################# SPECIFY PINS AND OBJECTS #################
############################################################
thermistor = ADC(28)

# OLED object
display_width = 128 # pixel x values = 0 to 127
display_height = 64 # pixel y values = 0 to 63
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000) # TX pin is Pin 0, RX pin is Pin 1
display = SSD1306_I2C(display_width, display_height, i2c)

x_joy = ADC(27)
y_Joy = ADC(26)
Button_Joy = Button(21)

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

# Connect to Wi-Fi                                          # <<< DO NOT MODIFY >>>
wlan = network.WLAN(network.STA_IF)                         # <<< DO NOT MODIFY >>>
wlan.active(True)                                           # <<< DO NOT MODIFY >>>
wlan.config(pm = 0xa11140) # disable Wi-Fi low power mode   # <<< DO NOT MODIFY >>>
wlan.connect(SSID, PASSWORD)                                # <<< DO NOT MODIFY >>>

# print("Attempting to connect to Wi-Fi")
# while not wlan.isconnected():                               # <<< DO NOT MODIFY >>>
#     pass                                                    # <<< DO NOT MODIFY >>>
# 
# sleep(2)  # Extra delay for stability                       # <<< DO NOT MODIFY >>>
# print("Connected to Wi-Fi!")
# 
# 
# 
# # Connect to MQTT broker with reconnect support         # <<< DO NOT MODIFY >>>
# client = MQTTClient(f"client_{SENSOR_ID}", MQTT_BROKER) # <<< DO NOT MODIFY >>>
# client.DEBUG = True                                     # <<< DO NOT MODIFY >>>

# Try to connect to MQTT broker                         # <<< DO NOT MODIFY >>>
try:                                                    # <<< DO NOT MODIFY >>>
   client.connect()                                    # <<< DO NOT MODIFY >>> 
   print("Connected to MQTT broker!")
except Exception as e:                                  # <<< DO NOT MODIFY >>>#
 print("Failed to connect to MQTT broker:", e)

# voltage divider
V_in = 3.3 #[volts]
R1 = 10000 #[ohms], 10K resistor

# steinhart constants
A = 1.129e-3
B= 2.341e-4
C= 8.767e-8

#get temp
def getTempC():
    adc_value = thermistor.read_u16() # 0 to 65535
    V_out = (V_in/65535) * adc_value #[volts]
    Rt = (V_out * R1) / (V_in - V_out) # calculate resistance
    TempK = 1 / (A + (B * log(Rt)) + (C*pow(log(Rt), 3) ) )
    temperature_sensor_reading = TempK - 273.15 #[celcius]
    return temperature_sensor_reading

left1_flag = False
right1_flag = False
left2_flag = False
right2_flag = False
time_flag = False

display.fill(0)
display.text("Input the", 0, 10)
display.text("password.", 0, 20)
display.show()

while (time_flag == False):
    while(left1_flag == False):
        x_joy_value = x_joy.read_u16()
        if (x_joy_value < 500):
            left1_flag = True
            start_time = ticks_ms()
            print("Left Check!")
    while(right1_flag == False):
        x_joy_value = x_joy.read_u16()
        if (x_joy_value > 64000):
            right1_flag = True
            print("Right Check!")
    while(left2_flag == False):
        x_joy_value = x_joy.read_u16()
        if (x_joy_value < 500):
            left2_flag = True
            print("Left 2 Check!")
    while(right2_flag == False):
        x_joy_value = x_joy.read_u16()
        if (x_joy_value > 64000):
            right2_flag = True
            end_time = ticks_ms()
            print("Right 2 Check!")
    
            deltaTime = ticks_diff(end_time, start_time) / 1000
    if (deltaTime <= 3):
        time_flag = True
        display.fill(0)
        display.text("UNLOCKED", 0, 0)
        display.show()
        print(deltaTime)
    else:
        display.fill(0)
        display.text("UNLOCKED", 0, 0)
        display.show()
        left1_flag = False
        right1_flag = False
        left2_flag = False
        right2_flag = False
        
#OLED Menu
display.fill(0)
display.text("Welcome to Main Page", 0, 0)
display.text("Up: Temp C", 0, 15)
display.text("L: Temp F", 0, 35)
display.text("R: Status", 0, 50)
display.show()

############################################################
####################### INFINITE LOOP ######################
############################################################
# while True:    
#     # Create and send MQTT payload                               # <<< DO NOT MODIFY >>>
#     message_data = {                                             # <<< DO NOT MODIFY >>>
#         "sensorID": SENSOR_ID,                                   # <<< DO NOT MODIFY >>>
#         "temperatureReading": temperature_sensor_reading         # <<< DO NOT MODIFY >>>
#     }                                                            # <<< DO NOT MODIFY >>>
#     message_json = json.dumps(message_data)  # Convert to JSON   # <<< DO NOT MODIFY >>>
#     
#     # Try to publish message to MQTT broker                                    # <<< DO NOT MODIFY >>>
#     try:                                                                       # <<< DO NOT MODIFY >>>
#         client.publish(TOPIC, message_json, retain=True) # Send MQTT payload   # <<< DO NOT MODIFY >>>
#         print(f"Published: {message_json}") # Print MQTT payload to the Shell
#     except Exception as e:                                                     # <<< DO NOT MODIFY >>>
#         print("Publish failed:",e)
#     
#     sleep(2) # Send MQTT payload every 2 seconds



