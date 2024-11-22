from flask import Flask, request, send_file
import os
from png_to_pdf_converter import convert_png_to_pdf

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('PoolOfTools/dd@gmail.com/png_to_pdf_converter_ui.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file and file.filename.endswith('.png'):
        input_path = os.path.join('PoolOfTools/dd@gmail.com', file.filename)
        output_path = os.path.join('PoolOfTools/dd@gmail.com', 'converted.pdf')
        file.save(input_path)
        convert_png_to_pdf(input_path, output_path)
        return send_file(output_path, as_attachment=True)
    return 'Invalid file type', 400

if __name__ == '__main__':
    app.run(debug=True)