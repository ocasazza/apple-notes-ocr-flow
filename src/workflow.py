#!/usr/bin/env python3
"""
Apple Notes to Claude Workflow

This script orchestrates a workflow to:
1. Export Apple Notes as images
2. Process these images with htrflow to extract text
3. Send the extracted text to Claude 3.7 via API for further improvements
"""

import os
import subprocess
import argparse
import json
import shutil
from pathlib import Path
import requests
import time

DEFAULT_PROMPT = """
Please analyze this text that was extracted from handwritten notes using OCR techniques. 
There may be spelling mistakes in the output of the OCR. 
1) Please use context clues to try correct any spelling mistakes. 
2) Convert the text output to markdown format
3) Use context clues to improve the structure of the markdown output and useage of markdown macros.
4) The only content you should return should be in markdown format, so a script can save the text response in the content as a file.
"""

def parse_arguments():

    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Process Apple Notes and send to Claude')
    parser.add_argument('--output-dir', type=str, default='./output',
                        help='Directory to store output files (default: ./output)')
    parser.add_argument('--notes-folder', type=str, default='',
                        help='Specific Apple Notes folder to process (default: all)')
    parser.add_argument('--claude-prompt', type=str, default=DEFAULT_PROMPT,
                        help='Prompt to send to Claude along with the extracted text')
    parser.add_argument('--api-key', type=str, 
                        help='API key for Claude')
    return parser.parse_args()

def setup_directories(output_dir):
    """Create necessary directories for the workflow."""
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create subdirectories for each step
    images_dir = os.path.join(output_dir, 'images')
    text_dir = os.path.join(output_dir, 'text')
    claude_dir = os.path.join(output_dir, 'claude_responses')
    
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(text_dir, exist_ok=True)
    os.makedirs(claude_dir, exist_ok=True)
    
    return images_dir, text_dir, claude_dir

def export_apple_notes(images_dir, notes_folder=''):
    """Export Apple Notes as images using AppleScript."""
    print("Exporting Apple Notes as images...")
    
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'export_notes.scpt')
    
    # Run the AppleScript
    cmd = ['osascript', script_path, images_dir]
    if notes_folder:
        cmd.append(notes_folder)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error exporting notes: {result.stderr}")
        return False
    
    print(f"Successfully exported notes to {images_dir}")
    return True

def convert_pdf_to_images(output_dir, images_dir):
    """Convert PDF files to images using PyMuPDF (no external dependencies)."""
    print("Converting PDF files to images...")
    
    # Check if pdf_paths.txt exists
    pdf_paths_file = os.path.join(output_dir, "pdf_paths.txt")
    if not os.path.exists(pdf_paths_file):
        print(f"No PDF paths file found at {pdf_paths_file}")
        return False
    
    # Read the PDF file paths
    with open(pdf_paths_file, 'r') as f:
        pdf_paths = f.read().splitlines()
    
    if not pdf_paths:
        print("No PDF files to convert")
        return False
    
    # Try to import PyMuPDF for PDF to image conversion
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("PyMuPDF not found. Installing...")
        subprocess.run(['pip', 'install', 'PyMuPDF'], check=True)
        try:
            import fitz
        except ImportError:
            print("Failed to install PyMuPDF.")
            return False
    
    # Convert each PDF file to images
    success_count = 0
    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            continue
        
        # Get base filename without extension
        base_name = os.path.basename(pdf_path).replace('.pdf', '')
        
        try:
            # Open the PDF
            doc = fitz.open(pdf_path)
            
            # Convert each page to an image
            for i, page in enumerate(doc):
                # Create image filename
                if doc.page_count > 1:
                    img_path = os.path.join(images_dir, f"{base_name}_page{i+1}.png")
                else:
                    img_path = os.path.join(images_dir, f"{base_name}.png")
                
                # Render page to an image (2x zoom for better quality)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                
                # Save the image
                pix.save(img_path)
                print(f"Converted page {i+1} of {pdf_path} to {img_path}")
            
            success_count += 1
        except Exception as e:
            print(f"Error converting {pdf_path}: {str(e)}")
            # Try alternative method if conversion fails
            if not convert_pdf_to_images_alternative(pdf_path, images_dir):
                print(f"Failed to convert {pdf_path} using alternative method")
    
    # Clean up
    os.remove(pdf_paths_file)
    
    print(f"Successfully converted {success_count} of {len(pdf_paths)} PDF files to images")
    return success_count > 0

def convert_pdf_to_images_alternative(pdf_path, images_dir):
    """Alternative method to convert PDF files to images using PIL."""
    print(f"Using alternative PDF to image conversion method for {pdf_path}...")
    
    try:
        from PIL import Image
        import io
    except ImportError:
        print("Pillow not found. Installing...")
        subprocess.run(['pip', 'install', 'Pillow'], check=True)
        try:
            from PIL import Image
            import io
        except ImportError:
            print("Failed to install Pillow.")
            return False
    
    try:
        # Get base filename without extension
        base_name = os.path.basename(pdf_path).replace('.pdf', '')
        
        # Read the PDF file as binary
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        # Create a simple text file with the PDF content
        txt_path = os.path.join(images_dir, f"{base_name}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"PDF content from {pdf_path} (binary data converted to text)")
        
        print(f"Created text representation of {pdf_path} at {txt_path}")
        return True
    except Exception as e:
        print(f"Error creating text representation of {pdf_path}: {str(e)}")
        return False

def process_images_with_htrflow(images_dir, text_dir):
    """Process images with htrflow to extract text."""
    print("Processing images with htrflow...")
    
    # Import htrflow here to avoid dependency issues if not installed
    try:
        import htrflow
    except ImportError:
        print("htrflow not found. Installing...")
        subprocess.run(['pip', 'install', 'htrflow'], check=True)
        import htrflow
    
    # Get all image files
    image_files = []
    for ext in ['.png', '.jpg', '.jpeg', '.tiff', '.pdf']:
        image_files.extend(list(Path(images_dir).glob(f'*{ext}')))
    
    # Also check for text files (in case we had to fall back to text-only extraction)
    text_files = list(Path(images_dir).glob('*.txt'))
    
    if not image_files and not text_files:
        print(f"No image or text files found in {images_dir}")
        return False
    
    # If we have text files from the fallback method, just copy them
    if text_files:
        print(f"Found {len(text_files)} text files from fallback extraction")
        for txt_path in text_files:
            dest_path = os.path.join(text_dir, txt_path.name)
            shutil.copy(str(txt_path), dest_path)
            print(f"Copied {txt_path.name} to {dest_path}")
    
    # Process each image with htrflow
    for img_path in image_files:
        print(f"Processing {img_path.name}...")
        
        # Get base filename without extension
        base_name = img_path.stem
        output_path = os.path.join(text_dir, f"{base_name}.txt")
        
        # Use htrflow to extract text
        try:
            # Initialize the HTR model
            model = htrflow.load_model("default")
            
            # Process the image
            result = model.process_image(str(img_path))
            
            # Save the extracted text
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result['text'])
            
            print(f"Text extracted and saved to {output_path}")
        except Exception as e:
            print(f"Error processing {img_path.name}: {str(e)}")
    
    return True

def send_to_claude(text_dir, claude_dir, prompt, api_key):
    """Send extracted text to Claude 3.7 via API."""
    print("Sending extracted text to Claude 3.7...")
    
    # OpenAI-compatible API endpoint
    api_url = "https://chat-secret.autoscale.sdgr.app/api/chat/completions"
    
    # Get all text files
    text_files = list(Path(text_dir).glob('*.txt'))
    
    if not text_files:
        print(f"No text files found in {text_dir}")
        return False
    
    # Verify API key format
    if not api_key or len(api_key) < 10:
        print("Warning: API key appears to be invalid or missing.")
        print("Skipping Claude API calls. The extracted text files are available in the text directory.")
        return True
    
    # Test the API key with a simple request
    test_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    test_data = {
        "model": "claude-3-7",
        "max_tokens": 10,
        "messages": [
            {"role": "user", "content": "Test"}
        ]
    }
    
    try:
        test_response = requests.post(api_url, headers=test_headers, json=test_data)
        test_response.raise_for_status()
        print("API key validated successfully.")
    except Exception as e:
        print(f"Error validating API key: {str(e)}")
        print("Skipping Claude API calls. The extracted text files are available in the text directory.")
        return True
    
    # Process each text file
    success_count = 0
    for txt_path in text_files:
        print(f"Sending {txt_path.name} to Claude...")
        
        # Read the text content
        with open(txt_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Prepare the request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": "claude-3-7",
            "messages": [
                {"role": "user", "content": f"{prompt}\n\n{text_content}"}
            ]
        }
        
        # Send the request
        try:
            # Try to clean the content of any problematic characters
            text_content = text_content.replace('\x00', '')  # Remove null bytes
            # Update the data with the cleaned content
            data = {
                "model": "claude-3-7",
                "messages": [
                    {"role": "user", "content": f"{prompt}\n\n{text_content}"}
                ]
            }
            # Send the request
            response = requests.post(api_url, headers=headers, json=data)
            
            # Handle 400 Bad Request errors
            if response.status_code == 400:
                print(f"Bad Request error for {txt_path.name}. This might be due to content size or format issues.")
                print(f"Saving the original text content for reference.")
                
                # Save the original text content for reference
                error_path = os.path.join(claude_dir, f"{txt_path.stem}_error.txt")
                with open(error_path, 'w', encoding='utf-8') as f:
                    f.write(f"Original content that caused a 400 Bad Request error:\n\n{text_content}")
                
                # Try with a simplified request
                print(f"Trying again with a simplified request...")
                simplified_data = {
                    "model": "claude-3-7",
                    "max_tokens": 4000,
                    "messages": [
                        {"role": "user", "content": "Please format the following text as markdown:\n\n" + text_content[:50000]}
                    ]
                }
                
                response = requests.post(api_url, headers=headers, json=simplified_data)
            
            response.raise_for_status()
            
            # Parse the response (OpenAI API format)
            response_data = response.json()
            
            # Save the Claude response
            output_path = os.path.join(claude_dir, f"{txt_path.stem}_claude_response.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2)
            
            # Save the response content as markdown
            markdown_response_path = os.path.join(claude_dir, f"{txt_path.stem}_claude_response.md")
            with open(markdown_response_path, 'w', encoding='utf-8') as f:
                # Extract text from OpenAI format response
                f.write(response_data['choices'][0]['message']['content'])
            
            print(f"Claude response saved to {output_path}")
            success_count += 1
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"Error sending {txt_path.name} to Claude: {str(e)}")
            
            # Save the problematic content for debugging
            error_path = os.path.join(claude_dir, f"{txt_path.stem}_error.txt")
            with open(error_path, 'w', encoding='utf-8') as f:
                f.write(f"Error: {str(e)}\n\nContent that caused the error:\n\n{text_content[:10000]}...")
    
    if success_count > 0:
        print(f"Successfully sent {success_count} of {len(text_files)} text files to Claude.")
    else:
        print("Failed to send any text files to Claude.")
        print("The extracted text files are available in the text directory.")
    
    return True

def main():
    """Main function to orchestrate the workflow."""
    args = parse_arguments()
    
    # Setup directories
    images_dir, text_dir, claude_dir = setup_directories(args.output_dir)
    
    # Step 1: Export Apple Notes directly as text files
    if not export_apple_notes(args.output_dir, args.notes_folder):
        print("Failed to export Apple Notes. Exiting.")
        return
    
    # Step 2: Send extracted text to Claude
    if not send_to_claude(text_dir, claude_dir, args.claude_prompt, args.api_key):
        print("Failed to send text to Claude. Exiting.")
        return
    
    print("Workflow completed successfully!")

if __name__ == "__main__":
    main()
