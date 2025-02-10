from flask import Flask, request, render_template, jsonify
import pdfplumber
import os
import logging
from werkzeug.utils import secure_filename
from weekly_analyzer import WeeklyAnalyzer

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def process_pdf(file_path):
    positive_changes = []
    negative_changes = []
    all_data = []  # Store all table data for weekly analysis
    
    logger.debug(f"Opening PDF file: {file_path}")
    try:
        with pdfplumber.open(file_path) as pdf:
            logger.debug(f"Number of pages in PDF: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages, 1):
                logger.debug(f"Processing page {page_num}")
                
                # Try different table extraction settings
                table_settings = [
                    {},  # Default settings
                    {
                        'text_x_tolerance': 5,
                        'text_y_tolerance': 5
                    },
                    {
                        'text_x_tolerance': 10,
                        'text_y_tolerance': 3,
                        'intersection_x_tolerance': 10,
                        'intersection_y_tolerance': 3
                    }
                ]
                
                tables = None
                for settings in table_settings:
                    try:
                        tables = page.extract_tables(**settings)
                        if tables and any(len(table) > 1 for table in tables):
                            logger.debug(f"Successfully extracted tables with settings: {settings}")
                            break
                    except Exception as e:
                        logger.debug(f"Failed to extract tables with settings {settings}: {str(e)}")
                        continue
                
                if not tables:
                    logger.warning(f"No tables found on page {page_num}")
                    continue
                
                logger.debug(f"Found {len(tables)} tables on page {page_num}")
                
                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:  # Skip empty tables or tables with just headers
                        continue
                    
                    logger.debug(f"Processing table {table_idx + 1}")
                    logger.debug(f"Table headers: {table[0]}")
                    
                    # Store all rows for weekly analysis
                    all_data.extend(table)
                    
                    # Process each row in the table (skip header)
                    for row in table[1:]:
                        if len(row) >= 7:  # Make sure row has enough columns
                            try:
                                # Get the percentage value from the last column
                                value_str = str(row[6]).strip()
                                logger.debug(f"Processing value: {value_str}")
                                
                                # Remove any spaces and the % sign
                                value_str = value_str.replace(' ', '').replace('%', '')
                                logger.debug(f"Cleaned value string: {value_str}")
                                
                                # Convert to float
                                value = float(value_str.replace(',', '.'))
                                logger.debug(f"Converted to float: {value}")
                                
                                if value > 0:
                                    positive_changes.append(value)
                                    logger.debug(f"Added positive value: {value}")
                                elif value < 0:
                                    negative_changes.append(value)
                                    logger.debug(f"Added negative value: {value}")
                                        
                            except (ValueError, TypeError) as e:
                                logger.debug(f"Could not convert value '{row[6]}': {e}")
                                continue

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise

    logger.debug(f"Found {len(positive_changes)} positive changes: {positive_changes}")
    logger.debug(f"Found {len(negative_changes)} negative changes: {negative_changes}")

    # Calculate daily results
    daily_results = {
        'positive_count': len(positive_changes),
        'negative_count': len(negative_changes),
        'positive_avg': sum(positive_changes) / len(positive_changes) if positive_changes else 0,
        'negative_avg': sum(negative_changes) / len(negative_changes) if negative_changes else 0
    }
    
    # Process weekly analysis
    weekly_analyzer = WeeklyAnalyzer()
    weekly_results = weekly_analyzer.process_table_data(all_data)
    
    # Combine results
    results = {
        'daily': daily_results,
        'weekly': weekly_results
    }
    
    logger.debug(f"Final results: {results}")
    return results

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
    
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            logger.debug(f"Saving uploaded file to {file_path}")
            file.save(file_path)
            
            logger.debug("Processing PDF file")
            results = process_pdf(file_path)
            
            logger.debug(f"Processing complete. Results: {results}")
            os.remove(file_path)  # Clean up the uploaded file
            return jsonify(results)
            
        except Exception as e:
            logger.error(f"Error processing upload: {str(e)}", exc_info=True)
            if os.path.exists(file_path):
                os.remove(file_path)  # Clean up the uploaded file
            return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    # Changed port to 5015 to avoid conflicts
    app.run(debug=True, port=5025)