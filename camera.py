import os
import time
import io
import threading
from datetime import datetime

import picamera


def gen_filename(ext, path=""):
    counter = 1
    date = datetime.today()
    filename = f"{date.day}-{date.month}-{date.year} #{counter}"

    while True:
        if os.path.isfile(f"{path}{filename}.{ext}"):  # Increment counter if filename already exists
            counter += 1
            filename = f"{date.day}-{date.month}-{date.year} #{counter}"
        else:  # Filename doesn't already exist, end loop
            break

    return filename


class Camera:
    thread = None  # Background thread that reads frames from camera
    frame = None  # Current frame is stored here by background thread
    last_access = 0  # Time of last client access to the camera

    camera = picamera.PiCamera()

    # camera.hflip = True
    # camera.vflip = True

    def initialise(self):
        if Camera.thread is None:
            # Start background frame thread
            Camera.thread = threading.Thread(target=self._thread)
            Camera.thread.start()

            # Wait until frames start to be available
            while self.frame is None:
                time.sleep(0)

    def get_frame(self):
        Camera.last_access = time.time()
        self.initialise()
        return self.frame

    def capture_image(self, path="", ext="png"):
        # Appending a / to the end of path if it is missing
        if path != "" and path[-1] != "/":
            path += "/"

        # Generating filename
        filename = gen_filename(ext, path=path)

        while True:
            try:
                # Changing to higher resolution for capturing image
                self.camera.resolution = (1920, 1440)
                self.camera.capture(f"{path}{filename}.{ext}")
                break
            except picamera.exc.PiCameraMMALError:
                pass

        while True:
            try:
                # Reverting to live stream resolution
                self.camera.resolution = (320, 240)
                break
            except picamera.exc.PiCameraMMALError:
                pass

        return filename, ext

    @classmethod
    def _thread(cls):
        # Giving time for the camera to warm up
        cls.camera.resolution = (320, 240)
        cls.camera.start_preview()
        time.sleep(2)

        stream = io.BytesIO()
        for foo in cls.camera.capture_continuous(stream, "jpeg", use_video_port=True):
            # Store current frame
            stream.seek(0)
            cls.frame = stream.read()

            # Reset stream for next frame
            stream.seek(0)
            stream.truncate()

            # Stop thread if no clients have asked for a stream for 10 seconds
            if time.time() - cls.last_access > 10:
                cls.camera.stop_preview()
                break
        cls.thread = None
