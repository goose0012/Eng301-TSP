############################################################
#################### IMPORT LIBRARIES ######################
############################################################
from machine import ADC, I2C, Pin
from picozero import Button
from ssd1306 import SSD1306_I2C
from math import log
from time import sleep  # <<< DO NOT MODIFY >>>

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
Button_Joy = Pin(21, Pin.IN, Pin.PULL_UP)  # Raw pin, active-low

############################################################
##################### OTHER SETUP STUFF ####################
############################################################

SSID = "WilfongEngr301"                                            # <<< DO NOT MODIFY >>>
PASSWORD = "BoilerUp"                                              # <<< DO NOT MODIFY >>>
MQTT_BROKER = "10.42.0.1"                                          # <<< DO NOT MODIFY >>>
TOPIC = "pico/data"                                                # <<< DO NOT MODIFY >>>

SENSOR_ID = "Team02"

client = MQTTClient("PicoW", MQTT_BROKER)

wlan = network.WLAN(network.STA_IF)                                # <<< DO NOT MODIFY >>>
wlan.active(True)                                                  # <<< DO NOT MODIFY >>>
wlan.config(pm = 0xa11140)                                         # <<< DO NOT MODIFY >>>
wlan.connect(SSID, PASSWORD)                                       # <<< DO NOT MODIFY >>>

try:                                                               # <<< DO NOT MODIFY >>>
   client.connect()                                                # <<< DO NOT MODIFY >>>
   print("Connected to MQTT broker!")
except Exception as e:                                             # <<< DO NOT MODIFY >>>
   print("Failed to connect to MQTT broker:", e)

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

left1_flag = False
right1_flag = False
left2_flag = False
right2_flag = False

display.fill(0)
display.text("Input the", 0, 10)
display.text("password.", 0, 20)
display.show()

while(left1_flag == False):
    x_joy_value = x_joy.read_u16()
    if (x_joy_value < 500):
        left1_flag = True
        print("Left Check!")
        sleep(0.2)

while(right1_flag == False):
    x_joy_value = x_joy.read_u16()
    if (x_joy_value > 64000):
        right1_flag = True
        print("Right Check!")
        sleep(0.2)

while(left2_flag == False):
    x_joy_value = x_joy.read_u16()
    if (x_joy_value < 500):
        left2_flag = True
        print("Left 2 Check!")
        sleep(0.2)

while(right2_flag == False):
    x_joy_value = x_joy.read_u16()
    if (x_joy_value > 64000):
        right2_flag = True
        print("Right 2 Check!")

display.fill(0)
display.text("UNLOCKED", 0, 0)
display.show()
sleep(1)

############################################################
####################### INFINITE LOOP ######################
############################################################
while True:

    display.fill(0)
    display.text("Main Page", 0, 0)
    display.text("Up: Temp C", 0, 15)
    display.text("Left: Temp F", 0, 30)
    display.text("Right: Status", 0, 45)
    display.show()

    in_main_menu = True
    while in_main_menu:
        x_joy_value = x_joy.read_u16()
        y_joy_value = y_Joy.read_u16()

        # Up -> Temp C menu
        if y_joy_value > 64000:
            display.fill(0)
            display.text("Temp C Menu", 0, 0)
            tempC = getTempC()
            display.text(str(round(tempC, 2)) + " C", 0, 20)
            display.show()
            if Button_Joy.value() == 0:
                in_main_menu = False
                sleep(0.2)

        # Left -> Temp F menu
        elif x_joy_value < 500:
            display.fill(0)
            display.text("Temp F Menu", 0, 0)
            tempC = getTempC()
            tempF = (tempC * 9/5) + 32
            display.text(str(round(tempF, 2)) + " F", 0, 20)
            display.show()
            if Button_Joy.value() == 0:
                in_main_menu = False
                sleep(0.2)

        # Right -> Status menu
        elif x_joy_value > 64000:
            display.fill(0)
            display.text("Status Menu", 0, 0)
            display.text("WiFi: Connected", 0, 20)
            display.text("MQTT: Connected", 0, 35)
            display.show()
            if Button_Joy.value() == 0:
                in_main_menu = False
                sleep(0.2)

        sleep(0.3)

    # --- MQTT publish ---
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