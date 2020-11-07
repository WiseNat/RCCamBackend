import time
import io
import threading
import picamera


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

    def get_current_frame(self):
        self.camera.resolution = (1920, 1080)
        self.camera.capture("test.png")
        self.camera.resolution = (320, 240)

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
