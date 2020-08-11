from io import BytesIO

import PIL
from PIL.Image import Image
from flask import Flask, Response
from flask import request

import time
import re

try:
    import RPi.GPIO as GPIO
    from picamera import PiCamera

    camera = PiCamera()
    camera.start_preview()
    isRPI = True
except ModuleNotFoundError:
    print("WARNING: RPI functions won't work on this environment")
    isRPI = False


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
    def change_servo(servo, amount, tm=0.1):
        servo.ChangeDutyCycle(amount)
        time.sleep(tm)
        servo.ChangeDutyCycle(0)


web_app = Flask(__name__)

if isRPI:
    ser_app = ServoController()


def gen(cam):
    stream = BytesIO()
    for image in cam.capture_continuous(stream, format="jpeg"):
        stream.seek(0)
        out_image = PIL.Image.open(image)
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + out_image.tobytes() + b"\r\n")


@web_app.route("/")
def landing_page():
    return "Nothing to see here"


# Better to work with structurally and functionally
@web_app.route("/servo/")
def modify_servo():
    arg_keys = [item.lower() for item in list(request.args.keys())]

    if "p" in arg_keys and re.match(r"^-?\d+(?:\.\d+)?$", request.args["p"]) is not None:
        ser_app.change_servo(ser_app.pitch, float(request.args["p"]))
        print("Pitch: {}".format(request.args["p"]))

    if "y" in arg_keys and re.match(r"^-?\d+(?:\.\d+)?$", request.args["y"]) is not None:
        ser_app.change_servo(ser_app.yaw, float(request.args["y"]))
        print("Yaw: {}".format(request.args["y"]))

    return "Time to update the servo"


@web_app.route("/video/")
def video_feed():
    return Response(gen(camera), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    web_app.run("0.0.0.0")
