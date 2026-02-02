# lets consume some clean sand. data. clean sand data.

###
#== USGS Construction Sand and Gravel Data - US Historical Data 1902-2022
#== Source: https://www.usgs.gov/media/files/construction-sand-and-gravel-historical-statistics-data-series-140
#== Notes: contains production, import, export, and apparent consumption for US
###
#== This data includes production and consumption for the US from 1902-2022
#== Downloaded: 12/08/2025
###

# yay data!
import pandas as pd
raw_consumption_data = pd.read_csv('consumption_data/raw_data/ds140-construction_sand_and_gravel_consumption_1902_2022-12082025.csv')
print(raw_consumption_data)

# looks like we have a bunch of empty columns (?) so lets drop them
keep_them = ['Year', 'Production', 'Imports', 'Exports', 'Apparent consumption']
filtered_consumption_data = raw_consumption_data[keep_them]
print(filtered_consumption_data)

# drop any records with missing years
consumption_all_years = filtered_consumption_data.dropna(subset=['Year'])
print(consumption_all_years)

# replace NaN in import and exports columns to 0 for comma handling
cleaned_consumption_data = consumption_all_years.fillna(0)
print(cleaned_consumption_data)

# finally, remove commas from production, imports, exports, and apparent consumption
cleaned_consumption_data['Production'] = cleaned_consumption_data['Production'].replace(',', '', regex=True).astype(float)
cleaned_consumption_data['Imports'] = cleaned_consumption_data['Imports'].replace(',', '', regex=True).astype(float)
cleaned_consumption_data['Exports'] = cleaned_consumption_data['Exports'].replace(',', '', regex=True).astype(float)
cleaned_consumption_data['Apparent consumption'] = cleaned_consumption_data['Apparent consumption'].replace(',', '', regex=True).astype(float)
print(cleaned_consumption_data)

# export clean data to a csv
cleaned_consumption_data.to_csv('consumption_data/cleaned_data/sand_consumption_1902_2022-12092025.csv', index=False)
