import time
import tempfile
import os
import numpy as np
import pandas as pd
import pdfplumber
import re
from pdf2image import convert_from_path, convert_from_bytes
from PIL import ImageEnhance, ImageFilter
import fitz
import requests
from io import BytesIO
import cloudinary.uploader
from calciumValue import desired_image

class PDFExtractor:
    def __init__(self, pdf_path=None, pdf_url=None):
        self.pdf_path = pdf_path
        self.pdf_url = pdf_url
        self.extracted_text = ""
        self.values = {
            "url": None,
            "STJ Diameter": None,
            "Annulus Diameter": None,
            "Annulus Area": None,
            "Annulus Perimeter": None,
            "Annulus Perimeter Derived Diameter": None,
            "LVOT Diameter": None,
            "Asc Aorta Diameter": None,
            "RCA Height": None,
            "LCA Height": None,
            "SOV Height": None,
            "SOV Left Diameter": None,
            "SOV Right Diameter": None,
            "SOV Non Diameter": None,
            "Aortic Valve Anatomy Type": None,
            "Calcium Score": None,
        }
        self.patterns = {
            "STJ Diameter": r"STJ\s*Ø:\s*([\d.]+)\s*mm",
            "Annulus Diameter": r"Area\s*Derived\s*Ø:\s*([\d.]+)\s*mm",
            "Annulus Area": r"Area:\s*([\d.]+)\s*mm²",
            "Annulus Perimeter": r"Perimeter:\s*([\d.]+)\s*mm",
            "Annulus Perimeter Derived Diameter": r"Perimeter\s*Derived\s*Ø:\s*([\d.]+)\s*mm",
            "LVOT Diameter": r"LVOT\s*Ø:\s*([\d.]+)\s*mm",
            "Asc Aorta Diameter": r"Asc.\s*Aorta\s*Ø:\s*([\d.]+)\s*mm",
            "RCA Height": r"RCA\s*Height\s*:\s*([\d.]+)\s*mm",
            "LCA Height": r"LCA\s*Height\s*:\s*([\d.]+)\s*mm",
            "SOV Height": r"Sinus\s*of\s*Valsalva\s*Height\s*([\d.]+)\s*mm",
            "SOV Left Diameter": r"Left\s*:\s*([\d.]+)\s*mm",
            "SOV Right Diameter": r"Right\s*:\s*([\d.]+)\s*mm",
            "SOV Non Diameter": r"Non\s*:\s*([\d.]+)\s*mm",
            "Aortic Valve Anatomy Type": r"([A-Za-z0-9\s]+(?:\s+[A-Za-z0-9]+)*)\s+Aortic\s+Valve",
            "Calcium Score": [r"Total\s*:\s*([\d.]+)", r"Total\s+\w*\s*:\s*([\d.]+)", r'Total\s*Calcium\s*[^0-9]*([\d,\.]+)',r'Total\s*[^0-9]*([\d,\.]+)'],
        }

    def fetch_pdf_content(self):
        """
        Fetch the PDF content from a URL or local file.
        """
        if self.pdf_url:
            response = requests.get(self.pdf_url)
            if response.status_code == 200:
                return BytesIO(response.content)
            else:
                raise ValueError(f"Failed to fetch PDF from URL: {self.pdf_url}")
        elif self.pdf_path:
            return self.pdf_path
        else:
            raise ValueError("Either 'pdf_path' or 'pdf_url' must be provided.")

    def extract_text(self, pdf_content):
        """
        Extract text from the PDF using pdfplumber for faster processing.
        """
        pdf_bytes = pdf_content.read() if self.pdf_url else None
        page_text = ""

        # Use pdfplumber to extract text directly from the PDF
        with pdfplumber.open(BytesIO(pdf_bytes)) if self.pdf_url else pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages[:2]:  # Process the first 2 pages for optimization
                page_text += page.extract_text() or ""

        self.extracted_text = page_text  # Store the extracted text
        return page_text

    def extract_calcium(self) :
        regex_patterns = [r'(?i)aortic valve calcification']
        
        processor = desired_image(
            pdf_url=self.pdf_url,
            regex_patterns=regex_patterns
        )
        print("Cropped Image URL:", processor.cropped_output)
        print("Extracted Text:", processor.extracted_text)
        print("Calcium Score:", processor.calcium_score)
        return processor.calcium_score

    
    @staticmethod
    def preprocess_image(image):
        """
        Enhance and preprocess the image for better OCR results.
        """
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)
        return image.convert("L").filter(ImageFilter.SHARPEN)
    
    def clean_extracted_text(self, match):
        cleaned_text = re.sub(r'[\n\r\x0c]+', ' ', match)
        cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)
        cleaned_text = re.sub(r'(Aortic\s+Valve).*', r'\1', cleaned_text)
        cleaned_text = re.split(r'aortic valve', cleaned_text, flags=re.IGNORECASE)[0]
        # print(cleaned_text)
        return cleaned_text.strip()

    def extract_values(self, text):
        """
        Extract key-value pairs from the extracted text using patterns.
        """
        for key, pattern in self.patterns.items():
            if key == "Calcium Score":
               self.values[key]=self.extract_calcium()
            else : 
                match = re.findall(pattern, text, re.IGNORECASE)
                if match:
                   if key == "Aortic Valve Anatomy Type":
                            if len(match) > 1:
                                x = match[1]
                                x = self.clean_extracted_text(x)
                                if x in ["Mild", "Moderate", "Severe"]:
                                    self.values[key] = self.clean_extracted_text(match[0])
                                else:
                                    x = self.clean_extracted_text(match[1])
                                    self.values[key] = x
                            else:
                                self.values[key] = self.clean_extracted_text(match[0])
                   else:
                    self.values[key] = match[0]


    def highlight_values_in_pdf(self, output_pdf_path):

        if self.pdf_url:
            pdf_content = self.fetch_pdf_content()
            temp_pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_pdf_file.write(pdf_content.read())
            temp_pdf_file.close()
            pdf_path = temp_pdf_file.name
        else:
            pdf_path = self.pdf_path
        # Define a color map for each key
        color_map = {
            "STJ Diameter": (206 / 255, 233 / 255, 239 / 255),  # #CEE9EF
            "Annulus Diameter": (195 / 255, 199 / 255, 233 / 255),  # #C3C7E9
            "LVOT Diameter": (182 / 255, 219 / 255, 231 / 255),  # #B6DBE7
            "RCA Height": (238 / 255, 185 / 255, 196 / 255),  # #EEB9C4
            "LCA Height": (236 / 255, 189 / 255, 181 / 255),  # #ECBDB5
            "SOV Left Diameter": (211 / 255, 229 / 255, 192 / 255),  # #D3E5C0
            "SOV Right Diameter": (180 / 255, 228 / 255, 199 / 255),  # #B4E4C7
            "SOV Non Diameter": (195 / 255, 242 / 255, 219 / 255),  # #C3F2DB
            "Asc Aorta Diameter": (240 / 255, 230 / 255, 140 / 255),  # Light Goldenrod
            "Aortic Valve Anatomy Type": (243 / 255, 247 / 255, 238 / 255),  # #F3F7EE
        }

        # Open the original PDF
        doc = fitz.open(pdf_path)

        # Iterate through each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")  # Extract the full text from the page
            # print(page_text)
            # For each key in pattern dictionary, search for the corresponding value or pattern
            for key, value in self.values.items():
                if key != "Calcium Score":
                    if value is not None:
                        # Prepare the value to find (adding ' mm' for Diameter and Height)
                        value_to_find = f"{value} mm" if "Diameter" in key or "Height" in key else str(value)
                        
                        # Search for the value text in the page
                        text_instances = page.search_for(value_to_find)
                        
                        # Check if the pattern exists for this key
                        pattern = self.patterns.get(key)
                        if pattern:
                            # Search for pattern matches in the page text
                            pattern_instances = list(re.finditer(pattern, page_text))

                            # Iterate through all pattern matches and check if the value is part of the same line
                            for match in pattern_instances:
                                matched_text = match.group()

                                # If the matched text contains the value (both pattern and value match), highlight the line
                                if value_to_find in matched_text:
                                    pattern_instances_coords = page.search_for(matched_text)

                                    # Highlight the coordinates where both value and pattern match
                                    for inst in pattern_instances_coords:
                                        # Use the color from the color map
                                        highlight_color = color_map.get(key, (1, 1, 1))  # Default to white if key not in map
                                        highlight = page.add_highlight_annot(inst)
                                        highlight.set_colors(stroke=highlight_color)
                                        highlight.update()

        # Save the output PDF with highlights
        doc.save(output_pdf_path)
        doc.close()
        # self.values['url']= self.upload_to_cloudinary(output_pdf_path)

    def upload_to_cloudinary(self, file_path):
        """
        Upload the file to Cloudinary and return the file URL.
        """
        cloudinary.config(
            cloud_name='ddiv6zknz',
            api_key='583371225574577',
            api_secret='noZQfCIf3fvBaV-fEAa0PSqolt4'
        )
        try:
            response = cloudinary.uploader.upload(file_path, resource_type='raw',format = 'N/A')
            return response.get('url')
        except Exception as e:
            # print(f"Error uploading to Cloudinary: {e}")
            return None

    def run_extraction(self, output_pdf_path="highlighted_output.pdf"):
        pdf_content = self.fetch_pdf_content()
        page_text = self.extract_text(pdf_content)
        self.extract_values(page_text)
        self.highlight_values_in_pdf(output_pdf_path)
        self.values["url"] = self.upload_to_cloudinary(output_pdf_path)
        return self.values
    
    def get_extracted_values(self):
        return self.values

# if __name__ == "__main__":
#     folder_path = "/home/neeraj/reports"
#     output_csv_path = "/home/neeraj/processed_results.csv"  # Path for the CSV file
#     start_time = time.time()

#     # List all PDF files in the folder
#     pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

#     # Initialize a list to collect all results
#     all_results = []

#     # Process each PDF file
#     for pdf_file in pdf_files:
#         pdf_path = os.path.join(folder_path, pdf_file)
#         try:
#             print(f"Processing {pdf_file}...")

#             # Initialize the extractor
#             extractor = PDFExtractor(pdf_path=pdf_path)
#             results = extractor.run_extraction()

#             # Add the filename to results
#             results["Filename"] = pdf_file
#             all_results.append(results)

#             print(f"Processed {pdf_file}.")
#         except Exception as e:
#             print(f"Error occurred while processing {pdf_file}: {e}")

#     # Create a DataFrame and save it to CSV
#     if all_results:
#         df = pd.DataFrame(all_results)
#         df.to_csv(output_csv_path, index=False)
#         print(f"Results saved to {output_csv_path}")

#     print(f"Execution Time: {time.time() - start_time:.2f} seconds")


# pdf_url = "https://res.cloudinary.com/dkaa6ubzd/raw/upload/v1737449491/yabnbdw5cux5brkjd6zw"
# # pdf_path = "/home/neeraj/Bicuspid.pdf"
# start_time = time.time()
# # report_extractor = PDFExtractor(pdf_path=pdf_path)
# report_extractor = PDFExtractor(pdf_url=pdf_url)
# # report_extractor.extract_text_from_pdf()
# extracted_values = report_extractor.run_extraction()
# output_pdf_path = "output_highlighted_t.pdf"
# report_extractor.highlight_values_in_pdf(output_pdf_path)

# for key, value in extracted_values.items():
#    print(f"{key}: {value} mm" if "Diameter" in key or "Height" in key else f"{key}: {value}")
