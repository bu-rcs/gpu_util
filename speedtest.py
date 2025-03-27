import time
import pandas as pd

# Import the non-parallel and parallel versions of the function
from helpers import process_gpu_data as process_gpu_data_non_parallel
from helpers_parallel import process_gpu_data as process_gpu_data_parallel
from helpers import aggregate_gpu_data as aggregate_gpu_data_non_parallel
from helpers_parallel import aggregate_gpu_data as aggregate_gpu_data_parallel

# Define a function to test the processing time of both versions
def test_processing_time(year: str, month: str):
    # Test the non-parallel version
    start_time = time.time()
    print("Running non-parallel version (monthly)...")
    result_non_parallel = process_gpu_data_non_parallel(year, month)
    end_time = time.time()
    non_parallel_time = end_time - start_time
    print(f"Non-parallel processing took {non_parallel_time:.2f} seconds.")

    # Test the parallel version
    start_time = time.time()
    print("Running parallel version (monthly)...")
    result_parallel = process_gpu_data_parallel(year, month)
    end_time = time.time()
    parallel_time = end_time - start_time
    print(f"Parallel processing took {parallel_time:.2f} seconds.")

    # Optionally, you can check if both results are the same
    if result_non_parallel.equals(result_parallel):
        print("Both parallel and non-parallel results are the same.")
    else:
        print("Results differ between parallel and non-parallel versions.")

    return non_parallel_time, parallel_time

# Define a function to test the aggregate_gpu_data function for the entire year
def test_aggregate_gpu_data(year: str):
    # Test the non-parallel version (aggregating data for all months in the year)
    start_time = time.time()
    print(f"Running non-parallel version (yearly) for {year}...")
    result_non_parallel_year = aggregate_gpu_data_non_parallel(year)
    end_time = time.time()
    non_parallel_year_time = end_time - start_time
    print(f"Non-parallel yearly aggregation took {non_parallel_year_time:.2f} seconds.")

    # Test the parallel version (aggregating data for all months in the year)
    start_time = time.time()
    print(f"Running parallel version (yearly) for {year}...")
    result_parallel_year = aggregate_gpu_data_parallel(year)
    end_time = time.time()
    parallel_year_time = end_time - start_time
    print(f"Parallel yearly aggregation took {parallel_year_time:.2f} seconds.")

    # Optionally, check if the results are the same for yearly aggregation
    if result_non_parallel_year.equals(result_parallel_year):
        print("Both parallel and non-parallel yearly aggregation results are the same.")
    else:
        print("Yearly aggregation results differ between parallel and non-parallel versions.")

    return non_parallel_year_time, parallel_year_time

# Example usage of the test
if __name__ == "__main__":
    year = "24"  # Example year (2024)
    month = "01"  # Example month (January)

    # Call the function to test the time taken by both versions (monthly)
    print("Testing monthly function...")
    non_parallel_time, parallel_time = test_processing_time(year, month)

    # Call the function to test the time taken by both versions (yearly aggregation)
    print("\nTesting yearly aggregation function...")
    non_parallel_year_time, parallel_year_time = test_aggregate_gpu_data(year)

    # Print summary for both tests
    print(f"\nTest Summary:")
    print(f"Non-parallel monthly processing time: {non_parallel_time:.2f} seconds.")
    print(f"Parallel monthly processing time: {parallel_time:.2f} seconds.")
    print(f"Speedup for monthly processing: {non_parallel_time / parallel_time:.2f}x" if parallel_time != 0 else "Parallel version failed.")

    print(f"\nYearly Aggregation Test Summary:")
    print(f"Non-parallel yearly aggregation time: {non_parallel_year_time:.2f} seconds.")
    print(f"Parallel yearly aggregation time: {parallel_year_time:.2f} seconds.")
    print(f"Speedup for yearly aggregation: {non_parallel_year_time / parallel_year_time:.2f}x" if parallel_year_time != 0 else "Parallel version failed.")



# ==================== FOR 8 CORES ====================
#                   Monthly parallel
#
# Test Summary:
# Non-parallel monthly processing time: 48.85 seconds.
# Parallel monthly processing time: 25.69 seconds.
# Speedup for monthly processing: 1.90x

# Yearly Aggregation Test Summary:
# Non-parallel yearly aggregation time: 280.84 seconds.
# Parallel yearly aggregation time: 402.13 seconds.
# Speedup for yearly aggregation: 0.70x
# =====================================================