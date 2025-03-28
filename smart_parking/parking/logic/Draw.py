# import cv2
# import json
# import numpy as np
# import os
# from skimage.transform import resize

# class Draw:
#     def __init__(self, floor, frame):
#         # init the drawing tool for a specific floor
#         self.floor = floor
#         self.points = []  # Stores the points selected by the user
#         self.coordinates = []  # Stores all the selected parking spots
#         self.frame = frame.copy()  # Copy of the frame for drawing

#         # creating directories for saving parking spots and masks
#         os.makedirs('Spots', exist_ok=True)
#         os.makedirs('Mask', exist_ok=True)

#         # filling path to store parking spot coordinates
#         self.filepath = f'Spots/coordinates_floor{self.floor}.json'
        
#         # loading existing coordinates if the file already exists
#         if os.path.exists(self.filepath):
#             with open(self.filepath, 'r') as f:
#                 self.coordinates = json.load(f)

#     def saveCoordinates(self):
#         """Save the selected parking spot coordinates to a JSON file."""
#         with open(self.filepath, 'w') as f:
#             json.dump(self.coordinates, f, indent=4)

#     def selectPoints(self, event, x, y, flags, param):
#         """Allows the user to select parking spot points using the mouse."""
#         if event == cv2.EVENT_LBUTTONDOWN:
#             # saving the selected point
#             self.points.append((x, y))
#             print(f'Point {len(self.points)} selected on floor {self.floor}: ({x}, {y})')

#             # drawsng a small red dot at the selected point
#             cv2.circle(self.frame, (x, y), 2, (0, 0, 255), -1)

#             # labeling the spot with a number
#             cv2.putText(self.frame, f"Spot {len(self.coordinates) + 1}", (x+5, y-5),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

#             # If 4 points are selected, define a parking spot
#             if len(self.points) == 4:
#                 # Draw a green polygon connecting the points
#                 cv2.polylines(self.frame, [np.array(self.points)], isClosed=True, color=(0, 255, 0), thickness=2)

#                 # stroing the spot with its coordinates
#                 spot_name = f"Spot {len(self.coordinates) + 1}"
#                 self.coordinates.append({spot_name: self.points.copy()})

#                 print(f"{spot_name} saved with points: {self.points}")

#                 # saving the coordinates to file
#                 self.saveCoordinates()
#                 self.points.clear()  # Clear points for the next selection

#                 # updating the displayed frame
#                 cv2.imshow(f"Floor {self.floor} - Detection", self.frame)

#     def get_points(self):
#         """Activates interactive mode for selecting parking spot points."""
#         cv2.imshow(f"Floor {self.floor} - Detection", self.frame)
#         cv2.setMouseCallback(f"Floor {self.floor} - Detection", self.selectPoints)

#         # keping the window open until the user presses 'q'
#         while True:
#             key = cv2.waitKey(1) & 0xFF
#             if key == ord('q'):
#                 break

#         cv2.destroyAllWindows()
#         return self.coordinates
    
#     """ila icharine lahik w nhcufo kifeche"""

#     # def drawMask(self):
#     #     """Generates a binary mask from the saved parking spot coordinates."""
#     #     height, width = self.frame.shape[:2]
#     #     mask = np.zeros((height, width), dtype=np.uint8)  # creating an empty black mask

#     #     # loading the saved coordinates and fill the mask
#     #     if os.path.exists(self.filepath):
#     #         with open(self.filepath, 'r') as f:
#     #             spots = json.load(f)

#     #         for spot in spots:
#     #             for _, points in spot.items():
#     #                 pts = np.array(points, dtype=np.int32)
#     #                 cv2.fillPoly(mask, [pts], 255)  # filling the parking spots in white

#     #     return mask

#     # def saveMask(self, mask):
#     #     """Saves the generated mask as a png image."""
#     #     mask_path = f"Mask/mask_floor{self.floor}.png"
#     #     cv2.imwrite(mask_path, mask)
#     #     print(f"Mask saved: {mask_path}")



import cv2
import json
import numpy as np
import os

class Draw:
    def __init__(self, floor, frame):
        # Initialize the drawing tool for a specific floor
        self.floor = str(floor)  # Ensure the floor is a string
        self.points = []  # Stores the points selected by the user
        self.coordinates = {}  # Stores all the selected parking spots for this floor
        self.frame = frame.copy()  # Copy of the frame for drawing

        # Create directories for saving parking spots and masks
        os.makedirs('Spots', exist_ok=True)
        os.makedirs('Mask', exist_ok=True)

        # Path to the unified JSON file
        self.filepath = 'Spots/coordinates.json'

        # Load existing coordinates if the file already exists
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                # Extract coordinates for the current floor
                for floor_data in data:
                    if floor_data["floor"] == self.floor:
                        self.coordinates = floor_data["coordinates"]
                        break

    def saveCoordinates(self):
        """Save the selected parking spot coordinates to a unified JSON file."""
        # Load existing data from the JSON file
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                data = json.load(f)
        else:
            data = []

        # Update or add the current floor's data
        floor_found = False
        for floor_data in data:
            if floor_data["floor"] == self.floor:
                floor_data["coordinates"] = self.coordinates
                floor_found = True
                break

        if not floor_found:
            data.append({
                "floor": self.floor,
                "coordinates": self.coordinates
            })

        # Save the updated data back to the JSON file
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=4)

    def selectPoints(self, event, x, y, flags, param):
        """Allows the user to select parking spot points using the mouse."""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Save the selected point
            self.points.append((x, y))
            print(f'Point {len(self.points)} selected on floor {self.floor}: ({x}, {y})')

            # Draw a small red dot at the selected point
            cv2.circle(self.frame, (x, y), 2, (0, 0, 255), -1)

            # Label the spot with a number
            cv2.putText(self.frame, f"Spot {len(self.coordinates) + 1}", (x + 5, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # If 4 points are selected, define a parking spot
            if len(self.points) == 4:
                # Draw a green polygon connecting the points
                cv2.polylines(self.frame, [np.array(self.points)], isClosed=True, color=(0, 255, 0), thickness=2)

                # Store the spot with its coordinates
                spot_name = f"Spot {len(self.coordinates) + 1}"
                self.coordinates[spot_name] = self.points.copy()

                print(f"{spot_name} saved with points: {self.points}")

                # Save the coordinates to the unified JSON file
                self.saveCoordinates()
                self.points.clear()  # Clear points for the next selection

                # Update the displayed frame
                cv2.imshow(f"Floor {self.floor} - Detection", self.frame)

    def get_points(self):
        """Activates interactive mode for selecting parking spot points."""
        cv2.imshow(f"Floor {self.floor} - Detection", self.frame)
        cv2.setMouseCallback(f"Floor {self.floor} - Detection", self.selectPoints)

        # Keep the window open until the user presses 'q'
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        cv2.destroyAllWindows()
        return self.coordinates