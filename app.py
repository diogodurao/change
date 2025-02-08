from flask import Flask, request, render_template, jsonify
import os
import logging
from werkzeug.utils import secure_filename
from weekly_analyzer import WeeklyAnalyzer
from data_processor import DataProcessor

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            logger.debug(f"Saving uploaded file to {file_path}")
            file.save(file_path)
            
            logger.debug("Processing file")
            processor = DataProcessor()
            results = processor.process_file(file_path)
            
            # Process weekly analysis if data is available
            if results and 'data' in results:
                weekly_analyzer = WeeklyAnalyzer()
                weekly_results = weekly_analyzer.process_table_data(results['data'])
                results['weekly'] = weekly_results
            
            logger.debug(f"Processing complete. Results: {results}")
            
            # Clean up
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify(results)
            
        except Exception as e:
            logger.error(f"Error processing upload: {str(e)}", exc_info=True)
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    # Try to get port from environment variable, fallback to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # If port 5000 is in use, try the next available port
    while True:
        try:
            app.run(debug=True, port=port)
            break
        except OSError as e:
            if "Address already in use" in str(e):
                port += 1
                print(f"Port {port-1} is in use, trying port {port}")
            else:
                raise e 