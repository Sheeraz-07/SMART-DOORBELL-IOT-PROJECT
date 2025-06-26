# hardware.py

import time
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# OLED setup
WIDTH = 128
HEIGHT = 64
oled_reset = board.D4
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, reset=None)

# Buzzer setup (GPIO 17 or any free pin)
buzzer = digitalio.DigitalInOut(board.D17)
buzzer.direction = digitalio.Direction.OUTPUT

# Display label on OLED
def show_label_on_oled(label):
    oled.fill(0)
    oled.show()
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((0, 20), f"Detected: {label}", font=font, fill=255)
    oled.image(image)
    oled.show()

# Buzzer logic
def buzz_for(label):
    if label.lower() == "unknown":
        for _ in range(3):
            buzzer.value = True
            time.sleep(0.5)
            buzzer.value = False
            time.sleep(0.5)
    else:
        buzzer.value = True
        time.sleep(1)
        buzzer.value = False
