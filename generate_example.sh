#!/bin/bash

# CV Generator Usage Example

# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Tesseract OCR (system dependency)
# Ubuntu/Debian:
# sudo apt-get install tesseract-ocr

# macOS:
# brew install tesseract

# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

# 3. Make sure Ollama is running locally
# Install Ollama from https://ollama.ai/
# Pull a model: ollama pull llama2

# 4. Run the script
python generate_cv_profile.py \
    --github-data github_profile_data.json \
    --resume resume.pdf \
    --output my_cv.md \
    --ollama-model llama2

# Alternative with image resume
# python generate_cv_profile.py \
#     --github-data github_profile_data.json \
#     --resume resume.png \
#     --output my_cv.md \
#     --ollama-model codellama

echo "CV generated successfully!"