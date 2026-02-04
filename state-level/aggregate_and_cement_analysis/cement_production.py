import pandas as pd

# Load data
df = pd.read_csv('cement_production_2021-12_8_2025.csv')

# Clean data (remove any missing values)
df = df.dropna(subset=['State', 'Cement Production'])

# Aggregate by state
state_summary = df.groupby('State').agg({
    'Cement Production': ['sum', 'mean', 'count'],
    'Facility Name': 'count'
}).reset_index()

# Flatten column names
state_summary.columns = [
    'State',
    'Total_Production',
    'Avg_Production_Per_Facility',
    'Num_Facilities_Producing',  # Facilities with production data
    'Total_Facilities'  # All facilities in state
]

# Sort by total production
state_summary = state_summary.sort_values('Total_Production', ascending=False)

# Display
print("Cement Production Summary by State:")
print("="*80)
print(state_summary.to_string(index=False))

# Save
state_summary.to_csv('cement_production_summary_by_state.csv', index=False)
print("\n✓ Saved to cement_production_summary_by_state.csv")

# Quick stats
print("\n" + "="*80)
print("NATIONAL SUMMARY")
print("="*80)
print(f"Total US cement production: {df['Cement Production'].sum():,.0f}")
print(f"Total facilities: {len(df)}")
print(f"States with production: {df['State'].nunique()}")
print(f"Average production per facility: {df['Cement Production'].mean():,.0f}")
print(f"Top producing state: {state_summary.iloc[0]['State']} ({state_summary.iloc[0]['Total_Production']:,.0f})")
