import cv2
import numpy as np
import os
from PIL import Image
from io import BytesIO
from threading import Event, Thread


class SumoDisplay(Thread):
    """
    Displays frames received from the Jumping Sumo
    """

    def __init__(self, receiver):
        Thread.__init__(self, name='SumoDisplay')
        # self.setDaemon(True)

        self.receiver = receiver
        self.should_run = Event()
        self.should_run.set()

        self.window_name = 'Sumo Display'
        # cv2.namedWindow('SumoDisplay')

    def run(self):
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the path to the Haar cascade files
        face_cascade_path = os.path.join(current_dir, 'data', 'haarcascade_frontalface_default.xml')
        fullbody_cascade_path = os.path.join(current_dir, 'data', 'haarcascade_fullbody.xml')
        upperbody_cascade_path = os.path.join(current_dir, 'data', 'haarcascade_upperbody.xml')

        # Load the Haar cascade xml files for face, full body, and upper body detection
        face_cascade = cv2.CascadeClassifier(face_cascade_path)
        fullbody_cascade = cv2.CascadeClassifier(fullbody_cascade_path)
        upperbody_cascade = cv2.CascadeClassifier(upperbody_cascade_path)

        while self.should_run.isSet():
            frame = self.receiver.get_frame()

            if frame is not None:
                byte_frame = BytesIO(frame)
                img = np.array(Image.open(byte_frame))

                # Convert the image to grayscale
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                # Detect faces, full bodies, and upper bodies
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                fullbodies = fullbody_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                upperbodies = upperbody_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                # Draw a yellow circle around each face
                for (x, y, w, h) in faces:
                    cv2.circle(img, (x + w//2, y + h//2), max(w, h)//2, (0, 255, 255), 2)

                # Draw an orange bounding box around each full body
                for (x, y, w, h) in fullbodies:
                    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 165, 255), 2)

                # Draw a green bounding box around each upper body
                for (x, y, w, h) in upperbodies:
                    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

                cv2.imshow(self.window_name, img)

            cv2.waitKey(25)

    def disconnect(self):
        """
        Stops the main loop and closes the display window
        """
        self.should_run.clear()
        cv2.destroyWindow(self.window_name)