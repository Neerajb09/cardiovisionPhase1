import cv2
import numpy as np

class ImageProcessor:
    def __init__(self, image_path = "output_image.png", output_path= "output_image.png"):
        self.crop_center_contour(image_path, output_path)
        self.cropped_image=None
    def crop_center_contour(self, image_path, output_path):
        # Load the image
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Use edge detection to detect the central region
        edges = cv2.Canny(gray, 50, 150)

        # Find contours in the edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        largestContour = None
        maxArea = float("-inf")
        for contour in contours:
            # Calculate the bounding box of the contour
            x, y, w, h = cv2.boundingRect(contour)
            # Calculate the distance of the contour's center to the image center
        
            area = w*h
            if area > maxArea:
                maxArea = area
                largestContour = contour

        # Get the bounding box of the closest contour
        x, y, w, h = cv2.boundingRect(largestContour)

        # Crop the central square region
        cropped_image = image[y:y+h, x:x+w]

        # Save the cropped image
        cv2.imwrite(output_path, cropped_image)

# Example usage
# image_processor = ImageProcessor()
