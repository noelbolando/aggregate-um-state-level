"""
    This script creates a dynamic sankey diagram for aggregate consumption, production, imports, and exports.
    Spatial resolution: US (country-level)
    Temporal resolution: 1902-2022
    Data Source: https://www.usgs.gov/media/files/construction-sand-and-gravel-historical-statistics-data-series-140
"""

"""
Animated Sankey Diagram for Aggregate Material Flows
Reads from CSV with columns: Year, Production, Imports, Exports, Apparent consumption
"""

import plotly.graph_objects as go
import pandas as pd

# ============================================================================
# STEP 1: Load your data
# ============================================================================

# Load from CSV
df = pd.read_csv('sand_consumption_1902_2022-12092025.csv')  # Replace with your actual filename

# Clean column names (remove extra spaces)
df.columns = df.columns.str.strip()

# Rename for easier handling
df = df.rename(columns={
    'Year': 'year',
    'Production': 'production',
    'Imports': 'imports',
    'Exports': 'exports',
    'Apparent consumption': 'consumption'
})

# Display the data
print("Loaded data:")
print(df)
print()

# Verify balance: Production + Imports = Consumption + Exports
df['balance_check'] = (df['production'] + df['imports']) - (df['consumption'] + df['exports'])
print("Balance check (should be ~0):")
print(df[['year', 'balance_check']])
print()

# ============================================================================
# STEP 2: Create Sankey diagram function
# ============================================================================

import numpy as np

def create_sankey_for_year(year_data):
    production = year_data['production']
    imports = year_data['imports']
    exports = year_data['exports']
    consumption = year_data['consumption']
    
    production_to_domestic = production - exports
    production_to_exports = exports
    imports_to_domestic = imports
    
    # Store original values
    originals = [production_to_domestic, production_to_exports, imports_to_domestic]
    
    # Hybrid scaling
    def hybrid_scale(value, max_value):
        if value <= 0:
            return 0
        log_value = np.log10(value + 1)
        log_max = np.log10(max_value + 1)
        min_visible = log_max * 0.15
        return max(log_value, min_visible)
    
    max_flow = max(originals)
    scaled = [
        np.log10(production_to_domestic + 1),
        hybrid_scale(production_to_exports, max_flow),
        hybrid_scale(imports_to_domestic, max_flow)
    ]
    
    nodes = ["Domestic Extraction", "Imports", "Domestic<br>Consumption", "Exports"]
    
    # FORCE NODE POSITIONS (this is the key!)
    node_x = [0.01, 0.01, 0.99, 0.99]  # Left side, Left side, Right side, Right side
    node_y = [0.3, 0.7, 0.5, 0.9]      # Vertical positions
    
    links = {
        'source': [0, 0, 1],
        'target': [2, 3, 2],
        'value': scaled,
        'customdata': [f"Actual: {v:.1f}M tons" for v in originals],
        'label': [f"{v:.1f}M" for v in originals]
    }
    
    return {
        'nodes': nodes,
        'node_x': node_x,
        'node_y': node_y,
        'links': links,
        'node_colors': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],
        'link_colors': ['rgba(31, 119, 180, 0.4)', 'rgba(214, 39, 40, 0.4)', 'rgba(255, 127, 14, 0.4)'],
        'year': int(year_data['year']),
        'stats': {'production': production, 'imports': imports, 'exports': exports, 'consumption': consumption}
    }



# ============================================================================
# STEP 3: Create animation frames
# ============================================================================

frames = []
for _, row in df.iterrows():
    sankey_data = create_sankey_for_year(row)
    
    frame = go.Frame(
        data=[go.Sankey(
            node=dict(
                pad=20,
                thickness=25,
                line=dict(color="black", width=0.5),
                label=sankey_data['nodes'],
                color=sankey_data['node_colors'],
                customdata=[
                    f"Domestic Extraction: {sankey_data['stats']['production']:.1f}M tons",
                    f"Imports: {sankey_data['stats']['imports']:.1f}M tons",
                    f"Domestic Consumption: {sankey_data['stats']['consumption']:.1f}M tons",
                    f"Exports: {sankey_data['stats']['exports']:.1f}M tons"
                ],
                hovertemplate='%{label}<br>%{customdata}<extra></extra>'
            ),
            link=dict(
                source=sankey_data['links']['source'],
                target=sankey_data['links']['target'],
                value=sankey_data['links']['value'],
                label=sankey_data['links']['label'],
                color=sankey_data['link_colors'],
                hovertemplate='%{label}<extra></extra>'
            )
        )],
        name=str(sankey_data['year']),
        layout=go.Layout(
            title=dict(
                text=f"US Aggregate Material Flows - {sankey_data['year']}<br>" +
                     f"<sub>Domestic Extraction: {sankey_data['stats']['production']:.1f}M tons | " +
                     f"Imports: {sankey_data['stats']['imports']:.1f}M tons | " +
                     f"Exports: {sankey_data['stats']['exports']:.1f}M tons | " +
                     f"Domestic Consumption: {sankey_data['stats']['consumption']:.1f}M tons</sub>",
                font=dict(size=16)
            )
        )
    )
    frames.append(frame)

# ============================================================================
# STEP 4: Create initial figure (first year)
# ============================================================================

initial_data = create_sankey_for_year(df.iloc[0])

fig = go.Figure(
    data=[go.Sankey(
        arrangement='snap',  # Better layout algorithm
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="black", width=0.5),
            label=initial_data['nodes'],
            color=initial_data['node_colors'],
            customdata=[
                f"Domestic Extraction: {initial_data['stats']['production']:.1f}M tons",
                f"Imports: {initial_data['stats']['imports']:.1f}M tons",
                f"Domestic Consumption: {initial_data['stats']['consumption']:.1f}M tons",
                f"Exports: {initial_data['stats']['exports']:.1f}M tons"
            ],
            hovertemplate='%{label}<br>%{customdata}<extra></extra>'
        ),
        link=dict(
            source=initial_data['links']['source'],
            target=initial_data['links']['target'],
            value=initial_data['links']['value'],
            label=initial_data['links']['label'],
            color=initial_data['link_colors'],
            hovertemplate='%{label}<extra></extra>'
        )
    )],
    frames=frames
)

# ============================================================================
# STEP 5: Add slider and play/pause buttons
# ============================================================================

sliders = [dict(
    active=0,
    yanchor="top",
    y=-0.1,
    xanchor="left",
    x=0.1,
    currentvalue=dict(
        prefix="Year: ",
        visible=True,
        xanchor="right",
        font=dict(size=16)
    ),
    pad=dict(b=10, t=50),
    len=0.85,
    steps=[
        dict(
            args=[
                [frame.name],
                dict(
                    frame=dict(duration=240, redraw=False),
                    mode="immediate",
                    transition=dict(duration=250, easing='cubic-in-out')  
                )
            ],
            label=str(frame.name),
            method="animate"
        )
        for frame in frames
    ]
)]

updatemenus = [dict(
    type="buttons",
    showactive=False,
    y=-0.05,
    x=0,
    xanchor="left",
    yanchor="top",
    buttons=[
        dict(
            label="▶ Play",
            method="animate",
            args=[
                None,
                dict(
                    frame=dict(duration=1000, redraw=True),
                    fromcurrent=True,
                    mode="immediate",
                    transition=dict(duration=300)
                )
            ]
        ),
        dict(
            label="⏸ Pause",
            method="animate",
            args=[
                [None],
                dict(
                    frame=dict(duration=0, redraw=False),
                    mode="immediate",
                    transition=dict(duration=0)
                )
            ]
        )
    ]
)]

# ============================================================================
# STEP 6: Update layout
# ============================================================================

fig.update_layout(
    title=dict(
        text=f"US Aggregate Material Flows - {initial_data['year']}<br>" +
             f"<sub>Domestic Extraction: {initial_data['stats']['production']:.1f}M tons | " +
             f"Imports: {initial_data['stats']['imports']:.1f}M tons | " +
             f"Exports: {initial_data['stats']['exports']:.1f}M tons | " +
             f"Domestic Consumption: {initial_data['stats']['consumption']:.1f}M tons</sub>",
        font=dict(size=16)
    ),
    font=dict(size=14, family="Arial"),
    height=700,
    sliders=sliders,
    updatemenus=updatemenus,
    plot_bgcolor='white',
    paper_bgcolor='#f8f9fa',
    margin=dict(t=120, b=100, l=50, r=50)
)

# ============================================================================
# STEP 7: Show and save
# ============================================================================

# Show interactive figure
fig.show()

# Save to HTML file
output_file = "aggregate_flows_animated.html"
fig.write_html(output_file)
print(f"\n✓ Saved interactive diagram to {output_file}")

# Print summary statistics
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)
print(f"Years covered: {df['year'].min()} - {df['year'].max()}")
print(f"Average production: {df['production'].mean():.1f}M tons")
print(f"Average imports: {df['imports'].mean():.1f}M tons")
print(f"Average exports: {df['exports'].mean():.1f}M tons")
print(f"Average consumption: {df['consumption'].mean():.1f}M tons")
print(f"\nProduction change: {df['production'].iloc[-1] - df['production'].iloc[0]:.1f}M tons " +
      f"({((df['production'].iloc[-1] / df['production'].iloc[0]) - 1) * 100:.1f}%)")
print(f"Consumption change: {df['consumption'].iloc[-1] - df['consumption'].iloc[0]:.1f}M tons " +
      f"({((df['consumption'].iloc[-1] / df['consumption'].iloc[0]) - 1) * 100:.1f}%)")



