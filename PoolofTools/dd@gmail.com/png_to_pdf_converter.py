import sys
from PIL import Image

def convert_png_to_pdf(png_file_path, pdf_file_path):
    # Open the PNG file
    image = Image.open(png_file_path)
    # Convert to PDF
    image.convert('RGB').save(pdf_file_path, 'PDF')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python png_to_pdf_converter.py <input_png> <output_pdf>')
        sys.exit(1)
    convert_png_to_pdf(sys.argv[1], sys.argv[2])