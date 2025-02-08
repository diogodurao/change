# Project Requirements Document (PRD): Weekly Change % Analyzer

## 1. Project Overview

This feature will analyze sequences of dates in the "Change %" column to calculate weekly averages and identify key data points. It will work alongside the existing system without modifying the current implementation by creating new files as needed.

## 2. Functional Requirements

### 2.1 Sequence Identification
- Identify sequences of consecutive trading days in the "dates" column.
- A valid week consists of **5 sequential trading days** (e.g., Monday–Friday).
- A new week starts if there is a gap of **one or more non-trading days** (e.g., Friday to Monday).

### 2.2 Data Processing
- For each identified week:
  - Compute the **average positive change %**.
  - Compute the **average negative change %**.
  - Identify the **day of the week with the highest positive change %**.
  - Identify the **day of the week with the highest negative change %**.

### 2.3 Output
- Display a structured summary of weekly calculations:
  - Week start and end dates.
  - Average positive and negative change % per week.
  - The weekday with the highest positive and negative change %.

## 3. Technical Requirements

### 3.1 Code Structure
- **Create a new file** (or multiple if necessary) for this functionality.
- Do **not modify** any existing code.

### 3.2 Dependencies
- Install any required dependencies to ensure smooth execution.
- Use libraries to correctly interpret dates and perform calculations (e.g., `pandas` for Python).

## 4. User Interaction Flow
1. System reads the "dates" column and identifies weekly sequences.
2. It computes average positive and negative change % per week.
3. It identifies the weekday with the highest positive and negative change %.
4. It outputs a structured summary of findings.

## 5. Constraints
- The feature must operate **independently** without affecting existing code.
- The system must correctly handle non-trading days when identifying weeks.

## 6. Future Enhancements (Optional)
- Allow custom selection of week length (e.g., different markets with different trading days).
- Generate visualizations for trends over multiple weeks.
- Export results as CSV or JSON.

