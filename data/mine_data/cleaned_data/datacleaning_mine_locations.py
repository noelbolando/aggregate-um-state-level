# after running geocoder, use this script to drop all missing coordinates and abandoned mines

###
#== US Department of Labor Sand Mine Data
#== Source: https://www.msha.gov/data-and-reports/mine-data-retrieval-system 
#== Notes: I'm dropping all missing coordinate pairs and abandoned mines
###
#== This data contains the addresses for all active sand mines across the US
#== Downloaded: 12/07/2025
###

# bring in it
import pandas as pd
geocoded_mine_location_data = pd.read_csv('mine_data/cleaned_data/mine_addresses_with_coords_12072025.csv')
print(geocoded_mine_location_data)

# drop abandoned mines
drop_abandoned_mines = geocoded_mine_location_data[~geocoded_mine_location_data['Mine Status'].str.contains('Abandoned', case=False, na=False)]
print(drop_abandoned_mines)

# drop missing lat/long
drop_nan_coords = drop_abandoned_mines.dropna(subset=['lat', 'lon'])
print(drop_nan_coords)

# drop the columns we don't need
keep_them = ['Mine ID', 'Mine Name_x', 'Mine Status', 'Type of Mine', 'Street', 'City', 'State', 'Zip Code', 'lat', 'lon']
cleaned_mine_location_data = drop_nan_coords[keep_them]

# rename columns
cleaned_mine_location_data = cleaned_mine_location_data.rename(columns={'Mine Name_x': 'Mine Name', 'lat': 'Latitude', 'lon': 'Longitude'})
print(cleaned_mine_location_data)

# export the final cleaned df to a csv
cleaned_mine_location_data.to_csv('mine_data/cleaned_data/all_mine_locations-12_8_2025.csv', index=False)
