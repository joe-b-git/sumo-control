import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from threading import Event, Thread
import os
import time
from threading import Lock

class SumoDisplay(Thread):
    def __init__(self, receiver):
        Thread.__init__(self, name='SumoDisplay')
        self.receiver = receiver
        self.should_run = Event()
        self.should_run.set()
        self.window_name = 'Sumo Display'

        # Get the Yolo data, must download to the "data" folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if (cv2.cuda.getCudaEnabledDeviceCount() > 0):
            yolo_weights_path = os.path.join(current_dir, 'data', 'yolov4.weights')
            yolo_config_path = os.path.join(current_dir, 'data', 'yolov4.cfg')
        else:
            yolo_weights_path = os.path.join(current_dir, 'data', 'yolov4-tiny.weights')
            yolo_config_path = os.path.join(current_dir, 'data', 'yolov4-tiny.cfg')

        self.lock = Lock()  # Create a lock

        # Load YOLO
        self.net = cv2.dnn.readNet(yolo_weights_path, yolo_config_path)
        if (cv2.cuda.getCudaEnabledDeviceCount() > 0):
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
        self.layer_names = self.net.getLayerNames()
        output_layers_indices = self.net.getUnconnectedOutLayers()
        if output_layers_indices.ndim == 1:
            # This is a 1-D numpy array of integers
            self.output_layers = [self.layer_names[i - 1] for i in output_layers_indices]
        else:
            # This is a 2-D numpy array of integers
            self.output_layers = [self.layer_names[i[0] - 1] for i in output_layers_indices]

        self.frame_count = 0
        self.prev_detections = None

        self.person_detected = False
        self.person_position = None

    def run(self):
        prev_frame_time = 0
        while self.should_run.isSet():
            frame = self.receiver.get_frame()

            if frame is not None:
                # Calculate FPS
                new_frame_time = time.time()
                fps = 1 / (new_frame_time - prev_frame_time)
                prev_frame_time = new_frame_time
                fps_text = f'FPS: {fps:.2f}'

                byte_frame = BytesIO(frame)
                img = np.array(Image.open(byte_frame))
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                height, width, channels = img.shape

                # Detecting objects
                if self.frame_count % 2 == 0 or True:  # Run detection on every 5th frame
                    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
                    self.net.setInput(blob)
                    outs = self.net.forward(self.output_layers)
                    self.prev_detections = outs
                else:
                    outs = self.prev_detections

                with self.lock:  # Use the lock when modifying shared data
                    # Reset instance variables
                    self.person_detected = False
                    self.person_position = None

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

                    closest_person_distance = float('inf')

                    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

                    for i in range(len(boxes)):
                        if i in indexes:
                            # If a person is detected
                            if class_ids[i] == 0:  # Assuming the class ID for 'person' is 0
                                x, y, w, h = boxes[i]
                                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), 2)

                                self.person_detected = True

                                # Calculate the bottom center of the bounding box
                                bottom_center_x = x + w / 2
                                bottom_center_y = y + h

                                # Check if this person is more centered than the previous ones
                                distance_to_center = abs(width / 2 - bottom_center_x)
                                if distance_to_center < closest_person_distance:
                                    closest_person_distance = distance_to_center
                                    self.person_position = (bottom_center_x, bottom_center_y)

                # Draw FPS on the image
                cv2.putText(img, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                self.frame_count += 1

                cv2.imshow(self.window_name, img)

            cv2.waitKey(25)

    def disconnect(self):
        self.should_run.clear()
        cv2.destroyWindow(self.window_name)