import time
import io
from typing import Tuple

import cv2
import threading

from picamera2 import Picamera2


class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """

    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = threading.get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[threading.get_ident()][0].clear()


class Camera:

    rotation_dict = {
        90: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        -90: cv2.ROTATE_90_COUNTERCLOCKWISE,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }

    thread = None  # background thread that reads frames from camera
    lores_frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera
    event = CameraEvent()
    semaphore = threading.Semaphore(1)
    pause = False
    timeout = 10
    # pause_path = "/home/pi/diesel_camera_server/StreamPaused.png"
    # pause_frame = open(pause_path, "rb").read()

    res: Tuple[int, int] = (2592, 1944)
    lowres: Tuple[int, int] = (1280, 720)

    def __init__(self, rotation_angle=90):
        self.camera = Picamera2()
        self.capture_config = self.camera.create_still_configuration(
            main={"size": self.res, "format": "YUV420"},
            lores={"size": self.lowres, "format": "YUV420"},
        )
        if rotation_angle in Camera.rotation_dict.keys():
            print(f"Rotating by {rotation_angle}", flush=True)
            self.rotate = True
            self.rotation_angle = rotation_angle
            self.cv_rotation = Camera.rotation_dict[rotation_angle]
        elif rotation_angle == 0:
            print("No rotation", flush=True)
            self.rotate = False
            self.rotation_angle = rotation_angle
            self.cv_rotation = None
        else:
            print("Illegal Rotation Angle, setting rotation to 90", flush=True)
            self.rotate = True
            self.rotation_angle = 90
            self.cv_rotation = Camera.rotation_dict[90]

    def get_lores_stream_frame(self) -> cv2.UMat:
        """Return the current camera frame."""
        if Camera.thread is None:

            # start background frame thread
            Camera.thread = threading.Thread(target=self._thread)
            Camera.thread.start()

        Camera.last_access = time.time()

        # wait for a signal from the camera thread
        Camera.event.wait()
        Camera.event.clear()

        return Camera.lores_frame

    def _thread(self):
        self.camera.configure(self.capture_config)
        self.camera.start()
        while True:
            if Camera.pause:
                Camera.lores_frame = Camera.pause_frame
                Camera.event.set()
                time.sleep(0.1)
            else:
                Camera.semaphore.acquire()
                yuv420 = self.camera.capture_array("lores")
                Camera.semaphore.release()
                rgb = cv2.cvtColor(yuv420, cv2.COLOR_YUV420p2RGB)
                if self.rotate:
                    rgb = cv2.rotate(rgb, self.cv_rotation)

                Camera.lores_frame = rgb
                Camera.event.set()
                time.sleep(0)

            if 0 < Camera.timeout < time.time() - Camera.last_access:
                self.camera.stop()
                print("Stopping camera thread due to inactivity.", flush=True)
                break
        Camera.thread = None

    def read_image(self) -> cv2.UMat:
        if Camera.thread is None:
            self.camera.configure(self.capture_config)
            self.camera.start()

        Camera.semaphore.acquire()
        yuv420 = self.camera.capture_array("main")
        Camera.semaphore.release()
        rgb = cv2.cvtColor(yuv420, cv2.COLOR_YUV420p2RGB)
        if self.rotate:
            rgb = cv2.rotate(rgb, self.cv_rotation)

        return rgb

        # image = camera.capture_image("lores")
        # image = image.rotate(self.rotation_angle,expand = True)
        # img_io = io.BytesIO()
        # image.save(img_io, 'JPEG', quality=95)
        # img_io.seek(0)

    def pause_stream(self):
        Camera.pause = True
        return Camera.pause

    def resume_stream(self):
        Camera.pause = False
        return not Camera.pause

    def is_paused(self):
        return Camera.pause

    def set_stream_timeout(self,timeout):
        try:
            timeout = abs(float(timeout))
            Camera.timeout = timeout
            return True
        except Exception as e:
            print('Failed to set stream timeout: {}'.format(e),flush = True)
            return False

    def release(self):
        self.camera.stop()
        Camera.thread = None
