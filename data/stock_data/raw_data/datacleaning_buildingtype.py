"""
Clean Census ACS Table B25024 (Units in Structure)
1. Drop margin of error columns (ending with M)
2. Drop the first row
3. Map remaining columns to readable names
4. Handle quoted string values
5. Convert numeric columns (col 3 onward) to integers
"""

import pandas as pd
from pathlib import Path

COLUMN_MAPPING = {
    'GEO_ID': 'geo_id',
    'NAME': 'state_name',
    'B25024_001E': 'total_units',
    'B25024_002E': 'single_family_detached',
    'B25024_003E': 'single_family_attached',
    'B25024_004E': 'units_2',
    'B25024_005E': 'units_3_4',
    'B25024_006E': 'units_5_9',
    'B25024_007E': 'units_10_19',
    'B25024_008E': 'units_20_49',
    'B25024_009E': 'units_50_plus',
    'B25024_010E': 'mobile_homes',
    'B25024_011E': 'boat_rv_van',
}

def clean_census_data(input_file):
    """Clean Census ACS data by dropping MOE columns and renaming"""
    
    script_dir = Path(__file__).parent
    input_path = script_dir / input_file
    
    # Output directory
    output_dir = script_dir.parent / 'cleaned_data'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Reading {input_path.name}...")
    # Read with quotechar to handle quoted values
    df = pd.read_csv(input_path, quotechar='"')
    
    print(f"Original shape: {df.shape}")
    print(f"Original columns: {len(df.columns)}")
    
    # STEP 1: Drop all columns ending with 'M' (margin of error columns)
    moe_cols = [col for col in df.columns if col.endswith('M')]
    df_clean = df.drop(columns=moe_cols)
    print(f"✓ Dropped {len(moe_cols)} columns ending with 'M'")
    
    # STEP 2: Drop the first row (index 0)
    df_clean = df_clean.drop(index=0).reset_index(drop=True)
    print(f"✓ Dropped first row")
    
    # STEP 3: Rename remaining columns
    df_clean = df_clean.rename(columns=COLUMN_MAPPING)
    print(f"✓ Renamed columns to readable names")
    
    # STEP 4: Clean string values - remove extra quotes if present
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':  # Only process string columns
            df_clean[col] = df_clean[col].astype(str).str.strip().str.strip('"')
    print(f"✓ Cleaned string values")
    
    # STEP 5: Convert columns 3 onward to integers
    # (columns: total_units, single_family_detached, etc.)
    numeric_cols = df_clean.columns[2:]  # Skip first 2 columns (geo_id, state_name)
    
    for col in numeric_cols:
        try:
            # Remove commas if present, then convert to int
            df_clean[col] = df_clean[col].astype(str).str.replace(',', '').astype(int)
        except ValueError as e:
            print(f"⚠️  Warning: Could not convert column '{col}' to int: {e}")
    
    print(f"✓ Converted {len(numeric_cols)} numeric columns to integers")
    
    # Save
    output_file = output_dir / f"{input_path.stem}_cleaned.csv"
    df_clean.to_csv(output_file, index=False)
    
    print(f"✓ Saved to: {output_file}")
    print(f"Final shape: {df_clean.shape}")
    print(f"Final columns: {len(df_clean.columns)}\n")
    
    print("Column names and types:")
    for col in df_clean.columns:
        print(f"  - {col}: {df_clean[col].dtype}")
    
    print("\nPreview:")
    print(df_clean.head())
    
    return df_clean

def main():
    """Process all CSV files in raw_data directory"""
    
    script_dir = Path(__file__).parent
    
    print("="*60)
    print(f"Looking in: {script_dir}")
    print("="*60 + "\n")
    
    # Find CSV files
    csv_files = list(script_dir.glob('*.csv'))
    
    if not csv_files:
        print("❌ No CSV files found")
        return
    
    print(f"✓ Found {len(csv_files)} CSV file(s):")
    for f in csv_files:
        print(f"  - {f.name}")
    
    print("\n" + "="*60 + "\n")
    
    # Process each file
    for csv_file in csv_files:
        try:
            clean_census_data(csv_file.name)
            print("\n" + "="*60 + "\n")
        except Exception as e:
            print(f"❌ Error processing {csv_file.name}: {e}\n")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
    