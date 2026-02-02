### NOTE: not using this data for production, using the production values from the apparent consumption datasheet
# cleaning production data!

###
#== USGS 
#== Source: https://www.usgs.gov/index.php/media/files/usgs-aggregates-time-series-data-state-type-and-end-use 
#== Notes: this data has US- and state-level production data from 1971-2023, production in metric tons (t), value in $/t
###
#== Downloaded: 12/08/2025
###

# load it up
import pandas as pd
raw_prod_data = pd.read_csv('production_data/raw_data/USGS_Aggregates_Data_1971_2023-12082025.csv')
print(raw_prod_data)

# filter data for what we want
keep_them = ['Year', 'State Coverage', 'Region', 'Commodity', 'Quantity', 'Data Description', 'Total Value']
filtered_prod_data = raw_prod_data[keep_them]
print(filtered_prod_data)

# keep only state totals so as to not inflate the total values
filtered_prod_data = filtered_prod_data[filtered_prod_data['Data Description'] == 'State totals']
print(filtered_prod_data)

# drop the total commodity class since earlier years don't have this class
drop_comm = ['Aggregates, construction']
filtered_prod_data = filtered_prod_data[~filtered_prod_data['Commodity'].isin(drop_comm)]
print(filtered_prod_data)

# also drop any malformed production values ('W')
drop_malformed = ['W', '--']
filtered_prod_data = filtered_prod_data[~filtered_prod_data['Quantity'].isin(drop_malformed)]
print(filtered_prod_data)

# finally, drop US records (we only want state-level data)
state_level_prod_data = filtered_prod_data.dropna(subset=['Region'])
state_level_prod_data.to_csv('output.csv', index=False)

# clean up the data for summing - remove $ and commas from total value and convert to numeric type
state_level_prod_data['Total Value'] = state_level_prod_data['Total Value'].replace('[\$,]', '', regex=True).astype(float)
# also remove the commas from quantity
state_level_prod_data['Quantity'] = state_level_prod_data['Quantity'].replace(',', '', regex=True).astype(float)
print(state_level_prod_data)

# group by year, state, and region to sum production quantity and total value
agg_df = state_level_prod_data.groupby(['Year', 'State Coverage', 'Region'], as_index=False).agg({
    'Quantity': 'sum',
    'Total Value': 'sum'
    }
)
print(agg_df)

# export clean data to a csv
agg_df.to_csv('production_data/cleaned_data/sand_production_1971_2023-12082025.csv', index=False)
