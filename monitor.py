#!/usr/bin/python

import time
import Adafruit_CharLCD as LCD
import Adafruit_GPIO.MCP230xx as MCP
import Adafruit_DHT
import RPi.GPIO as io
import os

io.setmode(io.BCM)
pwr_pin = 13
tmp_pin = 4
water_pin = 24 
alarm_pin = 23
btn0 = 21
btn1 = 26
btn2 = 20
btn3 = 19
btn4 = 16

# Define MCP pins connected to the LCD.
lcd_rs        = 0
lcd_en        = 1
lcd_d4        = 2
lcd_d5        = 3
lcd_d6        = 4
lcd_d7        = 5
lcd_red       = 6
lcd_green     = 7
lcd_blue      = 8

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

# Alternatively specify a 20x4 LCD.
# lcd_columns = 20
# lcd_rows    = 4

# Initialize MCP23017 device using its default 0x20 I2C address.
gpio = MCP.MCP23017()

# Alternatively you can initialize the MCP device on another I2C address or bus.
# gpio = MCP.MCP23017(0x24, busnum=1)

# Initialize the LCD using the pins
lcd = LCD.Adafruit_RGBCharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                              lcd_columns, lcd_rows, lcd_red, lcd_green, lcd_blue,
                              gpio=gpio)
# Init DHT22
tmp_sensor = Adafruit_DHT.DHT22

# Init button io
io.setup(btn0, io.IN)
io.setup(btn1, io.IN)
io.setup(btn2, io.IN)
io.setup(btn3, io.IN)
io.setup(btn4, io.IN)

# Init pwr testing io
io.setup(pwr_pin, io.IN)
time.sleep(0.2)


# Init alarm io
io.setup(alarm_pin, io.OUT)
io.output(alarm_pin, io.LOW)

# Init water sensor io
io.setup(water_pin, io.IN)

# Grab temp and humidity data
humidity, temperature = Adafruit_DHT.read_retry(tmp_sensor, tmp_pin)
benchmark = temperature

def alert(number, alertString):
    os.system("""echo \"{0}\" | mail -s "ALERT" {1}@msg.fi.google.com""".format(alertString, number))         
    print("""echo \"{0}\" | mail -s "ALERT" {1}@msg.fi.google.com""".format(alertString, number))         
    lcd.clear()
    lcd.home()
    lcd.message(alertString)
    while not io.input(btn0):
        pass
    # Wait for ok
    while io.input(btn0): 
        io.output(alarm_pin, io.HIGH)
        time.sleep(0.1)
    while not io.input(btn0):
        pass
    io.output(alarm_pin, io.LOW)
    lcd.clear()
    lcd.home()
    lcd.message("Suppressed\nHit ok to reset")
    time.sleep(2)
    lcd.clear()
    return

def enterNumber():
    lcd.clear()
    lcd.home()
    col = 0
    row = 0
    number = [6,1,7,0,0,0,0,0,0,0]
    numberStr = ''
    for i in number:
        numberStr += str(i)
    print (str(number))
    lcd.message(numberStr)
    lcd.show_cursor(True)
    while io.input(btn0):
        time.sleep(.2)

        # Setup number string
        numberStr = ''
        for i in number:
            numberStr += str(i)

        # Setup cursor to print home
        lcd.home()
        lcd.message(numberStr)

        # Button commands
        lcd.set_cursor(col, row)
        if not io.input(btn4):
            if col == 0:
                col = 15
            else:
                col -= 1
        if not io.input(btn3):
            if col == 15:
                col = 0
            else:
                col += 1
        lcd.set_cursor(col, row)
        if not io.input(btn2):
            if number[col] < 9:
                number[col] += 1
        if not io.input(btn1):
            if number[col] > 0:
                number[col] -= 1

    numberStr = ''
    for i in number:
        numberStr += str(i)
    return numberStr

if not io.input(pwr_pin):
    print('No power!\n')

suppressPwr = False
suppressWater = False
suppressTemp = False

phone = enterNumber()
alertStr = ""
alertStrNew = ""
while True:

    humidity, temperature = Adafruit_DHT.read_retry(tmp_sensor, tmp_pin)
    lcd.home()
    lcd.message('Temp: ')
    lcd.message('{:4.1f}'.format(temperature))
    lcd.message('\nHumidity: ')
    lcd.message('{:4.1f}'.format(humidity))
    if temperature > benchmark + 0.3 and not suppressTemp: # Breath test
        alertStrNew += " Tmp "
        suppressTemp = True
    if not io.input(pwr_pin) and not suppressPwr:
        alertStrNew += " Pwr "
        suppressPwr = True
    if not io.input(water_pin) and not suppressWater:
        alertStrNew += " Wtr "
        suppressWater = True
    #if not io.input(btn0) and not suppressTemp: # Simulate low temp for now
        #lcd.clear()
        #lcd.home()
        #lcd.message('Button 0')
        #alert(phone, "Temp ")
    #    suppressTemp = True
    #    while not io.input(btn0):
    #        pass
    #    alertStrNew += " Tmp "
    if not io.input(btn0):
        while not io.input(btn0):
            pass
        # Clear suppressions and reset
        alertStr = ""
        alertStrNew = ""
        lcd.clear()
        lcd.home()
        lcd.message("Suppressions\nreset")
        print ("Clearing suppressions")
        time.sleep(1)
        suppressTemp = False
        suppressWater = False
        suppressPwr = False
    
    # Something changed, raise alert
    if alertStr != alertStrNew:
        alertStr = alertStrNew
        alert(phone, alertStr)
    if not io.input(btn1):
        phone = enterNumber()
        suppressPwr = False
        suppressWater = False
        suppressTemp = False

        alertStr = ""
        alertStrNew = ""
    #time.sleep(0.1)
