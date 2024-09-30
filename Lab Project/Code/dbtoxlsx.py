import sqlite3
import pandas as pd

def export_db_to_excel(db_path, table_name, output_excel_path):
    # Create a connection to the SQLite database
    conn = sqlite3.connect(db_path)

    # Read data from SQLite into a DataFrame
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, conn)

    # Export the DataFrame to an Excel file
    df.to_excel(output_excel_path, index=False)

    # Close the database connection
    conn.close()

    print(f"Data exported successfully to {output_excel_path}")

# Replace 'weather_data.db' with your database file path
# Replace 'weather_data' with your table name
# Specify the path for your new Excel file
if __name__ == "__main__":
    export_db_to_excel('weather_data.db', 'weather_data', 'weather_data1.xlsx')
