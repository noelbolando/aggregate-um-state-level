"""
Top-Down Concrete Stock Estimation for US Buildings
===================================================

This script estimates the cumulative concrete stock in US buildings using:
1. Historical cement production data (USGS)
2. Construction spending allocation (Census Bureau)
3. Building lifetime distributions
4. Material flow analysis (stock-flow modeling)

Approach: Stock = Σ[Inflow(t) × Survival(year, t)]
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import weibull_min, norm
from typing import Dict, Tuple

# ============================================================================
# CONFIGURATION PARAMETERS
# ============================================================================

# Current analysis year
CURRENT_YEAR = 2024

# Building lifetime parameters (in years)
LIFETIMES = {
    'residential': {'mean': 70, 'std': 20},      # Single family, multi-family
    'commercial': {'mean': 60, 'std': 15},       # Office, retail, warehouse
    'institutional': {'mean': 75, 'std': 20},    # Schools, hospitals
    'industrial': {'mean': 50, 'std': 15}        # Factories, manufacturing
}

# Concrete content by construction dollar (kg concrete per $ of construction)
# These are rough estimates - should be calibrated with literature
CONCRETE_INTENSITY_BY_DOLLAR = {
    'residential': 0.15,    # kg/$, lower for wood-frame construction
    'commercial': 0.25,     # kg/$, mid-rise with concrete structure
    'institutional': 0.30,  # kg/$, heavy institutional buildings
    'industrial': 0.20      # kg/$, varies widely by industry
}

# Allocation of cement to buildings vs infrastructure
# From literature: ~50-60% of cement goes to buildings
BUILDING_FRACTION = 0.55  # 55% to buildings, 45% to infrastructure

# Concrete to cement ratio (typically 1 ton cement makes ~5-6 tons of concrete)
CONCRETE_TO_CEMENT_RATIO = 5.5  # tons concrete per ton cement


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_usgs_cement_data() -> pd.DataFrame:
    """
    Load historical cement production data from USGS.
    
    For now, returns sample data. Replace with actual USGS data loading.
    Data source: https://www.usgs.gov/centers/national-minerals-information-center/cement-statistics-and-information
    
    Returns:
        DataFrame with columns: year, production_mt (million metric tons)
    """
    # Sample data from USGS Mineral Commodity Summaries
    # You should replace this with actual historical data
    sample_data = {
        'year': list(range(1950, 2025)),
        'production_mt': [
            # 1950s - post-WWII construction boom
            *[40 + i*1.5 for i in range(10)],
            # 1960s - sustained growth
            *[55 + i*2 for i in range(10)],
            # 1970s - oil crisis slowdown
            *[75 + i*0.5 for i in range(10)],
            # 1980s - recovery
            *[80 + i*1 for i in range(10)],
            # 1990s - strong growth
            *[90 + i*0.8 for i in range(10)],
            # 2000s - peak then recession
            *[98, 99.3, 97, 95, 94, 92, 90, 85, 75, 65],
            # 2010s - recovery
            *[66, 67, 71, 76, 81, 84, 86, 87, 88, 87],
            # 2020s - recent
            *[83, 90, 91, 93, 90]
        ]
    }
    
    df = pd.DataFrame(sample_data)
    print(f"Loaded cement production data for {len(df)} years")
    print(f"Total cumulative production: {df['production_mt'].sum():.1f} million metric tons")
    return df


def load_construction_spending() -> pd.DataFrame:
    """
    Load construction spending data from Census Bureau.
    
    For now, returns sample allocation factors. Replace with actual data.
    Data source: https://www.census.gov/construction/c30/historical_data.html
    
    Returns:
        DataFrame with allocation factors by building type
    """
    # Sample allocation factors (fraction of total building construction)
    # These should be calculated from actual Census spending data
    years = list(range(1950, 2025))
    
    # Simplified allocation - refine with actual data
    allocations = {
        'year': years,
        'residential_fraction': [0.60] * len(years),      # 60% residential
        'commercial_fraction': [0.25] * len(years),       # 25% commercial
        'institutional_fraction': [0.10] * len(years),    # 10% institutional
        'industrial_fraction': [0.05] * len(years)        # 5% industrial
    }
    
    df = pd.DataFrame(allocations)
    print(f"Loaded construction spending allocations for {len(df)} years")
    return df


# ============================================================================
# LIFETIME DISTRIBUTION FUNCTIONS
# ============================================================================

def survival_function(age: int, lifetime_params: Dict) -> float:
    """
    Calculate survival probability for a building of given age.
    
    Uses a normal distribution for building lifetime.
    Could also use Weibull distribution for more flexibility.
    
    Args:
        age: Age of building in years
        lifetime_params: Dict with 'mean' and 'std' for lifetime distribution
        
    Returns:
        Probability that building is still standing (0 to 1)
    """
    mean_life = lifetime_params['mean']
    std_life = lifetime_params['std']
    
    # Survival = P(lifetime > age) = 1 - CDF(age)
    survival_prob = 1 - norm.cdf(age, loc=mean_life, scale=std_life)
    
    return max(0, survival_prob)  # Ensure non-negative


def calculate_survival_matrix(current_year: int, start_year: int,
                              lifetimes: Dict) -> pd.DataFrame:
    """
    Calculate survival probabilities for all years and building types.
    
    Args:
        current_year: Year to calculate stock for
        start_year: First year of data
        lifetimes: Dictionary of lifetime parameters by building type
        
    Returns:
        DataFrame with survival probabilities [year_built × building_type]
    """
    years = range(start_year, current_year + 1)
    survival_data = {}
    
    for building_type, life_params in lifetimes.items():
        survival_probs = []
        for year_built in years:
            age = current_year - year_built
            survival_probs.append(survival_function(age, life_params))
        survival_data[building_type] = survival_probs
    
    df = pd.DataFrame(survival_data, index=years)
    df.index.name = 'year_built'
    
    print(f"\nCalculated survival probabilities:")
    print(f"Example - building built in 1970 (age {current_year - 1970}):")
    for btype in lifetimes.keys():
        print(f"  {btype}: {df.loc[1970, btype]:.1%} survival probability")
    
    return df


# ============================================================================
# STOCK CALCULATION
# ============================================================================

def calculate_concrete_inflows(cement_data: pd.DataFrame,
                               spending_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate annual concrete inflows to different building types.
    
    Args:
        cement_data: Cement production by year
        spending_data: Construction spending allocations
        
    Returns:
        DataFrame with concrete inflows by year and building type (in million metric tons)
    """
    # Merge datasets
    df = cement_data.merge(spending_data, on='year')
    
    # Convert cement to concrete
    df['concrete_available_mt'] = df['production_mt'] * CONCRETE_TO_CEMENT_RATIO
    
    # Allocate to buildings (vs infrastructure)
    df['concrete_to_buildings_mt'] = df['concrete_available_mt'] * BUILDING_FRACTION
    
    # Allocate to building types based on spending fractions
    for btype in ['residential', 'commercial', 'institutional', 'industrial']:
        df[f'{btype}_concrete_mt'] = (
            df['concrete_to_buildings_mt'] * df[f'{btype}_fraction']
        )
    
    print(f"\nConcrete inflows calculated:")
    print(f"Average annual concrete to buildings: {df['concrete_to_buildings_mt'].mean():.1f} million metric tons")
    print(f"Peak year: {df.loc[df['concrete_to_buildings_mt'].idxmax(), 'year']} "
          f"({df['concrete_to_buildings_mt'].max():.1f} million metric tons)")
    
    return df


def calculate_stock(inflows: pd.DataFrame, survival_matrix: pd.DataFrame,
                   current_year: int) -> Dict:
    """
    Calculate current concrete stock by building type.
    
    Stock(year) = Σ[Inflow(t) × Survival(current_year, t)]
    
    Args:
        inflows: Concrete inflows by year and building type
        survival_matrix: Survival probabilities
        current_year: Year to calculate stock for
        
    Returns:
        Dictionary with stock estimates by building type
    """
    stocks = {}
    building_types = ['residential', 'commercial', 'institutional', 'industrial']
    
    for btype in building_types:
        # Get inflows and survival probabilities for this building type
        inflow_col = f'{btype}_concrete_mt'
        
        # Calculate stock: sum of (inflow × survival) for all past years
        stock = 0
        for year in inflows['year']:
            if year in survival_matrix.index:
                inflow = inflows.loc[inflows['year'] == year, inflow_col].values[0]
                survival = survival_matrix.loc[year, btype]
                stock += inflow * survival
        
        stocks[btype] = stock
    
    stocks['total'] = sum(stocks.values())
    
    return stocks


# ============================================================================
# ANALYSIS AND VISUALIZATION
# ============================================================================

def print_stock_summary(stocks: Dict, current_year: int):
    """Print formatted summary of stock estimates."""
    print(f"\n{'='*70}")
    print(f"CONCRETE STOCK IN US BUILDINGS - {current_year}")
    print(f"{'='*70}")
    print(f"\nBy Building Type:")
    print(f"  Residential:    {stocks['residential']:>10,.0f} million metric tons")
    print(f"  Commercial:     {stocks['commercial']:>10,.0f} million metric tons")
    print(f"  Institutional:  {stocks['institutional']:>10,.0f} million metric tons")
    print(f"  Industrial:     {stocks['industrial']:>10,.0f} million metric tons")
    print(f"  {'-'*60}")
    print(f"  TOTAL:          {stocks['total']:>10,.0f} million metric tons")
    print(f"\nPer Capita (assuming 335 million people):")
    per_capita_tons = (stocks['total'] * 1e6) / 335e6  # Convert million tons to tons per person
    print(f"  {per_capita_tons:>10,.1f} metric tons per person")
    print(f"{'='*70}\n")


def calculate_stock_timeseries(inflows: pd.DataFrame, survival_matrix: pd.DataFrame,
                               start_year: int, end_year: int) -> pd.DataFrame:
    """Calculate stock for each year in the time series."""
    years = range(start_year, end_year + 1)
    building_types = ['residential', 'commercial', 'institutional', 'industrial']
    
    results = []
    for year in years:
        year_stocks = {'year': year}
        
        for btype in building_types:
            inflow_col = f'{btype}_concrete_mt'
            stock = 0
            
            # Sum contributions from all past years still standing
            for built_year in inflows['year']:
                if built_year <= year:
                    age = year - built_year
                    inflow = inflows.loc[inflows['year'] == built_year, inflow_col].values[0]
                    # Recalculate survival for this specific year
                    survival = survival_function(age, LIFETIMES[btype])
                    stock += inflow * survival
            
            year_stocks[btype] = stock
        
        year_stocks['total'] = sum(year_stocks[k] for k in building_types)
        results.append(year_stocks)
    
    return pd.DataFrame(results)


def plot_results(stock_timeseries: pd.DataFrame, inflows: pd.DataFrame):
    """Create visualization of results."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Stock over time
    ax = axes[0, 0]
    building_types = ['residential', 'commercial', 'institutional', 'industrial']
    for btype in building_types:
        ax.plot(stock_timeseries['year'], stock_timeseries[btype], 
               label=btype.capitalize(), linewidth=2)
    ax.set_xlabel('Year')
    ax.set_ylabel('Concrete Stock (million metric tons)')
    ax.set_title('Concrete Stock in US Buildings Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Stock composition (pie chart for current year)
    ax = axes[0, 1]
    latest = stock_timeseries.iloc[-1]
    sizes = [latest[bt] for bt in building_types]
    ax.pie(sizes, labels=[bt.capitalize() for bt in building_types],
           autopct='%1.1f%%', startangle=90)
    ax.set_title(f'Stock Composition ({int(latest["year"])})')
    
    # Plot 3: Annual inflows
    ax = axes[1, 0]
    ax.plot(inflows['year'], inflows['concrete_to_buildings_mt'],
            linewidth=2, color='darkgreen')
    ax.set_xlabel('Year')
    ax.set_ylabel('Concrete Inflow (million metric tons/year)')
    ax.set_title('Annual Concrete Inflow to Buildings')
    ax.grid(True, alpha=0.3)
    
    # Plot 4: Growth rate of total stock
    ax = axes[1, 1]
    growth_rate = stock_timeseries['total'].pct_change() * 100
    ax.plot(stock_timeseries['year'][1:], growth_rate[1:],
            linewidth=2, color='steelblue')
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual Growth Rate (%)')
    ax.set_title('Stock Growth Rate')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('concrete_stock_analysis.png', dpi=300, bbox_inches='tight')
    print("Saved visualization to concrete_stock_analysis.png")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print("=" * 70)
    print("TOP-DOWN CONCRETE STOCK ESTIMATION FOR US BUILDINGS")
    print("=" * 70)
    
    # Load data
    print("\n1. Loading data...")
    cement_data = load_usgs_cement_data()
    spending_data = load_construction_spending()
    
    # Calculate survival probabilities
    print("\n2. Calculating building survival probabilities...")
    start_year = cement_data['year'].min()
    survival_matrix = calculate_survival_matrix(CURRENT_YEAR, start_year, LIFETIMES)
    
    # Calculate concrete inflows
    print("\n3. Calculating concrete inflows to buildings...")
    inflows = calculate_concrete_inflows(cement_data, spending_data)
    
    # Calculate current stock
    print("\n4. Calculating current concrete stock...")
    stocks = calculate_stock(inflows, survival_matrix, CURRENT_YEAR)
    
    # Print results
    print_stock_summary(stocks, CURRENT_YEAR)
    
    # Calculate time series
    print("5. Calculating historical stock time series...")
    stock_timeseries = calculate_stock_timeseries(inflows, survival_matrix, 
                                                   start_year, CURRENT_YEAR)
    
    # Create visualizations
    print("\n6. Creating visualizations...")
    plot_results(stock_timeseries, inflows)
    
    # Save detailed results
    output_file = 'concrete_stock_results.csv'
    stock_timeseries.to_csv(output_file, index=False)
    print(f"\nSaved detailed results to {output_file}")
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    
    return stocks, stock_timeseries, inflows


if __name__ == "__main__":
    stocks, stock_timeseries, inflows = main()
