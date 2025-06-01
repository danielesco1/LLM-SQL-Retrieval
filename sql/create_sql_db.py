import sqlite3
import pandas as pd


excel_file_path = 'sql/building_panels.xlsx'
conn = sqlite3.connect(r'sql/building_panels-database.db')
cursor = conn.cursor()


def drop_all_tables(cursor):
    # Query to get all table names in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    # Drop each table
    for table_name in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]}")

drop_all_tables(cursor)
print("Existing tables have been dropped.")

# Load the Excel file, get a dictionary of DataFrames, one per sheet
sheets_dict = pd.read_excel(excel_file_path, sheet_name=None)

# Iterate over each sheet in the Excel file
for sheet_name, df in sheets_dict.items():
    # Get column names and types from the DataFrame
    columns =df.columns.str.strip()
    types = df.dtypes

    # Create a SQL command to create a table dynamically
    column_defs = []
    for col, dtype in zip(columns, types):
        if pd.api.types.is_integer_dtype(dtype):
            col_type = 'INTEGER'
        elif pd.api.types.is_float_dtype(dtype):
            col_type = 'REAL'
        else:
            col_type = 'TEXT'
        column_defs.append(f'"{col}" {col_type}')

    column_defs_str = ', '.join(column_defs)
    create_table_sql = f'CREATE TABLE IF NOT EXISTS {sheet_name} ({column_defs_str})'

    # Execute the SQL command to create the table
    cursor.execute(create_table_sql)

    # Insert DataFrame into SQLite database
    df.to_sql(sheet_name, conn, if_exists='append', index=False)

    print(f"Data from sheet '{sheet_name}' inserted into table '{sheet_name}'.")

# Verify data
# print("Verifying...")
# for sheet_name in sheets_dict.keys():
#     cursor.execute(f'SELECT * FROM {sheet_name}')
#     rows = cursor.fetchall()
#     print(f"\nData from table '{sheet_name}':")
#     for row in rows:
#         print(row)

# Close the connection
conn.close()