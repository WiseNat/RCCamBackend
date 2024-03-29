import io
import os
import re
import time

import numpy as np
from PIL import Image, ImageFile
import cv2 as cv
from flask import Flask, send_from_directory, url_for, redirect, render_template, Response
from flask import request

from camera import Camera, gen_filename
from servo import ServoController

# GET ~ GET message is send, and the server returns data
# POST ~ Used to send HTML form data to the server. The data received by the POST method is not cached by the server.

web_app = Flask(__name__)

ser_app = ServoController()
camera = Camera()

ImageFile.LOAD_TRUNCATED_IMAGES = True


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
        val = request.values.get(char, "a")
        if is_number(val):
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
    image_ext = "png"
    image_location = f"{image_paths[0]}{gen_filename(image_ext, path=image_paths[0])}.{image_ext}"
    camera.capture_image(filename=image_location, res=res)

    # Convert and save image as JPEG
    im = Image.open(image_location).convert("RGB")
    image_ext = "jpeg"
    image_name = f"{gen_filename(image_ext, path=image_paths[1])}.{image_ext}"
    im.save(f"{image_paths[1]}{image_name}")  # JPEG
    print(f"Took photo: {image_paths[1]}{image_name}")

    return send_from_directory(image_paths[1], image_name, as_attachment=True)


@web_app.route("/get_photo/<path:filename>")
def get_photo(filename):
    return send_from_directory("compressed_photos/", filename, as_attachment=True)


@web_app.route("/face_detection", methods=["POST", "GET"])
def face_detection():
    # Width and Height
    resWidth = request.args.get("w", "")
    resHeight = request.args.get("h", "")

    if (resHeight != "" or resWidth != "") and is_number(resWidth) and is_number(resHeight):
        res = [int(resWidth), int(resHeight)]
    else:
        res = [1920, 1080]

    # Image stream capture and decode for OpenCV
    stream = io.BytesIO()
    camera.capture_image(stream, format="jpeg", res=res)
    data = np.frombuffer(stream.getvalue(), dtype=np.uint8)
    img = cv.imdecode(data, 1)

    # Image manipulation and saving
    img_grey = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    img_grey = cv.equalizeHist(img_grey)

    # Run face detection
    cascade = cv.CascadeClassifier("face_detect.xml")
    faces = cascade.detectMultiScale(img_grey,
                                     scaleFactor=1.05,
                                     minNeighbors=3,
                                     minSize=(70, 70),
                                     flags=cv.CASCADE_SCALE_IMAGE)

    # Apply bounding boxes
    for (x, y, w, h) in faces:
        cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

    # Calculating servo rotation
    height, width, channel = img.shape

    print(width, height)

    # Calculating average co-ord
    mid_coords = [(x + (w / 2), y + (h / 2)) for (x, y, w, h) in faces]

    if len(mid_coords) != 0:
        total = [sum(i) for i in zip(*mid_coords)]
        average = (round(total[0] / len(mid_coords)), round(height - total[1] / len(mid_coords)))
        print(f"Average: {average}")

        vals = [(10 * loc - 5 * dim) / arc for arc, loc, dim in zip((1920 * 3, 1080 * 3), average, (width, height))]

        yaw = round(ser_app.yaw.current + vals[0], 1)
        if yaw < 0:
            yaw = 0
        elif yaw > 10:
            yaw = 10
        ser_app.change_servo(ser_app.yaw, yaw)
        print(f"Yaw rotation set to {yaw}")

        pitch = round(ser_app.pitch.current - vals[1], 1)
        if pitch < 0:
            pitch = 0
        elif pitch > 10:
            pitch = 10
        ser_app.change_servo(ser_app.pitch, pitch)
        print(f"Pitch rotation set to {pitch}")

        # Write image with bounding box
        cv.imwrite("result.png", img)

    return redirect(url_for("main_page"))


@web_app.after_request
def add_header(response):
    response.cache_control.max_age = 0
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    response.cache_control.proxy_revalidate = True
    return response


if __name__ == "__main__":
    ser_app.change_servo(ser_app.pitch, 7)
    ser_app.change_servo(ser_app.yaw, 7)
    web_app.run("0.0.0.0", threaded=True)
