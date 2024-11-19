import sys

from langchain.tools import tool
from PIL import Image

@tool('image_to_pdf_converter', return_direct=False)
def image_to_pdf_converter(image_path: str, pdf_path: str) -> str:
    """Converts an image to a PDF file."""
    try:
        # Open the image file
        with Image.open(image_path) as img:
            # Convert the image to PDF
            img.save(pdf_path, 'PDF')
        return f'Successfully converted {image_path} to {pdf_path}'
    except Exception as e:
        return f'Error: {str(e)}'