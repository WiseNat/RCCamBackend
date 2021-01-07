import os
import re
import time

from PIL import Image
from flask import Flask, send_from_directory, url_for, redirect, render_template, Response
from flask import request

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
    return render_template("base.html")


@web_app.route("/video")
def video_feed():
    return Response(generator(camera), mimetype="multipart/x-mixed-replace; boundary=frame")


@web_app.route("/servo")
def servo():
    arg_keys = [item.lower() for item in list(request.args.keys())]

    # Acceptable value range for servos
    smin = 2
    smax = 12

    # Servo pitch modification logic
    for char, servo_name, ref in (("p", "Pitch", ser_app.pitch), ("y", "Yaw", ser_app.yaw)):
        if char in arg_keys and re.match(r"^-?\d+(?:\.\d+)?$", request.args[char]) is not None:
            val = float(request.args[char])
            if val < smin:
                print(f"{servo_name} value '{val}' exceeded range ({smin} -> {smax})\n{servo_name} value set to {smin}")
                val = smin
            elif val > smax:
                print(f"{servo_name} value '{val}' exceeded range ({smin} -> {smax})\n{servo_name} value set to {smax}")
                val = smax

            ser_app.change_servo(ref, val)
            print(f"{servo_name} rotation set to {val}")

    return redirect(url_for("main_page"))


@web_app.route("/take_photo/", defaults={"dur": "0"})
@web_app.route("/take_photo/<string:dur>")
def take_photo(dur):
    dur = float(dur)
    image_paths = ["photos/", "compressed_photos/"]

    time.sleep(dur)

    for path in image_paths:
        if not os.path.exists(path):
            os.mkdir(path)

    image_name, image_ext = camera.capture_image(path=image_paths[0])  # PNG
    im = Image.open(f"{image_paths[0]}{image_name}.{image_ext}").convert("RGB")

    jpeg_name = f"{image_name}.jpeg"
    im.save(f"{image_paths[1]}{jpeg_name}")  # JPEG

    return send_from_directory(image_paths[1], jpeg_name, as_attachment=True)


@web_app.route("/get_photo/<path:filename>")
def get_photo(filename):
    return send_from_directory("compressed_photos/", filename, as_attachment=True)


if __name__ == "__main__":
    web_app.run("0.0.0.0", threaded=True)
