import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect("scholar_harvest.db")

# Read data into a pandas DataFrame (makes it pretty)
df = pd.read_sql_query("SELECT * FROM papers", conn)

# Print the first 10 rows
print(df.head(10))

# Optional: Export to CSV if you want to open in Excel
df.to_csv("my_papers.csv", index=False)
print("\n✅ Exported data to 'my_papers.csv'")

conn.close()