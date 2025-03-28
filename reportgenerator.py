import argparse
from helpers import *
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import time
from datetime import datetime

import warnings
warnings.filterwarnings('ignore')

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate GPU utilization report')
    parser.add_argument('-y', '--year', type=str, default="25", 
                        help='Year (last two digits, e.g. 25)')
    parser.add_argument('-m', '--month', type=str, default="02", 
                    help='Month (two digits, e.g. 02)')
    parser.add_argument('-o', '--output', type=str, default="gpu_utilization_report.pdf", 
                    help='Output PDF filename')
    parser.add_argument('-p', '--project', type=str, default=None, 
                        help='Filter by project name (optional)')

    return parser.parse_args()

def create_title_page(pdf, year_month_date, project=None):
    """Create and save the title page"""
    month_name = year_month_date.strftime("%B")
    year_val = year_month_date.strftime("%Y")
    generation_time = time.strftime('%H:%M%p %Z on %b %d, %Y')
    
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor('#f5f9ff')
    
    fig.text(0.5, 0.65, f"GPU Usage Report", 
            fontsize=28, ha='center', weight='bold', color='#15417E')

    fig.text(0.5, 0.58, 
            f"{month_name} {year_val}" + (f" - {project}" if project else ""),
            fontsize=22, ha='center', color='#15417E')

    line_ax = fig.add_axes([0.2, 0.55, 0.6, 0.01])
    line_ax.axhline(y=0.5, color='#15417E', linewidth=2)
    line_ax.axis('off')

    project_text = f"For project: {project}\n" if project else ""

    info_text = (
        f"This report provides an analysis of GPU usage patterns\n"
        f"across different job types and execution modes.\n"
        f"The dataset covers all GPU jobs run during {month_name} {year_val}.\n"
        f"{project_text}"
        f"The analysis includes job counts and GPU-hours consumed."
    )

    fig.text(0.5, 0.4, info_text, 
            fontsize=14, ha='center', va='center', linespacing=1.8,
            bbox=dict(facecolor='white', edgecolor='#BFDBFF', boxstyle='round,pad=1.0', linewidth=1.5))

    gen_text = f"Report generated on: {generation_time}"
    fig.text(0.5, 0.2, gen_text, 
            fontsize=10, ha='center', va='center', linespacing=1.8, style='italic',
            bbox=dict(facecolor='#e1ebff', edgecolor='#BFDBFF', boxstyle='round,pad=0.8', linewidth=1))

    footer = "For internal use — Research Computing Services Team"
    fig.text(0.5, 0.03, footer, fontsize=8, ha='center', va='center', style='italic')

    pdf.savefig(fig)

def create_utilization_chart(pdf, year_data):
    """Create utilization chart"""
    # Add gpu reserved column
    year_data['reserved'] = year_data['scenario'] != 0
    year_data['reserved'] = year_data['reserved'].astype(int)
    
    # Resample utilization by 1-hour intervals (mean utilization)
    gpu_util_hourly = year_data.resample('1H', on='time')['reserved'].mean() * 100
    gpu_util_hourly[gpu_util_hourly.isna()] = 0
    
    # Define moving average window size
    window_size = 10
    
    # Compute moving averages for smoothing
    gpu_util_hourly_smooth = gpu_util_hourly.rolling(window=window_size, min_periods=1).mean()
    
    # Resample and compute moving average for percent utilization
    gpu_util_hourly_util = year_data.resample('1H', on='time')['util'].mean()
    gpu_util_hourly_util.fillna(0, inplace=True)
    gpu_util_hourly_util_smooth = gpu_util_hourly_util.rolling(window=window_size, min_periods=1).mean()
    
    fig = plt.figure(figsize=(8.5, 11))  
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 2])
    
    ax = fig.add_subplot(gs[0])
    
    sns.lineplot(x=gpu_util_hourly.index, y=gpu_util_hourly_smooth.values, 
                color="blue", label="Reserved GPU Utilization (Smoothed)", ax=ax)
    ax.axhline(gpu_util_hourly_smooth.mean(), color="blue", linestyle="dashed", 
              linewidth=1, label="Reserved Utilization Avg")
    
    sns.lineplot(x=gpu_util_hourly_util_smooth.index, y=gpu_util_hourly_util_smooth.values, 
                color="red", label="Percent GPU Utilization (Smoothed)", ax=ax)
    ax.axhline(gpu_util_hourly_util_smooth.mean(), color="red", linestyle="dashed", 
              linewidth=1, label="Percent Utilization Avg")
    
    ax.set_xlabel("Time")
    ax.set_ylabel("GPU Utilization (%)")
    ax.set_title("Overall Hourly GPU Reserved vs. Percent Utilization (Smoothed)")
    ax.legend(title="Legend", loc="upper right", frameon=True)
    ax.grid(True)
    plt.xticks(rotation=45)
    
    ax2 = fig.add_subplot(gs[1])
    ax2.axis("off")
    
    description = (
        "This chart provides an overview of GPU utilization trends over time. "
        "The blue line represents the reserved GPU utilization, which reflects job allocations, while the red line "
        "shows the actual percentage of GPU utilization. The dashed lines indicate the average utilization for each metric. "
    )
    
    ax2.text(0.5, 0.75, description, wrap=True, horizontalalignment='center', 
             verticalalignment='center', fontsize=11, color="black", transform=ax2.transAxes,
             bbox=dict(facecolor="lightgray", edgecolor="black", linewidth=1.5),
             ha='center', va='center', clip_on=False)
    
    footer = "For internal use — Research Computing Services Team"
    fig.text(0.5, 0.03, footer, fontsize=8, ha='center', va='center', style='italic')
    
    plt.tight_layout()
    pdf.savefig(fig)

def create_top_users_chart(pdf, year_data):
    """Create top users chart"""
    top_users = year_data[year_data['scenario']!=0].groupby("owner")["reserved"].sum().nlargest(10)
    top_projects = year_data[year_data['scenario']!=0].groupby("project_y")["reserved"].sum().nlargest(10)
    
    sns.set_theme(style="whitegrid")
    
    fig = plt.figure(figsize=(8.5, 11))
    gs = gridspec.GridSpec(3, 1, height_ratios=[2, 2, 1])
    
    ax1 = fig.add_subplot(gs[0])
    
    sns.barplot(x=top_users.values / 12, y=top_users.index, ax=ax1, palette="Blues_r")
    ax1.set_title("Top 10 Users by GPU Utilization", fontsize=14)
    ax1.set_xlabel("Total GPU Utilization (Hours)", fontsize=12)
    ax1.set_ylabel("User", fontsize=12)
    
    ax2 = fig.add_subplot(gs[1])
    
    sns.barplot(x=top_projects.values / 12, y=top_projects.index, ax=ax2, palette="Greens_r")
    ax2.set_title("Top 10 Projects by GPU Utilization", fontsize=14)
    ax2.set_xlabel("Total GPU Utilization (Hours)", fontsize=12)
    ax2.set_ylabel("Project", fontsize=12)
    
    ax3 = fig.add_subplot(gs[2])
    ax3.axis("off")
    
    description = (
        "This visualization shows the top 10 users and projects based on GPU utilization metrics. "
        "The top chart (blue) displays the users who consumed the most GPU resources, while "
        "the bottom chart (green) shows the projects with the highest GPU utilization. Both charts "
        "represent the data in total hours of utilization."
    )
    
    ax3.text(0.5, 0.75, description, wrap=True, horizontalalignment='center', 
             verticalalignment='center', fontsize=11, color="black", transform=ax3.transAxes,
             bbox=dict(facecolor="lightgray", edgecolor="black", linewidth=1.5),
             ha='center', va='center', clip_on=False)
    
    footer = "For internal use — Research Computing Services Team"
    fig.text(0.5, 0.03, footer, fontsize=8, ha='center', va='center', style='italic')
    
    plt.tight_layout()
    pdf.savefig(fig)

def create_low_utilization_chart(pdf, year_data):
    """Create low utilization chart"""
    zero_util_users = year_data[(year_data['util'] <= 5) & (year_data['scenario'] != 0)].groupby('owner').size().reset_index(name='zero_util_count')
    zero_util_projects = year_data[(year_data['util'] <= 5) & (year_data['scenario'] != 0)].groupby('project_y').size().reset_index(name='zero_util_count')
    
    zero_util_users_sorted = zero_util_users.sort_values('zero_util_count', ascending=False).head(10)
    zero_util_projects_sorted = zero_util_projects.sort_values('zero_util_count', ascending=False).head(10)
    
    zero_util_users_sorted['zero_util_count'] /= 12
    zero_util_projects_sorted['zero_util_count'] /= 12
    
    sns.set_theme(style="whitegrid")
    
    fig = plt.figure(figsize=(8.5, 11))
    gs = gridspec.GridSpec(3, 1, height_ratios=[2, 2, 1])
    
    ax1 = fig.add_subplot(gs[0])
    
    sns.barplot(x='zero_util_count', y='owner', data=zero_util_users_sorted, palette='Reds_d', ax=ax1)
    ax1.set_title('Top 10 Users with Low GPU Utilization (<5%)', fontsize=14)
    ax1.set_xlabel('Low Utilization Hours', fontsize=12)
    ax1.set_ylabel('User', fontsize=12)
    
    ax2 = fig.add_subplot(gs[1])
    
    sns.barplot(x='zero_util_count', y='project_y', data=zero_util_projects_sorted, palette='Oranges_d', ax=ax2)
    ax2.set_title('Top 10 Projects with Low GPU Utilization (<5%)', fontsize=14)
    ax2.set_xlabel('Low Utilization Hours', fontsize=12)
    ax2.set_ylabel('Project', fontsize=12)
    
    ax3 = fig.add_subplot(gs[2])
    ax3.axis("off")
    
    description = (
        "This visualization identifies inefficient GPU resource allocation by highlighting users and projects with "
        "consistently low GPU utilization (below 5%). The top chart (red) shows the users who have the most hours "
        "of GPU allocation with minimal actual usage, while the bottom chart (orange) shows projects with similar "
        "patterns. This data can help identify opportunities for better resource allocation and training on GPU "
        "optimization."
    )
    
    ax3.text(0.5, 0.75, description, wrap=True, horizontalalignment='center', 
             verticalalignment='center', fontsize=11, color="black", transform=ax3.transAxes,
             bbox=dict(facecolor="lightgray", edgecolor="black", linewidth=1.5),
             ha='center', va='center', clip_on=False)
    
    footer = "For internal use — Research Computing Services Team"
    fig.text(0.5, 0.03, footer, fontsize=8, ha='center', va='center', style='italic')
    
    plt.tight_layout()
    pdf.savefig(fig)

def create_job_type_chart(pdf, year_data):
    """Create job type chart"""
    df = year_data.copy()
    
    df["job_type"] = df["class_own"].str.capitalize()
    df["execution_type"] = df["job_interactive"].apply(lambda x: "On-Demand/Interactive" if x else "Batch")
    df["gpu_hours"] = df["reserved"] / 12
    
    grouped_df = df.groupby(["owner", "job_id"]).agg({
        "job_type": "first",
        "execution_type": "first",
        "gpu_hours": "sum"
    }).reset_index()
    
    job_count_by_type = grouped_df["job_type"].value_counts()
    job_count_by_execution = grouped_df["execution_type"].value_counts()
    
    gpu_hours_by_type = grouped_df.groupby("job_type")["gpu_hours"].sum()
    gpu_hours_by_execution = grouped_df.groupby("execution_type")["gpu_hours"].sum()
    
    fig = plt.figure(figsize=(8.5, 11))
    gs = gridspec.GridSpec(3, 2, height_ratios=[2, 2, 1])
    
    ax1 = fig.add_subplot(gs[0, 0])
    sns.barplot(x=job_count_by_type.index, y=job_count_by_type.values, ax=ax1, palette="coolwarm")
    ax1.set_title("Job Count: Shared vs Buyin", fontsize=12)
    ax1.set_ylabel("Count", fontsize=10)
    ax1.set_xlabel("Job Type", fontsize=10)
    
    ax2 = fig.add_subplot(gs[0, 1])
    sns.barplot(x=job_count_by_execution.index, y=job_count_by_execution.values, ax=ax2, palette="coolwarm")
    ax2.set_title("Job Count: On-Demand/Interactive vs Batch", fontsize=12)
    ax2.set_ylabel("Count", fontsize=10)
    ax2.set_xlabel("Execution Type", fontsize=10)
    
    ax3 = fig.add_subplot(gs[1, 0])
    sns.barplot(x=gpu_hours_by_type.index, y=gpu_hours_by_type.values, ax=ax3, palette="magma")
    ax3.set_title("GPU Hours: Shared vs Buyin", fontsize=12)
    ax3.set_ylabel("GPU Hours", fontsize=10)
    ax3.set_xlabel("Job Type", fontsize=10)
    
    ax4 = fig.add_subplot(gs[1, 1])
    sns.barplot(x=gpu_hours_by_execution.index, y=gpu_hours_by_execution.values, ax=ax4, palette="magma")
    ax4.set_title("GPU Hours: On-Demand/Interactive vs Batch", fontsize=12)
    ax4.set_ylabel("GPU Hours", fontsize=10)
    ax4.set_xlabel("Execution Type", fontsize=10)
    
    ax5 = fig.add_subplot(gs[2, :])
    ax5.axis("off")
    
    description = (
        "This analysis compares GPU usage patterns across different job categories. "
        "The top row shows the total number of jobs by 'Job Type' (Shared vs Buyin) and 'Execution Type' "
        "(On-Demand/Interactive vs Batch). The bottom row displays the corresponding GPU hours consumed by each category. "
    )
    
    ax5.text(0.5, 0.75, description, wrap=True, horizontalalignment='center', 
             verticalalignment='center', fontsize=11, color="black", transform=ax5.transAxes,
             bbox=dict(facecolor="lightgray", edgecolor="black", linewidth=1.5),
             ha='center', va='center', clip_on=False)
    
    footer = "For internal use — Research Computing Services Team"
    fig.text(0.5, 0.03, footer, fontsize=8, ha='center', va='center', style='italic')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.05, hspace=0.3)
    pdf.savefig(fig)

def create_stacked_job_chart(pdf, year_data):
    """Create stacked job chart"""
    df = year_data.copy()
    
    df["job_type"] = df["class_own"].str.capitalize()
    df["execution_type"] = df["job_interactive"].apply(lambda x: "On-Demand/Interactive" if x else "Batch")
    df["gpu_hours"] = df["reserved"] / 12
    
    grouped_df = df.groupby(["owner", "job_id"]).agg({
        "job_type": "first",
        "execution_type": "first",
        "gpu_hours": "sum"
    }).reset_index()
    
    job_count_stacked = grouped_df.groupby(["job_type", "execution_type"]).size().unstack(fill_value=0)
    gpu_hours_stacked = grouped_df.groupby(["job_type", "execution_type"])["gpu_hours"].sum().unstack(fill_value=0)
    
    fig = plt.figure(figsize=(8.5, 11))
    gs = gridspec.GridSpec(3, 2, height_ratios=[2, 2, 1], hspace=0.4)
    
    ax1 = fig.add_subplot(gs[0, 0:])
    job_count_stacked.plot(kind="bar", stacked=True, ax=ax1, colormap="coolwarm")
    ax1.set_title("Job Count by Job Type & Execution Type", fontsize=12)
    ax1.set_ylabel("Count", fontsize=10)
    ax1.set_xlabel("Job Type", fontsize=10)
    ax1.legend(title="Execution Type")
    ax1.grid(axis='y', linestyle="--", alpha=0.7)
    
    for container in ax1.containers:
        ax1.bar_label(container, labels=[f"{int(val):,}" if val > 0 else "" for val in container.datavalues], 
                      padding=3, fontsize=9, color='black')
    
    ax2 = fig.add_subplot(gs[1, 0:])
    gpu_hours_stacked.plot(kind="bar", stacked=True, ax=ax2, colormap="magma")
    ax2.set_title("GPU Hours by Job Type & Execution Type", fontsize=12)
    ax2.set_ylabel("GPU Hours", fontsize=10)
    ax2.set_xlabel("Job Type", fontsize=10)
    ax2.legend(title="Execution Type")
    ax2.grid(axis='y', linestyle="--", alpha=0.7)
    
    for container in ax2.containers:
        ax2.bar_label(container, labels=[f"{val:,.0f}" if val > 0 else "" for val in container.datavalues], 
                      padding=3, fontsize=9, color='black')
    
    ax3 = fig.add_subplot(gs[2, :])
    ax3.axis("off")
    
    description = (
        "This analysis compares GPU usage patterns across job types and execution modes. "
        "The top chart shows the total number of jobs by Job Type (Shared vs Buyin) broken down by "
        "Execution Type (On-Demand/Interactive vs Batch). The middle chart displays the corresponding "
        "GPU hours consumed by each category combination. "
    )
    
    ax3.text(0.5, 0.5, description, wrap=True, horizontalalignment='center', 
             verticalalignment='center', fontsize=11, color="black", transform=ax3.transAxes,
             bbox=dict(facecolor="lightgray", edgecolor="black", linewidth=1.5),
             ha='center', va='center', clip_on=False)
    
    footer = "For internal use — Research Computing Services Team"
    fig.text(0.5, 0.03, footer, fontsize=8, ha='center', va='center', style='italic')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.05, hspace=0.5, top=0.95)
    pdf.savefig(fig)

def create_n_gpu_chart(pdf, year_data):
    """Create number of gpus per job histogram chart"""
    df = year_data.copy()
    grouped_df = df.groupby(["owner", "job_id"]).agg({
        "n_gpu": "first",
    }).reset_index()

    fig = plt.figure(figsize=(8.5, 11))

    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], figure=fig)

    ax = fig.add_subplot(gs[0])
    sns.histplot(grouped_df['n_gpu'].astype(int), bins=range(1, grouped_df['n_gpu'].astype(int).max() + 1), kde=False, ax=ax, color="purple")
    ax.set_title("Distribution of GPUs per Job", fontsize=14)
    ax.set_xlabel("Number of GPUs per Job", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    ax_text = fig.add_subplot(gs[1])
    ax_text.axis("off")  # Hide axis

    description = (
        "This histogram shows the distribution of GPUs requested per job. Each bar represents the "
        "frequency of jobs that requested a specific number of GPUs."
    )

    ax_text.text(0.5, 0.4, description, fontsize=11, ha='center', va='center', 
                bbox=dict(facecolor='lightgray', edgecolor='black', boxstyle='round,pad=0.4'),
                wrap=True, transform=ax_text.transAxes)

    footer = "For internal use — Research Computing Services Team"
    fig.text(0.5, 0.03, footer, fontsize=8, ha='center', va='center', style='italic')
    pdf.savefig(fig)


def main():
    # Parse command line arguments
    args = parse_arguments()

    # Define year and month from arguments
    year, month = args.year, args.month
    
    # Set up PDF output file
    pdf = PdfPages(args.output)
    
    # Parse date for report
    year_month_date = datetime.strptime("20" + year + '-' + month, "%Y-%m")
    
    # Create title page
    create_title_page(pdf, year_month_date, args.project)
    
    # Process GPU data
    year_data = process_gpu_data(year, month)

    # If project is specified, we mask the dataframe
    if args.project:
        year_data = year_data[year_data['project_y'] == args.project]

    print(f"Percent NaN from GPU Util: {float(year_data[year_data['scenario']!=0]['qname'].isna().mean()):.2%}")
    
    # Load and map node status
    node_status = pd.read_csv('/projectnb/scv/utilization/katia/queue_info.csv')
    node_status_mapping = node_status.set_index('queuename')['class_own'].to_dict()
    year_data['class_own'] = year_data['qname'].map(node_status_mapping)
    node_status_mapping = node_status.set_index('queuename')['class_user'].to_dict()
    year_data['class_user'] = year_data['qname'].map(node_status_mapping)
    
    # Determine if job is interactive
    year_data['job_interactive'] = (year_data['job_name'].str.startswith("ood")) | (year_data['job_name'] == "QRLOGIN")
    
    # Convert 'time' to datetime
    year_data['time'] = pd.to_datetime(year_data['time'], unit='s')
    
    # Create charts
    create_utilization_chart(pdf, year_data)
    create_top_users_chart(pdf, year_data)
    create_low_utilization_chart(pdf, year_data)
    create_job_type_chart(pdf, year_data)
    create_stacked_job_chart(pdf, year_data)
    create_n_gpu_chart(pdf, year_data)
    
    # Close the PDF
    pdf.close()
    print(f"Report saved as {args.output}")

if __name__ == "__main__":
    main()
