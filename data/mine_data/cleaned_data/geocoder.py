# geocoding script to convert addresses into long/lats

import pandas as pd
import requests
import time
from tqdm import tqdm

INPUT_FILE = "mine_data/cleaned_data/US-DOL-Cleaned-Sand-Mine-Addresses_12072025.csv"
OUTPUT_FILE = "mine_data/cleaned_data/mine_addresses_with_coords_12072025.csv"
ADDRESS_COLS = ["Street", "City", "State", "Zip Code"]
SLEEP_TIME = 0.1  # seconds between API calls

def join_address(row):
    return f"{row['Street']}, {row['City']}, {row['State']} {row['Zip Code']}"

# api caller
def census_geocode(address, retries=3):
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    params = {
        "address": address,
        "benchmark": "Public_AR_Current",
        "format": "json"
    }

    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()

            matches = data.get("result", {}).get("addressMatches", [])
            if len(matches) > 0:
                coords = matches[0]["coordinates"]
                return coords["y"], coords["x"]  # lat, lon
            else:
                return None, None

        except Exception:
            if attempt < retries - 1:
                time.sleep(1)  # retry delay
                continue
            return None, None

def main():

    print("\n Loading input CSV…")
    df = pd.read_csv(INPUT_FILE)

    # Ensure required columns exist
    for col in ADDRESS_COLS:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    print("Building full address strings…")
    df["full_address"] = df.apply(join_address, axis=1)

    # Storage lists
    lats = []
    lons = []

    print("\n Geocoding addresses using Census API…\n")

    for addr in tqdm(df["full_address"], total=len(df)):
        lat, lon = census_geocode(addr)
        lats.append(lat)
        lons.append(lon)
        time.sleep(SLEEP_TIME)

    df["lat"] = lats
    df["lon"] = lons

    print("\n Saving output CSV…")
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n Done! Geocoded file saved to: {OUTPUT_FILE}\n")


if __name__ == "__main__":
    main()