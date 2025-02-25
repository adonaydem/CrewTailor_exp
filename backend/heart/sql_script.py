import sqlite3
import csv
from io import StringIO

def process_csv_to_sqlite(csv_string, table_name, db_name=":memory:"):
    """
    Accepts a CSV-style string, a table name, and processes it into an SQLite database.

    Args:
        csv_string (str): The CSV-formatted string.
        table_name (str): The name of the table to create and populate.
        db_name (str): SQLite database name. Defaults to in-memory database.

    Returns:
        None
    """
    import os

    # Connect to the SQLite database
    db_name = os.path.join(os.getcwd(), db_name)
    if os.path.exists(db_name):
        print("yes")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Parse the CSV string
    csv_data = StringIO(csv_string)
    reader = csv.reader(csv_data)
    rows = list(reader)

    if not rows:
        print("CSV data is empty.")
        return

    print("Rows:", rows)
    # Extract headers and data
    headers = rows[0]
    data = rows[1:]

    # Generate the SQL for table creation
    columns = ', '.join([f'"{header}" TEXT' for header in headers])
    create_table_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns});'
    print("CRRRRR",create_table_query)
    cursor.execute(create_table_query)

    # Generate the SQL for inserting data
    placeholders = ', '.join(['?' for _ in headers])
    insert_query = f'INSERT INTO "{table_name}" VALUES ({placeholders});'

    # Insert data into the table
    cursor.executemany(insert_query, data)

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print(f"Data successfully inserted into the table '{table_name}'.")

# Example usage
csv_input = """Sector Name,Region,Annual Growth Rate (%),Demand Index,Market Saturation (%),Revenue Forecast (in millions),Historical Growth Patterns
Renewable Energy,South Korea,10.28,60.88,30.76,73.84,5Y: 16.043754267173853% CAGR
Manufacturing,India,10.08,86.87,64.41,146.09,5Y: 18.62135739872638% CAGR
Tech,Indonesia,15.52,68.7,58.42,288.67,5Y: 17.325206119480363% CAGR
Tech,India,22.81,72.96,46.39,71.09,5Y: 17.22604513764881% CAGR
Manufacturing,South Korea,23.47,78.25,64.34,361.45,5Y: 22.708590656546416% CAGR
Automotive,South Korea,14.83,64.3,15.5,94.16,5Y: 17.553296481522203% CAGR
Agriculture,Singapore,19.06,92.15,66.13,334.41,5Y: 21.901151132778324% CAGR
Renewable Energy,China,26.75,89.28,44.49,349.94,5Y: 15.481179288664784% CAGR
Healthcare,Singapore,11.18,84.79,20.93,472.38,5Y: 14.118360517464561% CAGR
Manufacturing,Singapore,25.19,96.11,29.92,134.88,5Y: 21.582262177243862% CAGR
Manufacturing,Singapore,16.77,77.17,76.18,210.13,5Y: 15.87755217796658% CAGR
Manufacturing,Indonesia,13.8,74.0,14.8,261.27,5Y: 18.36370064522101% CAGR
Manufacturing,South Korea,26.75,92.6,50.57,63.17,5Y: 17.969794828571374% CAGR
Renewable Energy,Singapore,19.28,65.29,47.87,355.06,5Y: 22.515783371623044% CAGR
Agriculture,China,25.94,86.54,49.03,220.61,5Y: 13.501548858268116% CAGR
Automotive,India,15.08,91.85,60.91,427.08,5Y: 21.448563614806975% CAGR
Healthcare,Singapore,29.44,61.73,42.84,333.06,5Y: 21.26177319002963% CAGR
Manufacturing,Indonesia,19.63,61.13,69.87,479.31,5Y: 12.944358502225757% CAGR
Agriculture,India,25.62,79.5,78.69,493.06,5Y: 20.536869487141587% CAGR
Automotive,China,19.49,91.72,49.74,229.77,5Y: 12.86287514134548% CAGR
Renewable Energy,Indonesia,26.41,97.08,69.13,283.2,5Y: 24.121814960625848% CAGR
Healthcare,South Korea,28.52,61.42,46.17,186.69,5Y: 12.306344925753315% CAGR
Renewable Energy,Japan,29.63,86.91,51.36,287.77,5Y: 13.149108685261488% CAGR
Renewable Energy,South Korea,11.94,92.14,75.16,160.45,5Y: 17.964615821024992% CAGR
Healthcare,Singapore,6.04,73.94,23.57,173.64,5Y: 24.62718895054006% CAGR
"""

table_name = "sector_market"

process_csv_to_sqlite(csv_input, table_name, db_name="dbs/CW6PSVSxgsZFOql56bc92ryeU3L2/6764295c336498812fe8b630.db")