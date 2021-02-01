import os
import time

from camera import Camera, gen_filename
from servo import ServoController

servo = ServoController()
camera = Camera()

ext = "jpeg"
res = [1920, 1080]

servo.change_servo(servo.yaw, 6)
time.sleep(0.5)

for path, s in zip(("panorama/pitch/", "panorama/yaw/"), (servo.pitch, servo.yaw)):

    if not os.path.exists(path):
        os.makedirs(path)

    for i in range(0, 105, 5):
        servo.change_servo(s, 2 + i/10)
        print(f"Changed servo to: {i/10}")
        time.sleep(1)
        camera.capture_image(filename=f"{path}{gen_filename(ext, path=path)}.{ext}", res=res)
        time.sleep(0.5)

    servo.change_servo(servo.pitch, 6)
    time.sleep(0.5)
