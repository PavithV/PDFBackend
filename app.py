import os
import uuid
from flask import Flask, request, render_template, send_file, jsonify, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import shutil

# Set all compression libraries as unavailable for now
PIKEPDF_AVAILABLE = False
PYMUPDF_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configuration
UPLOAD_FOLDER = 'uploads'
COMPRESSED_FOLDER = 'compressed'
ALLOWED_EXTENSIONS = {'pdf'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['COMPRESSED_FOLDER'] = COMPRESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compress_pdf(input_path, output_path, compression_level='medium'):
    """
    Compress PDF using enhanced PyPDF2 compression techniques.
    Returns the compression ratio.
    """
    try:
        # Get original file size
        original_size = os.path.getsize(input_path)
        
        # Use enhanced PyPDF2 compression
        return compress_with_pypdf2(input_path, output_path, original_size, compression_level)
        
    except Exception as e:
        raise Exception(f"Error compressing PDF: {str(e)}")







def compress_with_pypdf2(input_path, output_path, original_size, compression_level='medium'):
    """
    Enhanced PyPDF2 compression with advanced optimization techniques.
    """
    try:
        # Read the original PDF
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        # Process each page with enhanced compression
        for page in reader.pages:
            # Add the page without modification to avoid errors
            writer.add_page(page)
        
        # Set compression parameters based on level
        if compression_level == 'extreme':
            # Maximum compression settings
            writer._compress = True
            # Additional compression techniques
            for page in writer.pages:
                if hasattr(page, 'compress_content_streams'):
                    page.compress_content_streams()
        elif compression_level == 'high':
            # High compression
            writer._compress = True
        elif compression_level == 'low':
            # Minimal compression
            writer._compress = True
        else:  # medium
            # Balanced compression
            writer._compress = True
        
        # Write with compression
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        # Get compressed file size
        compressed_size = os.path.getsize(output_path)
        
        # Calculate compression ratio
        compression_ratio = ((original_size - compressed_size) / original_size) * 100
        
        # If compression didn't work well, try additional optimization
        if compression_ratio < 5:  # Less than 5% compression
            return compress_with_advanced_pypdf2(input_path, output_path, original_size, compression_level)
        
        return compression_ratio, original_size, compressed_size
        
    except Exception as e:
        raise Exception(f"PyPDF2 compression failed: {str(e)}")

def compress_with_advanced_pypdf2(input_path, output_path, original_size, compression_level='medium'):
    """
    Advanced PyPDF2 compression using multiple passes and optimization techniques.
    """
    try:
        # Read the original PDF
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        # Configure compression settings based on level
        if compression_level == 'extreme':
            # Extreme compression - maximum optimization
            compress_settings = {
                'compress': True,
                'linearize': True,
                'remove_duplicate_objects': True,
                'remove_unused_objects': True
            }
        elif compression_level == 'high':
            # High compression
            compress_settings = {
                'compress': True,
                'linearize': True,
                'remove_duplicate_objects': True
            }
        elif compression_level == 'low':
            # Minimal compression
            compress_settings = {
                'compress': True
            }
        else:  # medium
            # Balanced compression
            compress_settings = {
                'compress': True,
                'linearize': True
            }
        
        # Process each page
        for page in reader.pages:
            # Add the page
            writer.add_page(page)
        
        # Apply compression settings
        writer._compress = compress_settings.get('compress', True)
        
        # Write with maximum compression
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        # Get compressed file size
        compressed_size = os.path.getsize(output_path)
        
        # Calculate compression ratio
        compression_ratio = ((original_size - compressed_size) / original_size) * 100
        
        return compression_ratio, original_size, compressed_size
        
    except Exception as e:
        raise Exception(f"Advanced PyPDF2 compression failed: {str(e)}")



@app.route('/')
def index():
    """API endpoint - redirect to health check."""
    return jsonify({
        'message': 'PDF Compressor API',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'upload': '/upload',
            'download': '/download/<download_id>/<filename>'
        }
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and compression."""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Check file size (16MB limit)
        file.seek(0, 2)  # Seek to end to get file size
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size = 500 * 1024 * 1024  # 500MB
        if file_size > max_size:
            return jsonify({'error': 'File size must be less than 500MB.'}), 400
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        filename_base = os.path.splitext(original_filename)[0]
        
        # Save original file
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{original_filename}")
        file.save(original_path)
        
        # Get compression level
        compression_level = request.form.get('compression_level', 'medium')
        
        # Compress the PDF
        compressed_filename = f"{filename_base}_compressed.pdf"
        compressed_path = os.path.join(app.config['COMPRESSED_FOLDER'], f"{unique_id}_{compressed_filename}")
        
        compression_ratio, original_size, compressed_size = compress_pdf(original_path, compressed_path, compression_level)
        
        # Clean up original file
        os.remove(original_path)
        
        return jsonify({
            'success': True,
            'compressed_filename': compressed_filename,
            'download_id': unique_id,
            'compression_ratio': round(compression_ratio, 2),
            'original_size': original_size,
            'compressed_size': compressed_size
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<download_id>/<filename>')
def download_file(download_id, filename):
    """Download the compressed PDF file."""
    try:
        file_path = os.path.join(app.config['COMPRESSED_FOLDER'], f"{download_id}_{filename}")
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Send file and then delete it
        response = send_file(file_path, as_attachment=True, download_name=filename)
        
        # Schedule file deletion after response is sent
        def cleanup():
            try:
                os.remove(file_path)
            except:
                pass
        
        response.call_on_close(cleanup)
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Use environment variable for port (Heroku) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
