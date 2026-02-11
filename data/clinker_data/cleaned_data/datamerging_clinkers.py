# gonna merge all the cleaned data into a single file

###
#== EPA GHG Reporting Program Data Sets
#== Source: https://www.epa.gov/ghgreporting/archive-ghg-reporting-program-data-sets
#== Notes: I'm merging all the cleaned clinker data into one csv based on the year
###
#== This data contains the addresses, long/lat, and cement production for all cement producers in the US
#== Downloaded: 12/08/2025
###

# bring it all in
import pandas as pd
import glob
import re
# get the files
files = glob.glob("clinker_data/cleaned_data/*.csv")

dfs = []
# useing regex to get the year from the filename to add to the appended df
for f in files:
    match = re.search(r"cement_production_(\d{4})", f)
    
    if match is None:
        print("Couldn't extract year from:", f)
        continue
    year = int(match.group(1))
    df = pd.read_csv(f)
    df["year"] = year
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)
print(df_all)
df_all.to_csv('clinker_data/cleaned_data/all_cement_production_2010_to_2021-02_11_2026.csv', index=False)
