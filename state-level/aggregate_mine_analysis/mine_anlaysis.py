"""
Cross-reference mine location data with mine status data
Keep only active mines (exclude Abandoned, AbandonedSealed, NonProdActive)
"""

import pandas as pd

# ============================================================================
# STEP 1: Load both datasets
# ============================================================================

# Load mine addresses
mines_address = pd.read_csv('US-DOL-All-Sand-Mines-Address_12072025.csv')

# Load mine status
mines_status = pd.read_csv('US-DOL-All-Sand-Mines_12072025.csv')

print("Loaded data:")
print(f"  Mines with addresses: {len(mines_address)} records")
print(f"  Mines with status: {len(mines_status)} records")
print()

# ============================================================================
# STEP 2: Check data
# ============================================================================

print("Sample from addresses:")
print(mines_address.head(3))
print()

print("Sample from status:")
print(mines_status.head(3))
print()

# Check what mine statuses exist in the data
print("Mine statuses in dataset:")
print(mines_status['Mine Status'].value_counts())
print()

# ============================================================================
# STEP 3: Filter out inactive mines
# ============================================================================

# Statuses to exclude
exclude_statuses = ['Abandoned', 'AbandonedSealed', 'NonProdActive']

# Filter to keep only mines NOT in the exclude list
mines_status_filtered = mines_status[
    ~mines_status['Mine Status'].isin(exclude_statuses)
].copy()

print(f"After filtering out {exclude_statuses}:")
print(f"  Mines with status before: {len(mines_status)}")
print(f"  Mines with status after: {len(mines_status_filtered)}")
print(f"  Removed: {len(mines_status) - len(mines_status_filtered)} inactive mines")
print()

print("Remaining mine statuses:")
print(mines_status_filtered['Mine Status'].value_counts())
print()

# ============================================================================
# STEP 4: Join datasets on Mine ID
# ============================================================================

# Merge address and status data
active_mines = mines_address.merge(
    mines_status_filtered,
    on='Mine ID',
    how='inner'  # Only keep mines that exist in BOTH datasets
)

print(f"After joining on Mine ID:")
print(f"  Active mines with complete data: {len(active_mines)}")
print()

# ============================================================================
# STEP 5: Check for duplicates or data quality issues
# ============================================================================

# Check for duplicate Mine IDs
duplicates = active_mines[active_mines.duplicated(subset=['Mine ID'], keep=False)]

if len(duplicates) > 0:
    print(f"⚠️  Warning: {len(duplicates)} duplicate Mine IDs found")
    print("Duplicate Mine IDs:")
    print(duplicates[['Mine ID', 'Mine Name_x', 'Mine Name_y', 'State']].head())
    print()
    
    # Optionally remove duplicates (keep first occurrence)
    active_mines = active_mines.drop_duplicates(subset=['Mine ID'], keep='first')
    print(f"After removing duplicates: {len(active_mines)} mines")
    print()

# Check if Mine Name differs between datasets
if 'Mine Name_x' in active_mines.columns and 'Mine Name_y' in active_mines.columns:
    name_mismatch = active_mines[active_mines['Mine Name_x'] != active_mines['Mine Name_y']]
    
    if len(name_mismatch) > 0:
        print(f"⚠️  Note: {len(name_mismatch)} mines have different names in the two datasets")
        print()
    
    # Use Mine Name from address dataset
    active_mines['Mine Name'] = active_mines['Mine Name_x']
    active_mines = active_mines.drop(columns=['Mine Name_x', 'Mine Name_y'])

# ============================================================================
# STEP 6: Count mines by state
# ============================================================================

mines_by_state = active_mines.groupby('State').size().reset_index(name='Num_Active_Mines')
mines_by_state = mines_by_state.sort_values('Num_Active_Mines', ascending=False)

print("="*60)
print("ACTIVE MINES BY STATE")
print("="*60)
print(f"{'State':<10} {'Active Mines':>15}")
print("-"*60)

for _, row in mines_by_state.iterrows():
    print(f"{row['State']:<10} {row['Num_Active_Mines']:>15,.0f}")

print("="*60)
print(f"{'TOTAL':<10} {mines_by_state['Num_Active_Mines'].sum():>15,.0f}")
print()

# ============================================================================
# STEP 7: Summary statistics
# ============================================================================

print("SUMMARY STATISTICS")
print("="*60)
print(f"Total active mines: {len(active_mines)}")
print(f"States with active mines: {active_mines['State'].nunique()}")
print(f"Average mines per state: {len(active_mines) / active_mines['State'].nunique():.1f}")
print()

print("Top 5 states by number of active mines:")
for i, row in mines_by_state.head(5).iterrows():
    pct = (row['Num_Active_Mines'] / mines_by_state['Num_Active_Mines'].sum()) * 100
    print(f"  {row['State']}: {row['Num_Active_Mines']:.0f} mines ({pct:.1f}%)")
print()

# Check commodity distribution
if 'Commodity' in active_mines.columns:
    print("Active mines by commodity:")
    print(active_mines['Commodity'].value_counts().head(10))
    print()

# ============================================================================
# STEP 8: Save results
# ============================================================================

# Reorder columns for cleaner output
column_order = [
    'Mine ID',
    'Mine Name',
    'Street',
    'City',
    'State',
    'Zip Code',
    'Commodity',
    'Mine Status',
    'Status Date',
    'Type of Mine'
]

# Only include columns that exist
active_mines_output = active_mines[[col for col in column_order if col in active_mines.columns]]

# Save active mines
active_mines_output.to_csv('active_mines.csv', index=False)
print("✓ Saved active mines to active_mines.csv")

# Save mines by state summary
mines_by_state.to_csv('active_mines_by_state.csv', index=False)
print("✓ Saved state summary to active_mines_by_state.csv")

# ============================================================================
# STEP 9: Save excluded mines (for reference)
# ============================================================================

# Get the mines that were filtered out
excluded_mines = mines_address.merge(
    mines_status[mines_status['Mine Status'].isin(exclude_statuses)],
    on='Mine ID',
    how='inner'
)

if len(excluded_mines) > 0:
    excluded_mines.to_csv('excluded_inactive_mines.csv', index=False)
    print(f"✓ Saved {len(excluded_mines)} excluded inactive mines to excluded_inactive_mines.csv")
    print()

print("="*60)
print("COMPLETE")
print("="*60)
