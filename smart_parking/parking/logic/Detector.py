import cv2
import numpy as np
from skimage.transform import resize

class Detector:
    def __init__(self):
        self.empty = True
        self.occupied = False

    def predict_empty_or_not(self):
        pass  

    def get_parking_spot(self, connected_components):
        (total_numbers, label_id, values, position) = connected_components
        slots = []  

        for i in range(1, total_numbers):
            x1 = int(values[i, cv2.CC_STAT_LEFT])  
            y1 = int(values[i, cv2.CC_STAT_TOP])  
            w = int(values[i, cv2.CC_STAT_WIDTH])  
            h = int(values[i, cv2.CC_STAT_HEIGHT])  

            slots.append([x1, y1, w, h])  

        return slots
    

