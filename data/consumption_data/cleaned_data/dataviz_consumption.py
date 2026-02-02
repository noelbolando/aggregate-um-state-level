# make a few pretty graphs to visualize the consumption data

import pandas as pd
import matplotlib.pyplot as plt

# load it up
df = pd.read_csv("consumption_data/cleaned_data/sand_consumption_1902_2022-12092025.csv")

import matplotlib.pyplot as plt

# make sure the year is numeric
df["Year"] = df["Year"].astype(int)

plt.figure(figsize=(10,5))

# plot!
plt.plot(df["Year"], df["Apparent consumption"], label="Apparent Consumption")
plt.plot(df["Year"], df["Production"], label="Production")

plt.xlabel("Year")
plt.ylabel("Metric Tons")
plt.title("US Sand Production vs. Apparent Consumption Over Time")
plt.legend()
plt.tight_layout()
plt.show()

df["gap"] = df["Apparent consumption"] - df["Production"]

plt.figure(figsize=(10,5))
plt.plot(df["Year"], df["gap"], linewidth=2, label="Consumption - Production")
plt.plot(df["Year"], df["Exports"], label="Exports")
plt.plot(df["Year"], df["Imports"], label="Imports")
plt.axhline(0, color="black", linewidth=1)
plt.xlabel("Year")
plt.ylabel("Consumption minus Production")
plt.title("Difference Between Apparent Consumption and Production")
plt.legend()
plt.tight_layout()
plt.show()

df_norm = df.copy()
df_norm["cons_norm"] = df["Apparent consumption"] / df["Apparent consumption"].iloc[0] * 100
df_norm["prod_norm"]  = df["Production"] / df["Production"].iloc[0] * 100
