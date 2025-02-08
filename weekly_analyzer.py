import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class WeeklyAnalyzer:
    def __init__(self):
        self.weekly_data = []

    def process_table_data(self, table_data):
        """
        Process table data to analyze weekly changes.
        
        Args:
            table_data: List of lists containing rows with [date, price, open, high, low, volume, change%]
        Returns:
            Dictionary containing weekly analysis results
        """
        try:
            # Validate table data
            if not table_data or len(table_data) < 2:  # Need at least headers and one row
                logger.error("Table data is empty or has insufficient rows")
                raise ValueError("Invalid table data: insufficient rows")

            # Log the raw table data for debugging
            logger.debug(f"Raw table data first row: {table_data[0]}")
            logger.debug(f"Raw table data second row: {table_data[1]}")
            
            # Convert table data to DataFrame, skipping the header row
            df = pd.DataFrame(table_data[1:])  # Skip header row
            
            # Get column names from the first row
            headers = table_data[0]
            
            # Clean up header names (remove any whitespace and special characters)
            headers = [str(h).strip() for h in headers]
            
            # Ensure all columns are present
            df.columns = headers
            
            # Log the column names for debugging
            logger.debug(f"Column names in data: {list(df.columns)}")
            
            # More flexible column mapping with variations
            column_mapping = {
                'Date': 'Date',
                'Price': 'Close',
                'Último': 'Close',  # Spanish variation
                'Last': 'Close',    # Another variation
                'Open': 'Open',
                'Abertura': 'Open', # Spanish variation
                'High': 'High',
                'Máxima': 'High',   # Spanish variation
                'Low': 'Low',
                'Mínima': 'Low',    # Spanish variation
                'Vol.': 'Volume',
                'Volume': 'Volume',
                'Volumen': 'Volume', # Spanish variation
                'Change %': 'Change %',
                'Var %': 'Change %', # Variation
                'Change': 'Change %',
                '% Change': 'Change %'
            }
            
            # Create a mapping using only the columns that exist in the DataFrame
            actual_mapping = {col: column_mapping[col] for col in df.columns if col in column_mapping}
            
            # Log the actual mapping being used
            logger.debug(f"Using column mapping: {actual_mapping}")
            
            # Verify we have all required base columns (excluding Volume as it's optional)
            required_base_columns = {'Date', 'Close', 'Open', 'High', 'Low', 'Change %'}
            mapped_columns = set(actual_mapping.values())
            
            missing_columns = required_base_columns - mapped_columns
            if missing_columns:
                logger.error(f"Missing required columns after mapping: {missing_columns}")
                logger.error(f"Available columns: {list(df.columns)}")
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Rename columns to match our expected names
            df = df.rename(columns=actual_mapping)
            
            # Log the DataFrame columns after renaming
            logger.debug(f"DataFrame columns after renaming: {list(df.columns)}")
            
            # Convert date strings to datetime objects
            try:
                # First try with explicit format (DD/MM/YYYY)
                df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
            except:
                try:
                    # Try with default format
                    df['Date'] = pd.to_datetime(df['Date'])
                except:
                    try:
                        # Try with another common format (YYYY-MM-DD)
                        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
                    except Exception as e:
                        logger.error(f"Could not parse dates: {e}")
                        logger.debug(f"Date values: {df['Date'].values}")
                        raise ValueError("Could not parse date values")
            
            # Convert numeric columns and handle potential errors
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Change %']
            for col in numeric_columns:
                try:
                    # First, clean the values
                    df[col] = df[col].astype(str).apply(lambda x: x.strip().replace(',', '').replace('%', '').replace('K', ''))
                    # Convert to float
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    # Handle any NaN values
                    if df[col].isna().any():
                        logger.warning(f"Found NaN values in {col} after conversion")
                        df[col] = df[col].fillna(0)
                except Exception as e:
                    logger.error(f"Error converting column {col} to numeric: {e}")
                    logger.debug(f"Values in {col}: {df[col].values}")
                    raise ValueError(f"Could not convert {col} values to numeric format")
            
            # Handle Volume column separately as it's optional
            if 'Volume' in df.columns:
                try:
                    df['Volume'] = df['Volume'].astype(str).apply(lambda x: x.strip().replace(',', '').replace('K', '000') if x else '0')
                    df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0)
                except Exception as e:
                    logger.warning(f"Error converting Volume column: {e}. Setting to 0")
                    df['Volume'] = 0
            
            # Sort by date in descending order (newest to oldest)
            df = df.sort_values('Date', ascending=False)
            
            # Calculate previous day's close for percentage calculations
            df['Prev_Close'] = df['Close'].shift(-1)
            
            # Add day of week
            df['day_of_week'] = df['Date'].dt.day_name()
            
            # Calculate additional metrics
            df['Price_Range'] = df['High'] - df['Low']
            df['Range_Percent'] = (df['Price_Range'] / df['Low']) * 100
            df['High_Change_Percent'] = ((df['High'] - df['Prev_Close']) / df['Prev_Close']) * 100
            df['Low_Change_Percent'] = ((df['Low'] - df['Prev_Close']) / df['Prev_Close']) * 100
            
            # Group into weeks (Monday-Friday sequences)
            weekly_results = []
            current_week = []
            
            # Find the first day of the current week
            current_date = None
            week_start = None
            
            for idx, row in df.iterrows():
                if current_date is None:
                    current_date = row['Date']
                    week_start = current_date - timedelta(days=current_date.weekday())
                
                # Check if this row belongs to the current week
                if row['Date'] >= week_start and row['Date'] < week_start + timedelta(days=5):
                    current_week.append(row)
                else:
                    # Process completed week if it has 4 or 5 days
                    if len(current_week) >= 4:
                        weekly_results.append(self._analyze_week(current_week))
                    # Start new week
                    current_week = [row]
                    current_date = row['Date']
                    week_start = current_date - timedelta(days=current_date.weekday())
            
            # Process the last week if complete (4 or 5 days)
            if len(current_week) >= 4:
                weekly_results.append(self._analyze_week(current_week))
            
            if not weekly_results:
                logger.warning("No complete weeks found in the data")
                return {
                    'weekly_results': [],
                    'total_weeks': 0
                }
            
            return {
                'weekly_results': weekly_results,
                'total_weeks': len(weekly_results)
            }
            
        except Exception as e:
            logger.error(f"Error processing weekly data: {str(e)}", exc_info=True)
            raise

    def _analyze_week(self, week_data):
        """
        Analyze a single week of data with enhanced metrics.
        """
        # Sort the week data by date in chronological order (Monday to Friday)
        week_data = sorted(week_data, key=lambda x: x['Date'])
        
        # Get all trading days in the week
        week_days = set(row['day_of_week'] for row in week_data)
        all_days = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'}
        
        # Create a complete week dictionary with 0% for missing days
        complete_week = {}
        week_start = min(row['Date'] for row in week_data)
        
        # Find the day with highest volatility
        volatility_data = [(row['day_of_week'], row['Range_Percent'], row['Price_Range']) for row in week_data]
        max_volatility = max(volatility_data, key=lambda x: x[1])
        
        for day_name in all_days:
            day_data = next((row for row in week_data if row['day_of_week'] == day_name), None)
            if day_data is not None:
                complete_week[day_name] = {
                    'change': day_data['Change %'],
                    'date': day_data['Date'],
                    'is_market_closed': False,
                    'price_range': day_data['Price_Range'],
                    'range_percent': day_data['Range_Percent'],
                    'high_change': day_data['High_Change_Percent'],
                    'low_change': day_data['Low_Change_Percent'],
                    'high': day_data['High'],
                    'low': day_data['Low']
                }
            else:
                # Calculate the date for the missing day
                day_to_num = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4}
                missing_day_num = day_to_num[day_name]
                missing_date = week_start + timedelta(days=missing_day_num - week_start.weekday())
                complete_week[day_name] = {
                    'change': 0.0,
                    'date': missing_date,
                    'is_market_closed': True,
                    'price_range': 0.0,
                    'range_percent': 0.0,
                    'high_change': 0.0,
                    'low_change': 0.0,
                    'high': 0.0,
                    'low': 0.0
                }
        
        # Calculate cumulative changes and find streaks
        cumulative = 0.0
        daily_progress = []
        current_streak = {'direction': None, 'count': 0, 'days': []}
        longest_streak = {'direction': None, 'count': 0, 'days': []}
        highest_point = {'value': float('-inf'), 'day': None}
        turned_positive_day = None
        turned_negative_day = None
        
        # Process days in chronological order
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            data = complete_week[day]
            change = data['change']
            cumulative += change
            
            # Format daily progress with arrows and colors
            arrow = '↑' if change > 0 else '↓' if change < 0 else '→'
            daily_progress.append({
                'day': day,
                'date': data['date'].strftime('%Y-%m-%d'),
                'change': change,
                'cumulative': cumulative,
                'arrow': arrow,
                'is_market_closed': data['is_market_closed'],
                'price_range': data['price_range'],
                'range_percent': data['range_percent'],
                'high_change': data['high_change'],
                'low_change': data['low_change'],
                'high': data['high'],
                'low': data['low']
            })
            
            # Track highest point
            if cumulative > highest_point['value']:
                highest_point = {'value': cumulative, 'day': day}
            
            # Track when change turns positive/negative
            if turned_positive_day is None and cumulative > 0:
                turned_positive_day = day
            if turned_negative_day is None and cumulative < 0:
                turned_negative_day = day
            
            # Track streaks
            if not data['is_market_closed']:
                current_direction = 'positive' if change > 0 else 'negative' if change < 0 else None
                if current_direction:
                    if current_streak['direction'] == current_direction:
                        current_streak['count'] += 1
                        current_streak['days'].append(day)
                    else:
                        if current_streak['count'] > longest_streak['count']:
                            longest_streak = current_streak.copy()
                        current_streak = {'direction': current_direction, 'count': 1, 'days': [day]}
        
        # Check final streak
        if current_streak['count'] > longest_streak['count']:
            longest_streak = current_streak
        
        # Calculate basic statistics from actual trading days
        changes = [row['Change %'] for row in week_data]
        positive_changes = [c for c in changes if c > 0]
        negative_changes = [c for c in changes if c < 0]
        
        # Find best and worst days from actual trading days
        day_changes = [(row['day_of_week'], row['Change %']) for row in week_data]
        max_positive = max(((day, change) for day, change in day_changes if change > 0), default=(None, 0))
        max_negative = min(((day, change) for day, change in day_changes if change < 0), key=lambda x: x[1], default=(None, 0))
        
        result = {
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': max(row['Date'] for row in week_data).strftime('%Y-%m-%d'),
            'avg_positive': sum(positive_changes) / len(positive_changes) if positive_changes else 0,
            'avg_negative': sum(negative_changes) / len(negative_changes) if negative_changes else 0,
            'max_positive_day': max_positive[0],
            'max_positive_value': max_positive[1],
            'max_negative_day': max_negative[0],
            'max_negative_value': max_negative[1],
            'days_in_week': len(week_data),
            'daily_progress': daily_progress,
            'final_change': cumulative,
            'highest_point': highest_point,
            'turned_positive': turned_positive_day,
            'turned_negative': turned_negative_day,
            'longest_streak': {
                'direction': longest_streak['direction'],
                'count': longest_streak['count'],
                'days': '-'.join(longest_streak['days']) if longest_streak['days'] else None
            },
            'max_volatility': {
                'day': max_volatility[0],
                'range_percent': max_volatility[1],
                'price_range': max_volatility[2]
            }
        }
        
        return result 