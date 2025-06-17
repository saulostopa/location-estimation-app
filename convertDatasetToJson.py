# To run this script, ensure you have pandas installed:
# pip install pandas
# Convertendo um dataset CSV para JSON
# This script converts a CSV dataset to a JSON format.
# On command line, run:
# python convertDatasetToJson.py

import pandas as pd

# Load the dataset
df = pd.read_csv("dataset.csv")

# Filter out rows with zero latitude or longitude
df = df[["Latitude", "Longitude", "UTCDateTime", "State"]]

# Remove rows with NaN values
df = df.dropna()

# Convert list of dictionaries to JSON format
records = df.to_dict(orient="records")

# Export the records to a JSON file
# Ensure the file is saved with UTF-8 encoding to handle special characters
import json
with open("dataset.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
