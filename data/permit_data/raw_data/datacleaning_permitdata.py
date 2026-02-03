###
#== US Census Permit Data
#== Source: https://www.census.gov/construction/bps/index.html
###
#== This data contains the residental permit data
#== Downloaded: 12/07/2025
###

import sys
import re
from pathlib import Path
import pandas as pd


def clean_csv_file(input_file, output_dir=None):
    """
    Clean a CSV file by removing empty rows/columns.
    
    Args:
        input_file: Path to CSV file
        output_dir: Directory to save cleaned CSV (defaults to same directory as input)
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: File '{input_file}' does not exist")
        return
    
    # Determine output directory
    if output_dir is None:
        output_path = input_path.parent
    else:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"Processing: {input_path.name}")
        
        # Read CSV file without headers
        df = pd.read_csv(input_file, header=None)
        
        print(f"  Original size: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Remove first 3 rows
        df = df.iloc[6:]
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove completely empty columns
        df = df.dropna(axis=1, how='all')
        
        # Strip whitespace from all string cells
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Replace NaN with empty string for cleaner CSV output
        df = df.fillna('')
        
        # Extract year from filename (e.g., stateannual_202299.csv -> 2022)
        year_match = re.search(r'(\d{4})', input_path.stem)
        if year_match:
            year = year_match.group(1)
            # Add year column as the first column
            df.insert(0, 'year', year)
            print(f"  Extracted year: {year}")
        else:
            print(f"  Warning: Could not extract year from filename")
        
        print(f"  Cleaned size: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Add column headers
        column_names = [
            'year',
            'location',
            'total',
            'num_1_units',
            'num_2_units',
            'num_3_4_units',
            'num_5_more_units',
            'num_structures_more_5_units'
        ]
        
        # Make sure we have the right number of columns
        if len(df.columns) == len(column_names):
            df.columns = column_names
            print(f"  ✓ Added column headers")
        else:
            print(f"  Warning: Expected {len(column_names)} columns but found {len(df.columns)}")
        
        # Save as CSV
        csv_filename = input_path.stem + '_cleaned.csv'
        csv_path = output_path / csv_filename
        
        df.to_csv(csv_path, index=False)
        print(f"  ✓ Saved: {csv_filename}")
        
    except Exception as e:
        print(f"  ✗ Error processing {input_path.name}: {str(e)}")


def clean_all_csv_in_directory(input_dir='.', output_dir=None):
    """
    Clean all CSV files in a directory.
    
    Args:
        input_dir: Directory containing CSV files (defaults to current directory)
        output_dir: Directory to save cleaned CSVs (defaults to same as input_dir)
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Directory '{input_dir}' does not exist")
        return
    
    # Find all CSV files
    csv_files = list(input_path.glob('*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in '{input_dir}'")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to clean\n")
    
    for csv_file in csv_files:
        clean_csv_file(csv_file, output_dir)
        print()
    
    print("✓ All files processed!")


if __name__ == "__main__":
    # Default output directory is ../cleaned_data
    default_output = Path('..') / 'cleaned_data'
    
    if len(sys.argv) < 2:
        # No arguments - process all CSV files in current directory
        print("Processing all CSV files in current directory")
        print(f"Output directory: {default_output}\n")
        clean_all_csv_in_directory('.', default_output)
    elif len(sys.argv) == 2:
        # Single argument - could be a file or directory
        path = Path(sys.argv[1])
        if path.is_file():
            clean_csv_file(sys.argv[1], default_output)
        elif path.is_dir():
            clean_all_csv_in_directory(sys.argv[1], default_output)
        else:
            print(f"Error: '{sys.argv[1]}' is not a valid file or directory")
    else:
        # Two arguments - input and output
        path = Path(sys.argv[1])
        if path.is_file():
            clean_csv_file(sys.argv[1], sys.argv[2])
        elif path.is_dir():
            clean_all_csv_in_directory(sys.argv[1], sys.argv[2])
        else:
            print(f"Error: '{sys.argv[1]}' is not a valid file or directory")