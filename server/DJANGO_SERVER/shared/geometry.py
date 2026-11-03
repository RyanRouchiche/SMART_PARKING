import cv2
import numpy as np

SPOT_SIZE = 180
SPOT_SQUARE = np.float32([[0, 0], [SPOT_SIZE, 0], [SPOT_SIZE, SPOT_SIZE], [0, SPOT_SIZE]])


def order_corners(points):
    pts = np.asarray(points, dtype="float32")
    rect = np.zeros((4, 2), dtype="float32")
    total = pts.sum(axis=1)
    rect[0] = pts[np.argmin(total)]
    rect[2] = pts[np.argmax(total)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def crop_size(rect, frame_shape):
    width = max(int(np.linalg.norm(rect[0] - rect[1])), int(np.linalg.norm(rect[2] - rect[3])))
    height = max(int(np.linalg.norm(rect[0] - rect[3])), int(np.linalg.norm(rect[1] - rect[2])))
    return min(max(width, 1), frame_shape[1]), min(max(height, 1), frame_shape[0])


def crop_spot(frame, rect):
    width, height = crop_size(rect, frame.shape)
    target = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
    return cv2.warpPerspective(frame, cv2.getPerspectiveTransform(rect, target), (width, height))


def spot_transforms(spots):
    return {name: cv2.getPerspectiveTransform(np.float32(points), SPOT_SQUARE) for name, points in spots.items()}


def normalized_crops(frame, transforms):
    return [cv2.warpPerspective(frame, matrix, (SPOT_SIZE, SPOT_SIZE)) for matrix in transforms.values()]
