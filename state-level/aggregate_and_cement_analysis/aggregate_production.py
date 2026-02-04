"""
Extract 2021 production data by state from USGS data
Filters for specific year and aggregates by state
"""

import pandas as pd

# Load data
df = pd.read_csv('validated_sand_production_1971_2023-12082025.csv')

# Filter to 2021
df_2021 = df[df['Year'] == 2021]

# Aggregate by state (Quantity only)
production_by_state = df_2021.groupby('State Coverage')['Quantity'].sum().reset_index()
production_by_state.columns = ['State', 'Total_Quantity']

# Sort
production_by_state = production_by_state.sort_values('Total_Quantity', ascending=False)

# Display
print("PRODUCTION BY STATE - 2021")
print("="*60)
print(production_by_state.to_string(index=False))

# Save
production_by_state.to_csv('production_by_state_2021.csv', index=False)
print("\n✓ Saved to production_by_state_2021.csv")