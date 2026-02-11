# clinkers are dirty, but their data doesn't have to be!

###
#== EPA GHG Reporting Program Data Sets
#== Source: https://www.epa.gov/ghgreporting/archive-ghg-reporting-program-data-sets
#== Notes: this dataset contains all GHG emitter industries, will need to filter for cement producers
###
#== This data contains the addresses, long/lat, and cement production for all cement producers in the US
#== Downloaded: 12/08/2025
###

# bring it all in
import pandas as pd
raw_ghgp_data = pd.read_csv('clinker_data/raw_data/ghgp_data_2022-02_11_2026.csv')

# filter for industries with code 'H' (cement producers)
valid_industry_codes = ['C,H', 'H']
raw_cement_producer_data = raw_ghgp_data[raw_ghgp_data['Industry Type (subparts)'].isin(valid_industry_codes)]
print(raw_cement_producer_data)

# drop the columns we don't need
keep_them = ['Facility Id', 'Facility Name', 'City', 'State', 'Zip Code', 'Address', 'County', 'Latitude', 'Longitude', 'Primary NAICS Code', 'Cement Production']
cleaned_cement_producer_data = raw_cement_producer_data[keep_them]
print(cleaned_cement_producer_data)

# output the cleaned data to a csv
cleaned_cement_producer_data.to_csv('clinker_data/cleaned_data/cement_production_2022-02_11_2026.csv', index=False)
