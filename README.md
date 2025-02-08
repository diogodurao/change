# PDF Data Analyzer

A web application that analyzes PDF files to calculate average positive and negative percentage changes.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Upload a PDF file (max 10MB) containing a "Change %" column
2. The application will process the file and display:
   - Number of positive/negative days
   - Average percentage for positive values
   - Average percentage for negative values

## Features

- PDF file upload and processing
- Extraction of "Change %" column data
- Calculation of average positive and negative percentages
- Simple table display of results# change
