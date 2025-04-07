import subprocess
import sys
import pandas as pd
from io import StringIO
from datetime import datetime
import argparse

def read_user_records(start_date: str, end_date: str, username: str) -> pd.DataFrame:
    """
    Extracts rows where the 'user' column exactly matches a specified username from CSV files 
    within a given date range. It processes multiple years based on the range. Jobs are included
    if they ended during that time.

    Args:
        start_date (str): Start date in "YYYY-MM-DD" format.
        end_date (str): End date in "YYYY-MM-DD" format.
        username (str): The username to filter for.

    Returns:
        pd.DataFrame: A DataFrame containing only rows where the 'user' column matches the given username 
                      and the 'ux_end_time' column falls within the specified date range.

    Raises:
        ValueError: If date formats are incorrect.
        FileNotFoundError: If a file for a particular year does not exist.
        PermissionError: If a file cannot be accessed due to permission issues.
        subprocess.CalledProcessError: If an error occurs while executing the grep command.
    """
    try:
        # Convert start and end dates to datetime objects
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Validate date range
        if start_dt > end_dt:
            raise ValueError("Start date must be before or equal to end date.")

        # Generate list of years to process
        years_to_load = list(range(start_dt.year, end_dt.year + 1))

        all_dfs = []  # List to store DataFrames

        for year in years_to_load:
            filepath = f"/projectnb/rcsmetrics/accounting/data/scc/{year}.csv"

            try:
                # Run grep command to filter rows containing the username
                result = subprocess.run(
                    ["grep", "-e", username, filepath],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                # Extract header from the first row of the file
                with open(filepath, "r", encoding="utf-8") as file:
                    header = next(file).strip().split(",")

                # Convert grep output to a DataFrame
                df = pd.read_csv(StringIO(result.stdout), names=header, quotechar='"')

                # Ensure 'user' column exists and filter for exact matches
                if "user" in df.columns:
                    df = df[df["user"] == username]

                # Convert 'ux_end_time' column to datetime
                if "ux_end_time" in df.columns:
                    df["time"] = pd.to_datetime(df["ux_end_time"], unit="s")

                # Append processed DataFrame
                all_dfs.append(df)

            except FileNotFoundError:
                print(f"Warning: File not found for year {year}, skipping.")
                continue
            except PermissionError:
                print(f"Warning: Permission denied for file {filepath}, skipping.")
                continue
            except subprocess.CalledProcessError:
                print(f"Warning: No matching records found in {filepath}, skipping.")
                continue
            except pd.errors.EmptyDataError:
                print(f"Warning: Empty data in {filepath}, skipping.")
                continue

        # Concatenate all DataFrames and filter final range
        final_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

        if not final_df.empty and "time" in final_df.columns:
            final_df = final_df[(final_df["time"] >= start_dt) & (final_df["time"] <= end_dt)]

        return final_df

    except ValueError as e:
        raise ValueError(f"Date format error: {e}")


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Extract GPU job records for a specific user within a date range."
    )
    parser.add_argument(
        "start_date", type=str, help="Start date in YYYY-MM-DD format."
    )
    parser.add_argument(
        "end_date", type=str, help="End date in YYYY-MM-DD format."
    )
    parser.add_argument(
        "username", type=str, help="Username to filter records."
    )
    parser.add_argument(
        "--output", "-o", type=str, help="Optional: Output CSV file to save results."
    )

    # Parse arguments
    args = parser.parse_args()

    try:
        # Call function to get records
        df = read_user_records(args.start_date, args.end_date, args.username)

        if df.empty:
            print("No records found for the given criteria.")
            sys.exit(0)

        # Print result summary
        print(f"Loaded {len(df)} records for user '{args.username}' from {args.start_date} to {args.end_date}.")
        print(df.head())  # Print first few rows

        # Save to CSV if requested
        if args.output:
            df.to_csv(args.output, index=False)
            print(f"Results saved to {args.output}")

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
