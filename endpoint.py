from flask import Flask, request, jsonify
import time
# from io import BytesIO
from valueExtraction import PDFExtractor # for extracting the values from the pdf 
from logics import ConditionEvaluator # for evaluating the the condition for generating the report
from ICD import PDFHighlighterAndCropper # crop the image label ICD and crop and highlight the area below it # not used in below code 
from valueFromImage import YellowShadeOCR 
from cloudinaryUpload import CloudinaryUploader
from calcificationImage import Calcification_image 
from fineTuneImage import ImageProcessor
import logging


app = Flask(__name__)

@app.route("/")
def home():
    return "Welcome to Flash Server !!!"


@app.route('/extract_pdf', methods=['POST'])
def extract_pdf():
    """
    API endpoint to extract values from a PDF URL.
    Expects a JSON payload with 'pdf_url'.
    """
	
    data = request.json
    if not data or 'pdf_url' not in data:
        return jsonify({"error": "Invalid request. 'pdf_url' is required."}), 400

    pdf_url = data['pdf_url']
    start_time = time.time()

    try:
        # Initialize the PDFExtractor with the given URL
        report_extractor = PDFExtractor(pdf_url=pdf_url)

        # report_extractor.extract_text_from_pdf()
        extracted_values = report_extractor.run_extraction()
        icd_values = {}

        if('bicuspid' in extracted_values["Aortic Valve Anatomy Type"].lower()):
            

            gg = PDFHighlighterAndCropper(pdf_url,  regex_patterns = [r'ICD @4mm', r'Inter commisural distance @4mm', r'ICD @ 4mm'])
            value = YellowShadeOCR()
            ImageProcessor()
            icd_values['icd4mmImg'] = CloudinaryUploader().file_url
            icd_values['icd4mm'] = value.numeric_value
            print("ICD@4mm:",value.numeric_value)

            gg = PDFHighlighterAndCropper(pdf_url,  regex_patterns = [r'ICD @6mm', r'Inter commisural distance @6mm', r'ICD @ 6mm'])
            value = YellowShadeOCR()
            ImageProcessor()
            print("ICD@6mm:",value.numeric_value)
            icd_values['icd6mmImg'] = CloudinaryUploader().file_url
            icd_values['icd6mm'] = value.numeric_value
            
            gg = PDFHighlighterAndCropper(pdf_url,  regex_patterns = [r'ICD @8mm', r'Inter commisural distance @8mm',r'ICD @ 8mm'])
            value = YellowShadeOCR()
            ImageProcessor()
            print("ICD@8mm:",value.numeric_value)
            icd_values['icd8mmImg'] = CloudinaryUploader().file_url
            icd_values['icd8mm'] = value.numeric_value
        Calcification_image(pdf_url,regex_patterns=[r'(?i)aortic valve calcification']).cropped_output
        ImageProcessor()
        icd_values['aorticValveCalcificationImage'] = CloudinaryUploader().file_url

        


        end_time = time.time()
        execution_time = end_time - start_time

        # print(extracted_values)
        # print(icd_values)
        # Return the extracted values as a JSON response
        return jsonify({
            "status": "success",
            "extracted_values": extracted_values,
            "icd_values": icd_values,
            "execution_time": f"{execution_time:.2f} seconds"
        })

    except Exception as e:
        # Handle errors
        return jsonify({"error": str(e)}), 500


@app.route('/fetch_report', methods=['POST'])
def fetch_report():
    data = request.json['report']
    print(data)
    evaluator = ConditionEvaluator(data)
    results_table = evaluator.generate_results_table()


    # Convert DataFrame to a list of dictionaries
    # results_json = results_table.to_dict(orient='records')
    print("1")
    # 
    print(results_table)  # Debug: Print the results JSON
    return jsonify({"results": results_table})

if __name__ == '__main__':
    # Run the Flask app on the desired port
    print(1)
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port=20201)
