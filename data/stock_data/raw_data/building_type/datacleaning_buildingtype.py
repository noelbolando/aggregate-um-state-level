"""
Clean Census ACS Table B25024 (Units in Structure)
Maps cryptic column codes to human-readable names
"""

import pandas as pd
import os
from pathlib import Path

# Column mapping dictionary
COLUMN_MAPPING = {
    'GEO_ID': 'geo_id',
    'NAME': 'state_name',
    
    # Total
    'B25024_001E': 'total_units',
    'B25024_001M': 'total_units_moe',
    
    # Single-family
    'B25024_002E': 'single_family_detached',
    'B25024_002M': 'single_family_detached_moe',
    'B25024_003E': 'single_family_attached',
    'B25024_003M': 'single_family_attached_moe',
    
    # Small multi-family
    'B25024_004E': 'units_2',
    'B25024_004M': 'units_2_moe',
    'B25024_005E': 'units_3_4',
    'B25024_005M': 'units_3_4_moe',
    
    # Medium multi-family
    'B25024_006E': 'units_5_9',
    'B25024_006M': 'units_5_9_moe',
    'B25024_007E': 'units_10_19',
    'B25024_007M': 'units_10_19_moe',
    
    # Large multi-family
    'B25024_008E': 'units_20_49',
    'B25024_008M': 'units_20_49_moe',
    'B25024_009E': 'units_50_plus',
    'B25024_009M': 'units_50_plus_moe',
    
    # Other
    'B25024_010E': 'mobile_homes',
    'B25024_010M': 'mobile_homes_moe',
    'B25024_011E': 'boat_rv_van',
    'B25024_011M': 'boat_rv_van_moe',
}

def clean_census_data(input_file, output_dir='../cleaned_data'):
    """
    Clean Census ACS data by renaming columns to readable names
    
    Parameters:
    -----------
    input_file : str
        Path to input CSV file
    output_dir : str
        Directory to save cleaned file (default: ../cleaned_data)
    
    Returns:
    --------
    pd.DataFrame
        Cleaned dataframe
    """
    
    # Read the data
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    
    # Show original columns
    print(f"\nOriginal columns: {len(df.columns)}")
    print(f"Original shape: {df.shape}")
    
    # Rename columns
    df_clean = df.rename(columns=COLUMN_MAPPING)
    
    # Show what changed
    renamed_cols = [col for col in df.columns if col in COLUMN_MAPPING]
    print(f"\nRenamed {len(renamed_cols)} columns")
    
    # Drop margin of error columns (optional - comment out if you want to keep them)
    moe_cols = [col for col in df_clean.columns if col.endswith('_moe')]
    df_clean = df_clean.drop(columns=moe_cols)
    print(f"Dropped {len(moe_cols)} margin of error columns")
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    input_name = Path(input_file).stem
    output_file = Path(output_dir) / f"{input_name}_cleaned.csv"
    
    # Save cleaned data
    df_clean.to_csv(output_file, index=False)
    print(f"\nSaved cleaned data to: {output_file}")
    print(f"Final shape: {df_clean.shape}")
    
    # Show sample of cleaned data
    print("\nFirst few rows:")
    print(df_clean.head())
    
    return df_clean

def main():
    """
    Main function to process all Census CSV files in current directory
    """
    
    # Find all CSV files in current directory
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in current directory!")
        return
    
    print(f"Found {len(csv_files)} CSV file(s):")
    for f in csv_files:
        print(f"  - {f}")
    
    print("\n" + "="*60)
    
    # Process each file
    for csv_file in csv_files:
        try:
            clean_census_data(csv_file)
            print("\n" + "="*60 + "\n")
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
            print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
    