from flask import Flask, Response
from flask import request

import re

from camera import Camera
from servo import ServoController

web_app = Flask(__name__)
ser_app = ServoController()


def generator(cam):
    while True:
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + cam.get_frame() + b"\r\n")


@web_app.route("/")
def main_page():
    # Servo modification logic
    arg_keys = [item.lower() for item in list(request.args.keys())]

    if "p" in arg_keys and re.match(r"^-?\d+(?:\.\d+)?$", request.args["p"]) is not None:
        ser_app.change_servo(ser_app.pitch, float(request.args["p"]))
        print("Pitch: {}".format(request.args["p"]))

    if "y" in arg_keys and re.match(r"^-?\d+(?:\.\d+)?$", request.args["y"]) is not None:
        ser_app.change_servo(ser_app.yaw, float(request.args["y"]))
        print("Yaw: {}".format(request.args["y"]))

    # Live video feed
    return Response(generator(Camera()), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    web_app.run("0.0.0.0", threaded=True)
