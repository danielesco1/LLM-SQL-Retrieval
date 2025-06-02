import sqlite3
import pandas as pd
from pathlib import Path

def file_to_sqlite(file_path, db_path):
    conn = sqlite3.connect(db_path)
    # Drop all existing tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for table in cursor.fetchall():
        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
    
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.csv':
        df = pd.read_csv(file_path)
        table_name = Path(file_path).stem
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"Created table '{table_name}' with {len(df)} rows")
    elif file_ext in ['.xlsx', '.xls']:
        for sheet_name, df in pd.read_excel(file_path, sheet_name=None).items():
            df.to_sql(sheet_name, conn, if_exists='replace', index=False)
            print(f"Created table '{sheet_name}' with {len(df)} rows")
    
    conn.close()

def verify_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"Table '{table[0]}': {count} rows")
    
    conn.close()

# Usage
file_to_sqlite('sql/building_panels.csv', 'sql/building_panels-database1.db')
verify_database('sql/building_panels-database1.db')



# excel_file_path = 'sql/building_panels.xlsx'
# conn = sqlite3.connect(r'sql/building_panels-database.db')
# cursor = conn.cursor()


# def drop_all_tables(cursor):
#     # Query to get all table names in the database
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#     tables = cursor.fetchall()
    
#     # Drop each table
#     for table_name in tables:
#         cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]}")

# drop_all_tables(cursor)
# print("Existing tables have been dropped.")

# # Load the Excel file, get a dictionary of DataFrames, one per sheet
# sheets_dict = pd.read_excel(excel_file_path, sheet_name=None)

# # Iterate over each sheet in the Excel file
# for sheet_name, df in sheets_dict.items():
#     # Get column names and types from the DataFrame
#     columns =df.columns.str.strip()
#     types = df.dtypes

#     # Create a SQL command to create a table dynamically
#     column_defs = []
#     for col, dtype in zip(columns, types):
#         if pd.api.types.is_integer_dtype(dtype):
#             col_type = 'INTEGER'
#         elif pd.api.types.is_float_dtype(dtype):
#             col_type = 'REAL'
#         else:
#             col_type = 'TEXT'
#         column_defs.append(f'"{col}" {col_type}')

#     column_defs_str = ', '.join(column_defs)
#     create_table_sql = f'CREATE TABLE IF NOT EXISTS {sheet_name} ({column_defs_str})'

#     # Execute the SQL command to create the table
#     cursor.execute(create_table_sql)

#     # Insert DataFrame into SQLite database
#     df.to_sql(sheet_name, conn, if_exists='append', index=False)

#     print(f"Data from sheet '{sheet_name}' inserted into table '{sheet_name}'.")

# # Verify data
# # print("Verifying...")
# # for sheet_name in sheets_dict.keys():
# #     cursor.execute(f'SELECT * FROM {sheet_name}')
# #     rows = cursor.fetchall()
# #     print(f"\nData from table '{sheet_name}':")
# #     for row in rows:
# #         print(row)

# # Close the connection
# conn.close()