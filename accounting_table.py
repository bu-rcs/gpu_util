import os
import pandas as pd

def accounting_table(year):
    my_path = '/projectnb/rcsmetrics/accounting/data/scc/'
    
    # Reverse index like in MATLAB (2024 - year)
    year_offset = 2024 - year

    # List all .csv files in the directory
    csv_files = sorted(
        [f for f in os.listdir(my_path) if f.endswith('.csv')]
    )

    if not csv_files or year_offset >= len(csv_files):
        raise IndexError("Requested year index is out of range.")

    the_file = os.path.join(my_path, csv_files[-(year_offset + 1)])

    # Define column dtypes (to match MATLAB opts)
    dtype_mapping = {
        4: 'string',    # Column 5 (0-based index 4)
        5: 'string',    # Column 17 (0-based index 16)
        5: 'int32', 6: 'int32', 7: 'int32',  # Columns 6-8 (5-7)
        10: 'int32', 11: 'int32', 12: 'int32',  # Columns 11-13 (10-12)
        8: 'uint8', 9: 'uint8',  # Columns 9-10 (8-9)
        15: 'int16',  # Column 16 (15)
        20: 'int64',  # Column 21 (20)
    }

    # Read CSV with automatic header
    df = pd.read_csv(the_file)

    # Apply type conversions selectively
    for col_idx, col_type in dtype_mapping.items():
        if col_idx < len(df.columns):
            df.iloc[:, col_idx] = df.iloc[:, col_idx].astype(col_type)

    return df
