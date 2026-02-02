# pretty pics to tell a story

import pandas as pd
import matplotlib.pyplot as plt

# load it up
df = pd.read_csv("production_data/cleaned_data/sand_production_1971_2023-12082025.csv")

# make sure year is numeric
df["Year"] = df["Year"].astype(int)

# group by year and sum quantity
annual_totals = df.groupby("Year")["Quantity"].sum().reset_index()

# plot
plt.figure(figsize=(10,5))
plt.plot(annual_totals["Year"], annual_totals["Quantity"], label="Total US Quantity")

plt.xlabel("Year")
plt.ylabel("Quantity (tons)")
plt.title("US Sand Production Over Time")
plt.legend()
plt.tight_layout()
plt.show()
