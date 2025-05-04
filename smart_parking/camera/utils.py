import numpy as np
from .Camera import Camera




def calculate_width_height( rect) : 
        width_top = np.linalg.norm(rect[0] - rect[1]) 
        width_bottom = np.linalg.norm(rect[2] - rect[3])  
        width = max(int(width_top), int(width_bottom))

        height_left = np.linalg.norm(rect[0] - rect[3])  
        height_right = np.linalg.norm(rect[1] - rect[2]) 
        height = max(int(height_left), int(height_right))

        return width, height
    
def sort_parking_spot_points( pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)] 
        rect[2] = pts[np.argmax(s)]  
        
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]  
        rect[3] = pts[np.argmax(diff)] 

        return rect

async def initialize_cameras():
    active_cameras = await Camera.get_available_cameras()
    return {area: Camera(path, area=area) for area, path in active_cameras.items()}


from asgiref.sync import async_to_sync

def async_initialize_cameras():
    return async_to_sync(initialize_cameras)()

def convert_ndarray_to_list(data):
    if isinstance(data, dict):
        return {k: convert_ndarray_to_list(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_ndarray_to_list(i) for i in data]
    elif isinstance(data, np.ndarray):
        return data.tolist()
    return data