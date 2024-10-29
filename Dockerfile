# Use an official Python runtime as a base image
FROM python:3.8

# Set the working directory
WORKDIR /app

# Copy the project files to the container
COPY . /app

# Install system dependencies for Tesseract and OpenCV (if needed)
RUN apt-get update && \
    apt-get install -y tesseract-ocr libgl1-mesa-glx && \
    apt-get clean

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables (replace with secure values if necessary)
ENV OPENAI_API_KEY="your_openai_api_key" \
    GOOGLE_API_KEY="your_google_api_key" \
    GOOGLE_CSE_ID="your_google_cse_id"

# Command to run the main script (replace with your main script's name if different)
CMD ["python", "main.py"]
