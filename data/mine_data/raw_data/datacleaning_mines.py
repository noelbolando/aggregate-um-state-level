# just a little script to clean a little data

###
#== US Department of Labor Sand Mine Data
#== Source: https://www.msha.gov/data-and-reports/mine-data-retrieval-system 
#== Notes: This data only includes commodities with NEC codes 144200 and 144201
###
#== This data contains the addresses for all active sand mines across the US
#== Downloaded: 12/07/2025
###

# bring in the data
import pandas as pd
# data on all mines (active and abandoned)
all_mines_df = pd.read_csv('mine_data/raw_data/US-DOL-All-Sand-Mines_12072025.csv')
# address data on all mines (active and abandoned)
all_mines_addresses_df = pd.read_csv('mine_data/raw_data/US-DOL-All-Sand-Mines-Address_12072025.csv')

# join on mine id
raw_mine_location_data = pd.merge(all_mines_df, all_mines_addresses_df, on='Mine ID', how='inner')
print(raw_mine_location_data.head())

# get mine status to see how many abandoned mines we have
mine_status_counts = raw_mine_location_data['Mine Status'].value_counts()
print(mine_status_counts)

# see how many missing addresses we have
missing_values_per_column = raw_mine_location_data.isnull().sum()
print("Missing values per column:")
print(missing_values_per_column)

# see how many missing addresses align with abandoned mines
pivot_point = 'Abandoned'
missing_street_address = raw_mine_location_data['Street'].isna()
abandoned_mines = raw_mine_location_data['Mine Status'] == pivot_point
combined_condition = missing_street_address & abandoned_mines
count = combined_condition.sum()
print(count)

# drop all the empty addresses
cleaned_mine_location_data = raw_mine_location_data.dropna(subset=['Street'])
print(cleaned_mine_location_data)

# check mine status again to see how many abandoned mines we have
mine_status_counts = cleaned_mine_location_data['Mine Status'].value_counts()
print(mine_status_counts)

# grab the address fields so we can clean them next
keep_them = ['Mine ID', 'Street', 'City', 'State', 'Zip Code']
mine_address_data = cleaned_mine_location_data[keep_them]
print(mine_address_data)

# combine the address fields into a single string
mine_address_data['full_address'] = (
    mine_address_data['State'] + ", " + 
    mine_address_data['City'] + ", " + 
    mine_address_data['State'] + " " + 
    mine_address_data['Zip Code'].astype(str)
)
print(mine_address_data)   
