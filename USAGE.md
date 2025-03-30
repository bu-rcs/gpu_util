# GPU Utilization Report Generator

This script generates a detailed GPU utilization report, including various analyses and visualizations of GPU usage patterns across different job types and execution modes. When a user and/or project is specified, a special page, Quick Stats, is generated and contains some key information about their GPU jobs. The report is saved as a PDF file.

## Prerequisites

- Python 3.x
- Required Python packages: pandas, matplotlib, seaborn

You can install the required packages using pip:

```sh
pip install pandas matplotlib seaborn
```

## Usage

To generate a GPU utilization report, run the script with the following command:

```sh
python gpu_utilization_report.py [OPTIONS]
```

### Options

- `-y`, `--year` (default: "25"): Year (last two digits, e.g., 25 for 2025)
- `-m`, `--month` (default: "02"): Month (two digits, e.g., 02 for February)
- `-o`, `--output` (default: "gpu_utilization_report.pdf"): Output PDF filename
- `-p`, `--project` (optional): Filter by project name
- `-u`, `--user` (optional): Filter by user name

### Example

Generate a report for February 2025 and save it as `gpu_report_february.pdf`:

```sh
python gpu_utilization_report.py -y 25 -m 02 -o gpu_report_february.pdf
```

Generate a report for January 2025, filtering by project name `project_xyz`:

```sh
python gpu_utilization_report.py -y 25 -m 01 -p project_xyz
```

Generate a report for March 2025, filtering by user name `john_doe`:

```sh
python gpu_utilization_report.py -y 25 -m 03 -u john_doe
```

## Description

The script performs the following steps:

1. Parses the command-line arguments to get the year, month, output filename, and optional filters for project and user.
2. Processes GPU data for the specified year and month.
3. Generates various visualizations, including GPU utilization trends, top users and projects by GPU utilization, and low GPU utilization patterns.
4. Saves the visualizations and analysis in a PDF report.
