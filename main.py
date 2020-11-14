import io
import os

from PIL import Image
from flask import Flask, Response, send_file, send_from_directory, url_for, redirect
from flask import request

import re

from camera import Camera
from servo import ServoController

# GET ~ GET message is send, and the server returns data
# POST ~ Used to send HTML form data to the server. The data received by the POST method is not cached by the server.

web_app = Flask(__name__)
ser_app = ServoController()

camera = Camera()


def generator(cam):
    while True:
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + cam.get_frame() + b"\r\n"


@web_app.route("/")
def main_page():
    return Response(generator(camera), mimetype="multipart/x-mixed-replace; boundary=frame")


@web_app.route("/servo")
def servo():
    arg_keys = [item.lower() for item in list(request.args.keys())]

    # Servo pitch modification logic
    if "p" in arg_keys and re.match(r"^-?\d+(?:\.\d+)?$", request.args["p"]) is not None:
        ser_app.change_servo(ser_app.pitch, float(request.args["p"]))
        print("Pitch: {}".format(request.args["p"]))

    # Servo yaw modification logic
    if "y" in arg_keys and re.match(r"^-?\d+(?:\.\d+)?$", request.args["y"]) is not None:
        ser_app.change_servo(ser_app.yaw, float(request.args["y"]))
        print("Yaw: {}".format(request.args["y"]))

    return redirect(url_for("main_page"))


@web_app.route("/photo")
def photo():
    image_paths = ["photos/", "compressed_photos/"]

    for path in image_paths:
        if not os.path.exists(path):
            os.mkdir(path)

    image_name, image_ext = camera.capture_image(path=image_paths[0])  # PNG
    im = Image.open(f"{image_paths[0]}{image_name}.{image_ext}").convert("RGB")

    jpeg_name = f"{image_name}.jpeg"
    im.save(f"{image_paths[1]}{jpeg_name}")  # JPEG

    return send_from_directory(image_paths[1], jpeg_name)
    # header = b"--frame\r\nContent-Type: image/png\r\n\r\n" + camera.get_current_frame() + b"\r\n"
    # return Response(header, mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    web_app.run("0.0.0.0", threaded=True)
