import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from threading import Event, Thread
import os

class SumoDisplay(Thread):
    def __init__(self, receiver):
        Thread.__init__(self, name='SumoDisplay')
        self.receiver = receiver
        self.should_run = Event()
        self.should_run.set()
        self.window_name = 'Sumo Display'

        # Get the Yolo data, must download to the "data" folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        yolo_weights_path = os.path.join(current_dir, 'data', 'yolov3.weights')
        yolo_config_path = os.path.join(current_dir, 'data', 'yolov3.cfg')

        # Load YOLO
        self.net = cv2.dnn.readNet(yolo_weights_path, yolo_config_path)
        self.layer_names = self.net.getLayerNames()
        output_layers_indices = self.net.getUnconnectedOutLayers()
        if output_layers_indices.ndim == 1:
            # This is a 1-D numpy array of integers
            self.output_layers = [self.layer_names[i - 1] for i in output_layers_indices]
        else:
            # This is a 2-D numpy array of integers
            self.output_layers = [self.layer_names[i[0] - 1] for i in output_layers_indices]

    def run(self):
        while self.should_run.isSet():
            frame = self.receiver.get_frame()

            if frame is not None:
                byte_frame = BytesIO(frame)
                img = np.array(Image.open(byte_frame))

                height, width, channels = img.shape

                # Detecting objects
                blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
                self.net.setInput(blob)
                outs = self.net.forward(self.output_layers)

                # Showing informations on the screen
                class_ids = []
                confidences = []
                boxes = []
                for out in outs:
                    for detection in out:
                        scores = detection[5:]
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]
                        if confidence > 0.5:
                            # Object detected
                            center_x = int(detection[0] * width)
                            center_y = int(detection[1] * height)
                            w = int(detection[2] * width)
                            h = int(detection[3] * height)

                            # Rectangle coordinates
                            x = int(center_x - w / 2)
                            y = int(center_y - h / 2)

                            boxes.append([x, y, w, h])
                            confidences.append(float(confidence))
                            class_ids.append(class_id)

                indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
                for i in range(len(boxes)):
                    if i in indexes:
                        x, y, w, h = boxes[i]
                        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

                cv2.imshow(self.window_name, img)

            cv2.waitKey(25)

    def disconnect(self):
        self.should_run.clear()
        cv2.destroyWindow(self.window_name)