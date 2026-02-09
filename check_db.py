import sqlite3
import pandas as pd
from rich import _console

def export_to_csv(db_path="scholar_data.db", output_file="my_papers.csv"):
    conn = sqlite3.connect(db_path)

    df = pd.read_sql_query("SELECT * FROM papers", conn)

    print(df.head(10))

    df.to_csv(output_file, index=False)
    _console.print(f"\n[bold green]Exported data to '{output_file}'")

    conn.close()