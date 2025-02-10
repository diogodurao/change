import pandas as pd
import pdfplumber
import logging
import numpy as np

logger = logging.getLogger(__name__)

class DataProcessor:
    # Only focus on essential columns
    COLUMN_VARIATIONS = {
        'Date': ['date', 'fecha', 'data'],
        'Change %': ['change %', 'var %', 'change', 'variation %', 'var. %', '% change']
    }

    def __init__(self):
        self.df = None

    def process_file(self, file_path):
        """Process either PDF or CSV file and return standardized DataFrame."""
        try:
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                self.df = self._process_pdf(file_path)
            elif file_extension in ['csv', 'xlsx', 'xls']:
                self.df = self._process_spreadsheet(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")

            if self.df is not None and not self.df.empty:
                self._standardize_columns()
                self._clean_data()
                return self._calculate_metrics()
            else:
                raise ValueError("No data could be extracted from the file")

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise

    def _process_pdf(self, file_path):
        """Extract data from PDF using pdfplumber."""
        try:
            with pdfplumber.open(file_path) as pdf:
                tables = []
                for page in pdf.pages:
                    extracted_tables = page.extract_tables()
                    if extracted_tables:
                        tables.extend(extracted_tables)
                
                if not tables:
                    raise ValueError("No tables found in PDF")
                
                # Convert the first table with headers to DataFrame
                table = tables[0]
                headers = table[0]
                data = table[1:]
                return pd.DataFrame(data, columns=headers)
                
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise

    def _process_spreadsheet(self, file_path):
        """Process CSV or Excel files."""
        try:
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path)
            else:
                return pd.read_excel(file_path)
        except Exception as e:
            logger.error(f"Spreadsheet processing failed: {str(e)}")
            raise

    def _standardize_columns(self):
        """Standardize column names."""
        # Convert all column names to strings and clean them
        self.df.columns = self.df.columns.astype(str)
        self.df.columns = [col.strip().lower() for col in self.df.columns]
        
        # Create mapping for found columns
        column_mapping = {}
        for standard_name, variations in self.COLUMN_VARIATIONS.items():
            for col in self.df.columns:
                if col in variations or col == standard_name.lower():
                    column_mapping[col] = standard_name
                    break
        
        # Rename columns using the mapping
        self.df = self.df.rename(columns=column_mapping)

    def _clean_data(self):
        """Clean and convert data to appropriate types."""
        try:
            # Convert date
            self.df['Date'] = pd.to_datetime(self.df['Date'])
            
            # Clean Change % column
            if 'Change %' in self.df.columns:
                # Remove any non-numeric characters except decimal point and minus sign
                self.df['Change %'] = self.df['Change %'].astype(str).str.replace('[^0-9.-]', '', regex=True)
                self.df['Change %'] = pd.to_numeric(self.df['Change %'], errors='coerce').fillna(0)
            
            # Sort by date
            self.df = self.df.sort_values('Date', ascending=False)
            
        except Exception as e:
            logger.error(f"Error cleaning data: {str(e)}")
            raise

    def _calculate_metrics(self):
        """Calculate required metrics from the data."""
        try:
            change_col = 'Change %'
            
            # Get positive and negative changes
            positive_changes = self.df[self.df[change_col] > 0][change_col]
            negative_changes = self.df[self.df[change_col] < 0][change_col]
            
            metrics = {
                'daily': {
                    'positive_changes': positive_changes.tolist(),
                    'negative_changes': negative_changes.tolist(),
                    'positive_count': len(positive_changes),
                    'negative_count': len(negative_changes),
                    'positive_avg': positive_changes.mean() if not positive_changes.empty else 0,
                    'negative_avg': negative_changes.mean() if not negative_changes.empty else 0
                },
                'data': self.df[['Date', change_col]].to_dict('records')
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            raise 