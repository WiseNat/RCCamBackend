import RPi.GPIO as GPIO
import time


class Servo(GPIO.PWM):
    def __init__(self, pin, hz):
        GPIO.setup(pin, GPIO.OUT)
        super().__init__(pin, hz)
        super().start(0)

        self.current = 0


class ServoController:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)

        # GPIO 12 initialisation, 50hz
        self.yaw = Servo(pin=12, hz=50)

        # GPIO 11 initialisation, 50hz
        self.pitch = Servo(pin=11, hz=50)

    @staticmethod
    def change_servo(servo, amount, tm=0.3):
        if servo.current != amount:
            servo.ChangeDutyCycle(amount)
            servo.current = amount

            time.sleep(tm)
            servo.ChangeDutyCycle(0)
