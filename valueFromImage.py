import cv2
import numpy as np
import easyocr
import re

class YellowShadeOCR:
    def __init__(self, input_image_path='output_image.png', processed_image_path='yellow_shades_image.png'):
        """
        Initializes the class and runs the yellow shade detection and OCR automatically.
        :param input_image_path: Path to the input image.
        :param processed_image_path: Path to save the yellow-shaded processed image.
        """
        self.input_image_path = input_image_path
        self.processed_image_path = processed_image_path
        self.numeric_value = None

        # Automatically process the image and extract the numeric value
        self.run()

    def rgba_to_hsv(self, rgba_colors):
        """
        Convert RGBA colors to HSV colors.
        :param rgba_colors: List of RGBA tuples.
        :return: List of HSV tuples.
        """
        hsv_colors = []
        for rgba in rgba_colors:
            r, g, b, _ = rgba
            rgb_color = np.uint8([[[r, g, b]]])
            hsv_color = cv2.cvtColor(rgb_color, cv2.COLOR_RGB2HSV)[0][0]
            hsv_colors.append(tuple(hsv_color))
        return hsv_colors

    def pick_yellow_shades(self):
        """
        Detect and isolate all shades of yellow in an image and smoothen edges.
        """
        # Load the image
        image = cv2.imread(self.input_image_path)
        if image is None:
            raise FileNotFoundError(f"Image not found at {self.input_image_path}")

        # Convert the image to HSV
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define HSV range for yellow shades
        lower_yellow = np.array([20, 50, 50])  # Lower bound of yellow
        upper_yellow = np.array([40, 255, 255])  # Upper bound of yellow

        # Create a mask for yellow shades
        mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)

        # Smoothen edges with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))  # Elliptical kernel
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # Close gaps
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # Remove noise

        # Optional: Apply Gaussian blur for smoother transitions
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        # Apply the mask to the original image
        yellow_only = cv2.bitwise_and(image, image, mask=mask)

        # Save the output image
        cv2.imwrite(self.processed_image_path, yellow_only)
        print(f"Image with yellow shades saved and smoothed at: {self.processed_image_path}")

    def apply_easyocr_extract_numeric(self):
        """
        Apply EasyOCR to extract text from an image and concatenate all numeric values.
        :return: Concatenated numeric values as a single string.
        """
        # Initialize the EasyOCR Reader
        reader = easyocr.Reader(['en'], gpu=True)

        # Perform OCR on the image
        # print(f"Running EasyOCR on {self.processed_image_path}...")
        results = reader.readtext(self.processed_image_path)

        # Extract and combine text
        extracted_text = " ".join([result[1] for result in results])

        # Retain only numeric values using regex and concatenate them
        numeric_values = "".join(re.findall(r'\d+', extracted_text))  # Concatenate all numeric characters
        numeric_values = int(numeric_values)

        # Reduce numeric value if greater than 99
        while int(numeric_values) > 99:
            numeric_values = int(numeric_values) / 10
            # print(numeric_values)

        self.numeric_value = str(numeric_values)

    def run(self):
        """
        Runs the entire process: yellow shade detection and OCR.
        """
        self.pick_yellow_shades()
        self.apply_easyocr_extract_numeric()

# # Usage Example
# if __name__ == "__main__":
#     input_image_path = "output_image.png"  # Path to your input image
#     processed_image_path = "yellow_shades_image.png"  # Path to save the yellow-shaded image

#     processor = YellowShadeOCR(input_image_path, processed_image_path)

#     # print("OCR Complete. Final Numeric Value:", processor.numeric_value)
