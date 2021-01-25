import os
import re
import time

from PIL import Image
from flask import Flask, send_from_directory, url_for, redirect, render_template, Response
from flask import request

from camera import Camera, gen_filename
from servo import ServoController

# GET ~ GET message is send, and the server returns data
# POST ~ Used to send HTML form data to the server. The data received by the POST method is not cached by the server.

web_app = Flask(__name__)

ser_app = ServoController()
camera = Camera()


def generator(cam):
    while True:
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + cam.get_frame() + b"\r\n"


def is_number(num):
    """
    Determines whether a given input is a number or not. Valid for num∈ℚ

    :param num: string, int, float
    :return: true if the given value is a number, false if not.
    """
    return True if type(num) in [int, float] or re.match(r"^-?\d+(?:\.\d*)?$", num) is not None else False


@web_app.route("/")
def main_page():
    return render_template("base.html")


@web_app.route("/video")
def video_feed():
    return Response(generator(camera), mimetype="multipart/x-mixed-replace; boundary=frame")


@web_app.route("/servo", methods=["POST", "GET"])
def servo():
    # Acceptable value range for servos
    smin = 0.0
    smax = 10.0

    # Servo pitch modification logic
    for char, servo_name, ref in (("p", "Pitch", ser_app.pitch), ("y", "Yaw", ser_app.yaw)):
        val = request.values.get(char, "")
        if val != "" and is_number(val):
            val = float(val)
            if val < smin:
                print(f"{servo_name} value '{val}' exceeded range ({smin} -> {smax})\n{servo_name} value set to {smin}")
                val = smin
            elif val > smax:
                print(f"{servo_name} value '{val}' exceeded range ({smin} -> {smax})\n{servo_name} value set to {smax}")
                val = smax

            ser_app.change_servo(ref, val + 2)
            print(f"{servo_name} rotation set to {val}")

    return redirect(url_for("main_page"))


@web_app.route("/take_photo/")
def take_photo():
    # Get args and declare if missing
    dur = request.args.get("dur", "")
    resWidth = request.args.get("w", "")
    resHeight = request.args.get("h", "")

    if (resHeight != "" or resWidth != "") and is_number(resWidth) and is_number(resHeight):
        res = [int(resWidth), int(resHeight)]
    else:
        res = [1920, 1080]

    if dur != "" and is_number(dur) and float(dur) > 0:
        time.sleep(float(dur))

    image_paths = ("photos/", "compressed_photos/")

    # Make image paths if they don't exist
    for path in image_paths:
        if not os.path.exists(path):
            os.mkdir(path)

    # Capture image as PNG
    image_name, image_ext = camera.capture_image(path=image_paths[0], res=res)

    # Convert and save image as JPEG
    im = Image.open(f"{image_paths[0]}{image_name}.{image_ext}").convert("RGB")
    image_ext = "jpeg"
    jpeg_name = f"{gen_filename(image_ext, image_paths[1])}.{image_ext}"
    im.save(f"{image_paths[1]}{jpeg_name}")  # JPEG

    return send_from_directory(image_paths[1], jpeg_name, as_attachment=True)


@web_app.route("/get_photo/<path:filename>")
def get_photo(filename):
    return send_from_directory("compressed_photos/", filename, as_attachment=True)


if __name__ == "__main__":
    web_app.run("0.0.0.0", threaded=True)
