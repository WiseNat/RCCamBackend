import RPi.GPIO as GPIO
import time


class ServoController:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)

        # GPIO 12 initialisation, 50hz
        servoPIN = 12
        GPIO.setup(servoPIN, GPIO.OUT)
        self.yaw = GPIO.PWM(servoPIN, 50)
        self.yaw.start(0)

        # GPIO 11 initialisation, 50hz
        servoPIN = 11
        GPIO.setup(servoPIN, GPIO.OUT)
        self.pitch = GPIO.PWM(servoPIN, 50)
        self.pitch.start(0)

    @staticmethod
    def change_servo(servo, amount, amount=0.1):
        servo.ChangeDutyCycle(amount)
        time.sleep(amount)
        servo.ChangeDutyCycle(0)
