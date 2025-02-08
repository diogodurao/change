# Project Requirements Document (PRD): PDF Data Analyzer

## 1. Project Overview

The PDF Data Analyzer is a simple web application designed for personal use. It processes a manually uploaded PDF file, extracts data from the "Change %" column, and calculates the average for both positive and negative percentages over a selectable period. The results are displayed in a basic table format.

## 2. Functional Requirements

### 2.1 File Upload

- Users manually upload a single PDF file at a time.
- The PDF must not exceed 10MB.

### 2.2 Data Extraction

- Extract the "Change %" column from the PDF.
- Process varying amounts of data, ranging from 0 to 500+ days.
- Filter values into two categories: positive percentages and negative percentages.

### 2.3 Data Processing

- Compute the average of the positive percentages.
- Compute the average of the negative percentages.

### 2.4 Output

- Display results in a simple, structured table.
- Show:
  - Total number of positive/negative days.
  - Average percentage for positive values.
  - Average percentage for negative values.

## 3. Technical Requirements

### 3.1 Frontend

- Simple HTML/JavaScript user interface.
- Basic file upload input.
- Table to display results.

### 3.2 Backend

- Lightweight backend (Node.js or Python Flask) for PDF parsing.
- Use a library like `pdfplumber` (Python) or `pdf-parse` (Node.js) for text extraction.
- Process data and return results via API.

### 3.3 Performance Considerations

- Efficient PDF parsing to handle up to 500+ rows of data.
- Quick computation of averages.

## 4. User Interaction Flow

1. User uploads a PDF.
2. System extracts and processes the "Change %" column.
3. System calculates averages for positive and negative values.
4. System displays results in a table.

## 5. Constraints

- No support for multiple PDF uploads at once.
- No need for persistent storage; calculations are done on demand.

## 6. Future Enhancements (Optional)

- Allow CSV export of results.
- Add a simple chart visualization.
- Implement a date-range selection filter.

