"""
Merge cement production and aggregate production data
Handles state abbreviation mapping
Keeps cement and aggregate separate (no total)
"""

import pandas as pd

# ============================================================================
# STEP 1: State abbreviation mapping
# ============================================================================

STATE_ABBREV_TO_FULL = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
    'PR': 'Puerto Rico', 'VI': 'Virgin Islands', 'GU': 'Guam'
}

# ============================================================================
# STEP 2: Load both datasets
# ============================================================================

cement = pd.read_csv('cement_production_summary_by_state.csv')
aggregate = pd.read_csv('production_by_state_2021.csv')

print("Loaded data:")
print(f"  Cement: {len(cement)} states")
print(f"  Aggregate: {len(aggregate)} states")
print()

# ============================================================================
# STEP 3: Standardize state names
# ============================================================================

cement_has_abbrev = cement['State'].str.len().max() == 2

if cement_has_abbrev:
    print("✓ Cement data has state abbreviations - converting to full names")
    cement['State_Full'] = cement['State'].map(STATE_ABBREV_TO_FULL)
    
    unmapped = cement[cement['State_Full'].isna()]['State'].unique()
    if len(unmapped) > 0:
        print(f"⚠️  Warning: Could not map these states: {unmapped}")
        print()
    
    cement['State_Abbrev'] = cement['State']
    cement['State'] = cement['State_Full']
    cement = cement.drop(columns=['State_Full'])
else:
    print("✓ Cement data already has full state names")
    STATE_FULL_TO_ABBREV = {v: k for k, v in STATE_ABBREV_TO_FULL.items()}
    cement['State_Abbrev'] = cement['State'].map(STATE_FULL_TO_ABBREV)

aggregate['State'] = aggregate['State'].str.strip()

print()

# ============================================================================
# STEP 4: Merge datasets
# ============================================================================

merged = cement.merge(
    aggregate,
    on='State',
    how='outer',
    indicator=True
)

merged = merged.rename(columns={
    'Total_Production': 'Cement_Production',
    'Total_Quantity': 'Aggregate_Production'
})

merged['Cement_Production'] = merged['Cement_Production'].fillna(0)
merged['Aggregate_Production'] = merged['Aggregate_Production'].fillna(0)

# Sort by aggregate production (or however you prefer)
merged = merged.sort_values('Aggregate_Production', ascending=False)

# Reorder columns
column_order = [
    'State',
    'State_Abbrev',
    'Cement_Production',
    'Aggregate_Production',
    'Num_Cement_Production_Facilities',
    'Total_Facilities'
]

merged = merged[[col for col in column_order if col in merged.columns]]

# ============================================================================
# STEP 5: Display results
# ============================================================================

print("="*90)
print("MERGED PRODUCTION DATA (CEMENT + AGGREGATE) - 2021")
print("="*90)
print(f"{'State':<20} {'Abbrev':<8} {'Cement':>15} {'Aggregate':>15} {'Facilities':>10}")
print("-"*90)

for _, row in merged.iterrows():
    abbrev = row.get('State_Abbrev', 'N/A')
    facilities = row.get('Num_Facilities_Producing', 0)
    
    print(f"{row['State']:<20} "
          f"{abbrev:<8} "
          f"{row['Cement_Production']:>15,.0f} "
          f"{row['Aggregate_Production']:>15,.0f} "
          f"{facilities:>10.0f}")

print("="*90)
print(f"{'TOTAL':<20} {'':8} "
      f"{merged['Cement_Production'].sum():>15,.0f} "
      f"{merged['Aggregate_Production'].sum():>15,.0f}")
print()

# ============================================================================
# STEP 6: Data quality checks
# ============================================================================

print("DATA QUALITY CHECKS")
print("="*80)

if '_merge' in merged.columns:
    print("Merge statistics:")
    print(f"  Both datasets: {(merged['_merge'] == 'both').sum()} states")
    print(f"  Cement only: {(merged['_merge'] == 'left_only').sum()} states")
    print(f"  Aggregate only: {(merged['_merge'] == 'right_only').sum()} states")
    print()

cement_only = merged[
    (merged['Cement_Production'] > 0) & 
    (merged['Aggregate_Production'] == 0)
]['State'].tolist()

if cement_only:
    print(f"States with cement but NO aggregate data ({len(cement_only)}):")
    print(f"  {', '.join(cement_only)}")
    print()

aggregate_only = merged[
    (merged['Cement_Production'] == 0) & 
    (merged['Aggregate_Production'] > 0)
]['State'].tolist()

if aggregate_only:
    print(f"States with aggregate but NO cement data ({len(aggregate_only)}):")
    print(f"  {', '.join(aggregate_only)}")
    print()

# ============================================================================
# STEP 7: Summary statistics
# ============================================================================

print("SUMMARY STATISTICS")
print("="*80)
print(f"Total states: {len(merged)}")
print(f"States with cement: {(merged['Cement_Production'] > 0).sum()}")
print(f"States with aggregate: {(merged['Aggregate_Production'] > 0).sum()}")
print(f"States with both: {((merged['Cement_Production'] > 0) & (merged['Aggregate_Production'] > 0)).sum()}")
print()
print(f"Total cement production: {merged['Cement_Production'].sum():,.0f}")
print(f"Total aggregate production: {merged['Aggregate_Production'].sum():,.0f}")

if 'Num_Facilities_Producing' in merged.columns:
    print(f"Total cement facilities: {merged['Num_Facilities_Producing'].sum():.0f}")
print()

# ============================================================================
# STEP 8: Save merged dataset
# ============================================================================

if '_merge' in merged.columns:
    merged = merged.drop(columns=['_merge'])

merged.to_csv('merged_production_cement_aggregate.csv', index=False)
print("✓ Saved to merged_production_cement_aggregate.csv")
