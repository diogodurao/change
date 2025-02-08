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
                try:
                    # First try with default settings
                    tables = page.extract_tables()
                    
                    if not tables or not any(len(table) > 1 for table in tables):
                        # Try with custom settings
                        tables = page.extract_tables({
                            'vertical_strategy': 'text',
                            'horizontal_strategy': 'text',
                            'intersection_y_tolerance': 10
                        })
                    
                    if not tables or not any(len(table) > 1 for table in tables):
                        logger.warning(f"No tables found on page {page_num}")
                        continue
                        
                    logger.debug(f"Successfully extracted tables on page {page_num}")
                    
                    # Process each table
                    for table in tables:
                        if not table or len(table) < 2:  # Need at least header and one data row
                            continue
                        
                        # Clean and validate table data
                        cleaned_table = []
                        headers = [str(h).strip() if h else '' for h in table[0]]
                        cleaned_table.append(headers)
                        
                        # Process data rows
                        for row in table[1:]:
                            if not row or not any(row):  # Skip empty rows
                                continue
                            cleaned_row = [str(cell).strip() if cell else '' for cell in row]
                            if any(cleaned_row):  # Only add rows with data
                                cleaned_table.append(cleaned_row)
                        
                        if len(cleaned_table) < 2:  # Skip if no data rows after cleaning
                            continue
                            
                        logger.debug(f"Processing cleaned table with headers: {cleaned_table[0]}")
                        logger.debug(f"First data row: {cleaned_table[1]}")
                        
                        # Store all rows for weekly analysis
                        all_data.extend(cleaned_table)
                        
                        # Find the Change % column
                        change_idx = -1
                        for idx, header in enumerate(cleaned_table[0]):
                            if any(pattern in header.lower() for pattern in ['change %', 'var %', '% change', 'change']):
                                change_idx = idx
                                break
                        
                        if change_idx == -1:
                            logger.warning("Could not find Change % column, skipping table")
                            continue
                        
                        # Process each data row
                        for row in cleaned_table[1:]:
                            try:
                                if change_idx >= len(row):
                                    continue
                                    
                                value_str = row[change_idx].strip()
                                if not value_str:
                                    continue
                                    
                                # Remove any spaces and the % sign
                                value_str = value_str.replace(' ', '').replace('%', '')
                                logger.debug(f"Processing value: {value_str}")
                                
                                # Handle different decimal separators
                                value_str = value_str.replace(',', '.')
                                
                                # Convert to float
                                value = float(value_str)
                                logger.debug(f"Converted to float: {value}")
                                
                                if value > 0:
                                    positive_changes.append(value)
                                    logger.debug(f"Added positive value: {value}")
                                elif value < 0:
                                    negative_changes.append(value)
                                    logger.debug(f"Added negative value: {value}")
                                    
                            except (ValueError, TypeError, IndexError) as e:
                                logger.debug(f"Could not process row {row}: {e}")
                                continue
                                
                except Exception as e:
                    logger.error(f"Error extracting tables on page {page_num}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise

    logger.debug(f"Found {len(positive_changes)} positive changes: {positive_changes}")
    logger.debug(f"Found {len(negative_changes)} negative changes: {negative_changes}")

    try:
        # Calculate daily results
        daily_results = {
            'positive_count': len(positive_changes),
            'negative_count': len(negative_changes),
            'positive_avg': sum(positive_changes) / len(positive_changes) if positive_changes else 0,
            'negative_avg': sum(negative_changes) / len(negative_changes) if negative_changes else 0
        }
        
        # Check if table data was extracted
        if not all_data or len(all_data) < 2:
            logger.error("Insufficient table data extracted from PDF for weekly analysis.")
            raise ValueError("Insufficient table data extracted from PDF; please check the file formatting.")
        
        # Process weekly analysis
        weekly_analyzer = WeeklyAnalyzer()
        logger.debug("Starting weekly analysis with data:")
        logger.debug(f"Headers: {all_data[0]}")
        logger.debug(f"First row: {all_data[1]}")
        weekly_results = weekly_analyzer.process_table_data(all_data)
        
        # Combine results
        results = {
            'daily': daily_results,
            'weekly': weekly_results
        }
        
        logger.debug(f"Final results: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in final processing: {str(e)}", exc_info=True)
        raise

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
    # Changed port to 5034 to avoid conflicts
    app.run(debug=True, port=5034) 