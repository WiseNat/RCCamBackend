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
    servo_min = 2
    servo_max = 12

    # Servo pitch modification logic
    if "p" in arg_keys and re.match(r"^-?\d+(?:\.\d+)?$", request.args["p"]) is not None:
        val = float(request.args["p"])
        if val < servo_min:
            print("Pitch value '{0}' exceeded range ({min} -> {max})\nPitch value set to {min}"
                  .format(val, min=servo_min, max=servo_max))
            val = servo_min
        elif val > servo_max:
            print("Pitch value '{0}' exceeded range ({min} -> {max})\nPitch value set to {max}"
                  .format(val, min=servo_min, max=servo_max))
            val = servo_max

        ser_app.change_servo(ser_app.pitch, val)
        print("Pitch: {}".format(val))

    # Servo yaw modification logic
    if "y" in arg_keys and re.match(r"^-?\d+(?:\.\d+)?$", request.args["y"]) is not None:
        val = float(request.args["y"])
        if val < servo_min:
            print("Yaw value '{0}' exceeded range ({min} -> {max})\nYaw value set to {min}"
                  .format(val, min=servo_min, max=servo_max))
            val = servo_min
        elif val > servo_max:
            print("Yaw value '{0}' exceeded range ({min} -> {max})\nYaw value set to {max}"
                  .format(val, min=servo_min, max=servo_max))
            val = servo_max

        ser_app.change_servo(ser_app.yaw, val)
        print("Yaw: {}".format(val))

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
