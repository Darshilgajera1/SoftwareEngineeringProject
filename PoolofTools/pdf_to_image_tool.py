import sys

from langchain.tools import tool

@tool('pdf_to_image', return_direct=False)
def pdf_to_image(pdf_path: str) -> str:
    """Converts a PDF file into images and saves them."""
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path)
        image_paths = []
        for i, image in enumerate(images):
            image_path = f'image_{i + 1}.png'
            image.save(image_path, 'PNG')
            image_paths.append(image_path)
        return f'Converted {len(images)} pages to images: {', '.join(image_paths)}'
    except:
        return 'Error: ' + str(sys.exc_info())