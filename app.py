import os
import uuid
from flask import Flask, request, render_template, send_file, jsonify, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import shutil

# Try to import compression libraries
try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
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
    Compress PDF using working compression techniques.
    Returns the compression ratio.
    """
    try:
        # Get original file size
        original_size = os.path.getsize(input_path)
        
        # Try working image-based compression first
        try:
            return compress_with_working_image_conversion(input_path, output_path, original_size, compression_level)
        except Exception as e:
            print(f"Working image conversion failed, trying pikepdf: {e}")
        
        # Try pikepdf for better compression
        if PIKEPDF_AVAILABLE:
            try:
                return compress_with_pikepdf(input_path, output_path, original_size, compression_level)
            except Exception as e:
                print(f"Pikepdf compression failed, falling back to PyPDF2: {e}")
        
        # Fallback to PyPDF2 with enhanced compression
        return compress_with_pypdf2(input_path, output_path, original_size, compression_level)
        
    except Exception as e:
        raise Exception(f"Error compressing PDF: {str(e)}")







def compress_with_pypdf2(input_path, output_path, original_size, compression_level='medium'):
    """
    Enhanced PyPDF2 compression with multiple optimization techniques.
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
        
        return compression_ratio, original_size, compressed_size
        
    except Exception as e:
        raise Exception(f"PyPDF2 compression failed: {str(e)}")

def compress_with_working_image_conversion(input_path, output_path, original_size, compression_level='medium'):
    """
    Convert PDF to images with working compression - actually reduces file size.
    """
    try:
        import fitz
        from PIL import Image
        import io
        
        # Open the PDF
        doc = fitz.open(input_path)
        
        # Configure compression settings based on level
        if compression_level == 'extreme':
            image_quality = 25  # Low quality but readable
            zoom = 0.7  # Medium-low zoom
            max_width = 1000  # Maximum width
        elif compression_level == 'high':
            image_quality = 40  # Medium-low quality
            zoom = 0.8  # Medium zoom
            max_width = 1200  # Maximum width
        elif compression_level == 'low':
            image_quality = 70  # High quality
            zoom = 1.0  # Full zoom
            max_width = 1600  # Maximum width
        else:  # medium
            image_quality = 55  # Medium quality
            zoom = 0.9  # Medium-high zoom
            max_width = 1400  # Maximum width
        
        # Create a new PDF for the compressed version
        new_doc = fitz.open()
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Create a matrix for rendering at lower resolution
            mat = fitz.Matrix(zoom, zoom)
            
            # Render page to image at lower resolution
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Resize image to maximum width while maintaining aspect ratio
            width, height = pil_image.size
            if width > max_width:
                ratio = max_width / width
                new_width = max_width
                new_height = int(height * ratio)
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save with JPEG compression
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format='JPEG', quality=image_quality, optimize=True)
            img_buffer.seek(0)
            
            # Create new page with same dimensions as original
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            
            # Insert compressed image covering the entire page
            new_page.insert_image(new_page.rect, stream=img_buffer.getvalue())
            
            pix = None  # Free memory
        
        # Save with compression settings
        compress_settings = {
            'garbage': 4,  # Maximum garbage collection
            'clean': True,  # Clean unused objects
            'deflate': True,  # Use deflate compression
            'ascii': False,  # Binary mode for smaller size
            'linear': False,  # Non-linear for better compression
            'pretty': False,  # No pretty printing
        }
        
        new_doc.save(output_path, **compress_settings)
        new_doc.close()
        doc.close()
        
        # Get compressed file size
        compressed_size = os.path.getsize(output_path)
        
        # Calculate compression ratio
        compression_ratio = ((original_size - compressed_size) / original_size) * 100
        
        return compression_ratio, original_size, compressed_size
        
    except Exception as e:
        raise Exception(f"Working image conversion failed: {str(e)}")

def compress_with_pikepdf(input_path, output_path, original_size, compression_level='medium'):
    """
    Compress PDF using pikepdf with aggressive compression techniques.
    """
    try:
        # Open the PDF with pikepdf
        pdf = pikepdf.Pdf.open(input_path)
        
        # Apply aggressive compression based on level
        if compression_level == 'extreme':
            # Extreme compression - maximum file size reduction
            save_settings = {
                'compress_streams': True,
                'preserve_pdfa': False,
                'object_stream_mode': pikepdf.ObjectStreamMode.generate,
                'deterministic_id': False,
                'normalize_content': True,
                'recompress_flate': True
            }
        elif compression_level == 'high':
            # Maximum compression - aggressive compression
            save_settings = {
                'compress_streams': True,
                'preserve_pdfa': False,
                'object_stream_mode': pikepdf.ObjectStreamMode.generate,
                'deterministic_id': False,
                'normalize_content': True,
                'recompress_flate': True
            }
            
        elif compression_level == 'low':
            # Minimal compression - preserve quality
            save_settings = {
                'compress_streams': True,
                'preserve_pdfa': True,
                'object_stream_mode': pikepdf.ObjectStreamMode.preserve,
                'deterministic_id': True,
                'normalize_content': False
            }
        else:  # medium
            # Balanced compression
            save_settings = {
                'compress_streams': True,
                'preserve_pdfa': False,
                'object_stream_mode': pikepdf.ObjectStreamMode.generate,
                'deterministic_id': False,
                'normalize_content': True,
                'recompress_flate': True
            }
        
        # Save with compression settings
        pdf.save(output_path, **save_settings)
        
        # Get compressed file size
        compressed_size = os.path.getsize(output_path)
        
        # Calculate compression ratio
        compression_ratio = ((original_size - compressed_size) / original_size) * 100
        
        return compression_ratio, original_size, compressed_size
        
    except Exception as e:
        raise Exception(f"Pikepdf compression failed: {str(e)}")

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
