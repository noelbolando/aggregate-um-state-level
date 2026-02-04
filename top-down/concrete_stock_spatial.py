"""
Spatially-Explicit Top-Down Concrete Stock Estimation
======================================================

Extends the top-down model to distribute national stock across geographic units
using multiple allocation methods and proxy variables.

Methods for spatial allocation:
1. Population-based
2. GDP/Economic activity
3. Building floor area
4. Construction spending (historical)
5. Nighttime lights
6. Hybrid multi-factor approach
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from typing import Dict, List, Tuple
import seaborn as sns

# ============================================================================
# SPATIAL ALLOCATION METHODS
# ============================================================================

class SpatialAllocator:
    """
    Class for allocating national concrete stock to spatial units.
    """
    
    def __init__(self, national_stock: float, spatial_units: List[str]):
        """
        Args:
            national_stock: Total national stock in million metric tons
            spatial_units: List of geographic unit names (states, counties, etc.)
        """
        self.national_stock = national_stock
        self.spatial_units = spatial_units
        self.n_units = len(spatial_units)
        
    def allocate_by_population(self, population: pd.Series) -> pd.Series:
        """
        Simple population-proportional allocation.
        
        Assumption: Stock per capita is uniform across regions.
        Pro: Simple, data readily available
        Con: Ignores regional differences in building types, wealth
        
        Args:
            population: Population by spatial unit
            
        Returns:
            Allocated stock by spatial unit (million metric tons)
        """
        allocation_factor = population / population.sum()
        return self.national_stock * allocation_factor
    
    def allocate_by_gdp(self, gdp: pd.Series) -> pd.Series:
        """
        GDP-proportional allocation.
        
        Assumption: Material stock correlates with economic output
        Pro: Captures economic development differences
        Con: Service economies have lower material intensity
        
        Args:
            gdp: GDP by spatial unit (same units)
            
        Returns:
            Allocated stock by spatial unit
        """
        allocation_factor = gdp / gdp.sum()
        return self.national_stock * allocation_factor
    
    def allocate_by_floor_area(self, floor_area: pd.Series) -> pd.Series:
        """
        Building floor area-based allocation.
        
        Assumption: Stock proportional to total building floor area
        Pro: Most direct relationship to buildings
        Con: Doesn't account for building height/structure type
        
        Args:
            floor_area: Total building floor area by spatial unit (m²)
            
        Returns:
            Allocated stock by spatial unit
        """
        allocation_factor = floor_area / floor_area.sum()
        return self.national_stock * allocation_factor
    
    def allocate_by_construction_spending(self, spending_ts: pd.DataFrame) -> pd.Series:
        """
        Historical construction spending-based allocation.
        
        Uses time series of construction spending to build up stock spatially,
        accounting for different growth rates in different regions.
        
        Assumption: Regions with more historical construction have more stock
        Pro: Captures temporal dynamics
        Con: Requires detailed historical data
        
        Args:
            spending_ts: DataFrame with columns for each spatial unit, rows for years
            
        Returns:
            Allocated stock by spatial unit
        """
        # Calculate cumulative spending share for each region
        cumulative_spending = spending_ts.sum(axis=0)  # Sum over time
        allocation_factor = cumulative_spending / cumulative_spending.sum()
        return self.national_stock * allocation_factor
    
    def allocate_by_nighttime_lights(self, ntl: pd.Series) -> pd.Series:
        """
        Nighttime lights-based allocation.
        
        Assumption: Light intensity correlates with built environment
        Pro: Globally available, spatially detailed
        Con: Biased toward commercial/industrial, not residential
        
        Args:
            ntl: Total nighttime light radiance by spatial unit
            
        Returns:
            Allocated stock by spatial unit
        """
        allocation_factor = ntl / ntl.sum()
        return self.national_stock * allocation_factor
    
    def allocate_hybrid(self, weights: Dict[str, float], 
                       **proxy_data) -> pd.Series:
        """
        Multi-factor weighted allocation.
        
        Combines multiple proxy variables with weights.
        
        Example:
            weights = {'population': 0.3, 'gdp': 0.4, 'floor_area': 0.3}
            
        Args:
            weights: Dictionary of weights for each proxy (must sum to 1.0)
            **proxy_data: Keyword arguments with proxy data (pd.Series)
            
        Returns:
            Allocated stock by spatial unit
        """
        assert abs(sum(weights.values()) - 1.0) < 0.001, "Weights must sum to 1.0"
        
        # Initialize with zeros
        result = pd.Series(0.0, index=proxy_data[list(proxy_data.keys())[0]].index)
        
        # Combine proxies with weights
        for proxy_name, weight in weights.items():
            if proxy_name in proxy_data:
                proxy = proxy_data[proxy_name]
                allocation_factor = proxy / proxy.sum()
                result += weight * self.national_stock * allocation_factor
        
        return result
    
    def allocate_with_building_types(self, building_type_fractions: pd.DataFrame,
                                     type_intensities: Dict[str, float]) -> pd.Series:
        """
        Allocation accounting for building type composition.
        
        Different regions have different mixes of building types
        (e.g., NYC more high-rise, suburbs more single-family)
        
        Args:
            building_type_fractions: DataFrame [spatial_unit × building_type]
                                    Each row sums to 1.0
            type_intensities: Concrete intensity by building type 
                            (tons per unit floor area or per building)
            
        Returns:
            Allocated stock by spatial unit
        """
        # Calculate relative material intensity for each region
        intensity_scores = pd.Series(0.0, index=building_type_fractions.index)
        
        for building_type, intensity in type_intensities.items():
            if building_type in building_type_fractions.columns:
                intensity_scores += (
                    building_type_fractions[building_type] * intensity
                )
        
        # Normalize to sum to 1.0
        allocation_factor = intensity_scores / intensity_scores.sum()
        return self.national_stock * allocation_factor


# ============================================================================
# ENHANCED MODEL WITH SPATIAL CAPABILITIES
# ============================================================================

def load_spatial_proxy_data(method: str = 'state') -> pd.DataFrame:
    """
    Load proxy data for spatial allocation.
    
    Args:
        method: Geographic resolution ('state', 'county', 'msa')
        
    Returns:
        DataFrame with proxy variables by spatial unit
    """
    # Sample data - replace with real data sources
    # For states:
    if method == 'state':
        # Top 10 states by population for demo
        states = ['California', 'Texas', 'Florida', 'New York', 'Pennsylvania',
                 'Illinois', 'Ohio', 'Georgia', 'North Carolina', 'Michigan']
        
        data = {
            'state': states,
            # Population (millions) - approximate 2024
            'population': [39.0, 30.0, 22.0, 19.5, 13.0, 12.6, 11.8, 11.0, 10.8, 10.0],
            # GDP (billions $) - approximate
            'gdp': [3900, 2400, 1400, 2000, 900, 1000, 800, 750, 700, 600],
            # Building floor area (million m²) - estimated
            'floor_area': [8000, 6500, 5000, 4500, 3000, 2800, 2600, 2400, 2300, 2200],
            # Urbanization rate (0-1)
            'urbanization': [0.95, 0.85, 0.91, 0.88, 0.79, 0.88, 0.78, 0.76, 0.66, 0.75],
            # Avg construction year (proxy for building age)
            'avg_construction_year': [1975, 1980, 1985, 1960, 1955, 1965, 1958, 1985, 1980, 1960],
        }
        
        df = pd.DataFrame(data)
        df['state_abbrev'] = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI']
        
        return df
    
    else:
        raise NotImplementedError(f"Method {method} not yet implemented")


def calculate_regional_characteristics(proxy_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate derived characteristics for regions.
    
    Args:
        proxy_data: DataFrame with basic proxy variables
        
    Returns:
        Enhanced DataFrame with derived metrics
    """
    df = proxy_data.copy()
    
    # Population density proxy (using urbanization as proxy)
    df['density_score'] = df['urbanization'] * df['population']
    
    # Economic development score
    df['gdp_per_capita'] = df['gdp'] / df['population']
    
    # Building age score (older buildings = more accumulated stock)
    current_year = 2024
    df['avg_building_age'] = current_year - df['avg_construction_year']
    
    # Floor area per capita
    df['floor_area_per_capita'] = df['floor_area'] / df['population']
    
    return df


def allocate_national_stock(national_stocks: Dict[str, float],
                           proxy_data: pd.DataFrame,
                           method: str = 'hybrid') -> pd.DataFrame:
    """
    Allocate national stock to spatial units.
    
    Args:
        national_stocks: Stock by building type (million metric tons)
        proxy_data: Spatial proxy data
        method: Allocation method ('population', 'gdp', 'hybrid', etc.)
        
    Returns:
        DataFrame with allocated stocks by spatial unit and building type
    """
    results = proxy_data[['state', 'state_abbrev']].copy()
    
    # Calculate enhanced characteristics
    proxy_data = calculate_regional_characteristics(proxy_data)
    
    # For each building type, allocate differently
    for building_type, national_stock in national_stocks.items():
        if building_type == 'total':
            continue
            
        allocator = SpatialAllocator(national_stock, proxy_data['state'].tolist())
        
        if method == 'population':
            results[f'{building_type}_stock'] = allocator.allocate_by_population(
                proxy_data['population']
            )
        
        elif method == 'gdp':
            results[f'{building_type}_stock'] = allocator.allocate_by_gdp(
                proxy_data['gdp']
            )
        
        elif method == 'floor_area':
            results[f'{building_type}_stock'] = allocator.allocate_by_floor_area(
                proxy_data['floor_area']
            )
        
        elif method == 'hybrid':
            # Different building types use different allocation strategies
            if building_type == 'residential':
                # Residential: Population + floor area
                results[f'{building_type}_stock'] = allocator.allocate_hybrid(
                    weights={'population': 0.6, 'floor_area': 0.4},
                    population=proxy_data['population'],
                    floor_area=proxy_data['floor_area']
                )
            elif building_type == 'commercial':
                # Commercial: GDP + urbanization
                urban_score = proxy_data['urbanization'] * proxy_data['population']
                results[f'{building_type}_stock'] = allocator.allocate_hybrid(
                    weights={'gdp': 0.7, 'urban': 0.3},
                    gdp=proxy_data['gdp'],
                    urban=urban_score
                )
            elif building_type == 'institutional':
                # Institutional: Population-based (schools, hospitals serve people)
                results[f'{building_type}_stock'] = allocator.allocate_by_population(
                    proxy_data['population']
                )
            elif building_type == 'industrial':
                # Industrial: GDP-based
                results[f'{building_type}_stock'] = allocator.allocate_by_gdp(
                    proxy_data['gdp']
                )
    
    # Calculate total for each region
    stock_columns = [col for col in results.columns if col.endswith('_stock')]
    results['total_stock'] = results[stock_columns].sum(axis=1)
    
    # Add proxy data for reference
    results['population'] = proxy_data['population'].values
    results['gdp'] = proxy_data['gdp'].values
    results['floor_area'] = proxy_data['floor_area'].values
    
    # Calculate per capita metrics
    results['stock_per_capita'] = results['total_stock'] / results['population']  # million tons / million people = tons/person
    
    return results


# ============================================================================
# VISUALIZATION FOR SPATIAL RESULTS
# ============================================================================

def plot_spatial_distribution(spatial_results: pd.DataFrame):
    """
    Create visualizations of spatial distribution.
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Sort by total stock for better visualization
    df = spatial_results.sort_values('total_stock', ascending=False)
    
    # Plot 1: Total stock by state (bar chart)
    ax = axes[0, 0]
    colors = plt.cm.viridis(np.linspace(0, 1, len(df)))
    ax.bar(range(len(df)), df['total_stock'], color=colors)
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df['state_abbrev'], rotation=45, ha='right')
    ax.set_ylabel('Total Stock (million metric tons)')
    ax.set_title('Concrete Stock by State')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Per capita stock (bar chart)
    ax = axes[0, 1]
    df_sorted_pc = spatial_results.sort_values('stock_per_capita', ascending=False)
    colors = plt.cm.plasma(np.linspace(0, 1, len(df_sorted_pc)))
    ax.bar(range(len(df_sorted_pc)), df_sorted_pc['stock_per_capita'], color=colors)
    ax.set_xticks(range(len(df_sorted_pc)))
    ax.set_xticklabels(df_sorted_pc['state_abbrev'], rotation=45, ha='right')
    ax.set_ylabel('Stock per Capita (metric tons/person)')
    ax.set_title('Per Capita Concrete Stock by State')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Stock composition by state (stacked bar)
    ax = axes[1, 0]
    building_types = ['residential', 'commercial', 'institutional', 'industrial']
    stock_cols = [f'{bt}_stock' for bt in building_types]
    
    df_plot = df.set_index('state_abbrev')[stock_cols]
    df_plot.columns = building_types
    df_plot.plot(kind='bar', stacked=True, ax=ax, 
                colormap='Set3', width=0.8)
    ax.set_ylabel('Stock (million metric tons)')
    ax.set_title('Stock Composition by State')
    ax.legend(title='Building Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3, axis='y')
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Plot 4: Stock vs. Population (scatter with labels)
    ax = axes[1, 1]
    ax.scatter(spatial_results['population'], spatial_results['total_stock'],
              s=100, alpha=0.6, c=spatial_results['stock_per_capita'],
              cmap='coolwarm', edgecolors='black', linewidth=1)
    
    # Add state labels
    for idx, row in spatial_results.iterrows():
        ax.annotate(row['state_abbrev'], 
                   (row['population'], row['total_stock']),
                   fontsize=8, ha='center')
    
    ax.set_xlabel('Population (millions)')
    ax.set_ylabel('Total Stock (million metric tons)')
    ax.set_title('Stock vs. Population (color = per capita stock)')
    ax.grid(True, alpha=0.3)
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap='coolwarm',
                               norm=plt.Normalize(vmin=spatial_results['stock_per_capita'].min(),
                                                 vmax=spatial_results['stock_per_capita'].max()))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Stock per Capita (tons/person)', rotation=270, labelpad=20)
    
    plt.tight_layout()
    plt.savefig('spatial_concrete_stock.png', dpi=300, bbox_inches='tight')
    print("\nSaved spatial visualization to spatial_concrete_stock.png")


def print_spatial_summary(spatial_results: pd.DataFrame):
    """
    Print summary statistics for spatial distribution.
    """
    print("\n" + "="*80)
    print("SPATIAL DISTRIBUTION OF CONCRETE STOCK")
    print("="*80)
    
    print(f"\nNumber of spatial units: {len(spatial_results)}")
    print(f"Total national stock: {spatial_results['total_stock'].sum():,.0f} million metric tons")
    
    print("\n--- TOP 5 STATES BY TOTAL STOCK ---")
    top5 = spatial_results.nlargest(5, 'total_stock')[['state', 'total_stock', 'population', 'stock_per_capita']]
    print(top5.to_string(index=False))
    
    print("\n--- TOP 5 STATES BY PER CAPITA STOCK ---")
    top5_pc = spatial_results.nlargest(5, 'stock_per_capita')[['state', 'stock_per_capita', 'population', 'total_stock']]
    print(top5_pc.to_string(index=False))
    
    print("\n--- SUMMARY STATISTICS ---")
    print(f"Mean per capita stock:   {spatial_results['stock_per_capita'].mean():>8.2f} tons/person")
    print(f"Median per capita stock: {spatial_results['stock_per_capita'].median():>8.2f} tons/person")
    print(f"Std dev per capita:      {spatial_results['stock_per_capita'].std():>8.2f} tons/person")
    print(f"Min per capita:          {spatial_results['stock_per_capita'].min():>8.2f} tons/person ({spatial_results.loc[spatial_results['stock_per_capita'].idxmin(), 'state']})")
    print(f"Max per capita:          {spatial_results['stock_per_capita'].max():>8.2f} tons/person ({spatial_results.loc[spatial_results['stock_per_capita'].idxmax(), 'state']})")
    
    print("\n--- REGIONAL CONCENTRATION ---")
    total_stock = spatial_results['total_stock'].sum()
    top3_share = spatial_results.nlargest(3, 'total_stock')['total_stock'].sum() / total_stock
    top5_share = spatial_results.nlargest(5, 'total_stock')['total_stock'].sum() / total_stock
    print(f"Top 3 states account for: {top3_share*100:.1f}% of national stock")
    print(f"Top 5 states account for: {top5_share*100:.1f}% of national stock")
    
    print("="*80 + "\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Demonstrate spatial allocation.
    """
    print("="*80)
    print("SPATIAL CONCRETE STOCK ALLOCATION - DEMONSTRATION")
    print("="*80)
    
    # Example national stocks from top-down model
    # (These would come from running the main top-down model)
    national_stocks = {
        'residential': 3000,      # million metric tons
        'commercial': 1200,
        'institutional': 600,
        'industrial': 400,
        'total': 5200
    }
    
    print("\n1. Loading spatial proxy data...")
    proxy_data = load_spatial_proxy_data(method='state')
    print(f"   Loaded data for {len(proxy_data)} states")
    
    print("\n2. Allocating national stock spatially...")
    spatial_results = allocate_national_stock(
        national_stocks,
        proxy_data,
        method='hybrid'  # Try: 'population', 'gdp', 'floor_area', 'hybrid'
    )
    
    print("\n3. Calculating spatial statistics...")
    print_spatial_summary(spatial_results)
    
    print("4. Creating visualizations...")
    plot_spatial_distribution(spatial_results)
    
    # Save results
    output_file = 'spatial_concrete_stock_results.csv'
    spatial_results.to_csv(output_file, index=False)
    print(f"\n5. Saved detailed results to {output_file}")
    
    print("\n" + "="*80)
    print("SPATIAL ALLOCATION COMPLETE")
    print("="*80)
    
    return spatial_results


if __name__ == "__main__":
    results = main()
