import matplotlib.pyplot as plt
import numpy as np
import re
import argparse
from collections import defaultdict

# --- Configuration ---
plt.style.use('dark_background')

PLACEMENT_MAP = {
    'diff_node': 'Inter-node',
    'diff_numa': 'Cross-NUMA (same node)',
    'same_numa': 'Intra-NUMA (diff. core)',
    'same_core': 'Intra-core'
}
ORDERED_CATEGORIES = list(PLACEMENT_MAP.values())
PLACEMENT_TO_INDEX = {key: i for i, key in enumerate(PLACEMENT_MAP.keys())}

SOURCE_MAP = {
    "Compiled from source": "From Source",
    "Compiled with EasyBuild": "EasyBuild",
    "Binaries loaded from the EESSI distribution": "EESSI"
}
SOURCES = ["From Source", "EESSI", "EasyBuild"]
# A new, vibrant color scheme has been applied here
COLORS = ['#9B59B6', '#F1C40F', '#1ABC9C'] # Purple, Yellow, Cyan/Turquoise

def initialize_data_structure():
    """Creates the nested dictionary to hold all parsed performance data."""
    data = {}
    systems = ['Aion', 'Iris']
    metrics = ['Bandwidth', 'Latency']
    
    for system in systems:
        data[system] = {}
        for metric in metrics:
            data[system][metric] = {}
            for source in SOURCES:
                data[system][metric][source] = [0] * len(ORDERED_CATEGORIES)
    return data

def parse_report_file(filepath):
    """Parses the reframe performance report text file."""
    data = initialize_data_structure()
    current_source = None

    with open(filepath, 'r') as f:
        for line in f:
            for header, source_key in SOURCE_MAP.items():
                if header in line:
                    current_source = source_key
                    break
            
            if line.strip().startswith('│') and current_source:
                parts = [p.strip() for p in line.split('│')[1:-1]]
                if len(parts) < 6:
                    continue

                name_col, sysenv_col, _, pvar_col, _, pval_col = parts[:6]

                if 'aion' in sysenv_col:
                    system = 'Aion'
                elif 'iris' in sysenv_col:
                    system = 'Iris'
                else:
                    continue

                if 'bandwidth' in pvar_col.lower() or 'bandwidth' in name_col.lower():
                    metric = 'Bandwidth'
                elif 'latency' in pvar_col.lower() or 'latency' in name_col.lower():
                    metric = 'Latency'
                else:
                    continue

                placement_match = re.search(r'placement=(\w+)', name_col)
                if not placement_match:
                    continue
                
                placement_raw = placement_match.group(1)
                if placement_raw not in PLACEMENT_TO_INDEX:
                    continue
                
                try:
                    value = float(pval_col)
                except ValueError:
                    continue

                idx = PLACEMENT_TO_INDEX[placement_raw]
                data[system][metric][current_source][idx] = value
                
    return data

def create_grouped_bar_chart(ax, data, title, ylabel):
    """Generates a single grouped bar chart on a given matplotlib Axes object."""
    n_groups = len(ORDERED_CATEGORIES)
    n_bars = len(SOURCES)
    
    bar_width = 0.8 / n_bars
    index = np.arange(n_groups)
    
    for i, source in enumerate(SOURCES):
        offset = bar_width * (i - (n_bars - 1) / 2)
        ax.bar(index + offset, data[source], bar_width, label=source, color=COLORS[i])

    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=16)
    ax.set_xticks(index)
    ax.set_xticklabels(ORDERED_CATEGORIES)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")
    ax.grid(True, which='major', linestyle='--', linewidth=0.5, color='grey', alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend()

def generate_single_system_plot(system_name, system_data):
    """
    Creates and saves a single figure for one system (e.g., Aion) 
    with two subplots (Bandwidth and Latency).
    """
    # Create a figure with 1 row and 2 columns of subplots
    fig, axes = plt.subplots(1, 2, figsize=(20, 7))
    
    # Add a main title for the entire figure
    fig.suptitle(f'Performance Metrics - {system_name}', fontsize=22, fontweight='bold')

    # Plot Bandwidth on the left subplot (axes[0])
    create_grouped_bar_chart(
        axes[0], 
        system_data['Bandwidth'], 
        'Bandwidth Performance', 
        'Bandwidth (MB/s)'
    )

    # Plot Latency on the right subplot (axes[1])
    create_grouped_bar_chart(
        axes[1], 
        system_data['Latency'], 
        'Latency Performance', 
        'Latency (µs)'
    )

    # Adjust layout to prevent the title from overlapping plots
    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    
    # Save the figure to a file named after the system
    filename = f"{system_name.lower()}_performance.png"
    plt.savefig(filename, dpi=150)
    print(f"Graph saved as {filename}")
    plt.close(fig) # Close the figure to free up memory

def generate_separate_plots(all_data):
    """
    Iterates through each system in the data and generates a separate plot for it.
    """
    for system_name, system_data in all_data.items():
        if system_name in ['Aion', 'Iris']: # Process only the systems we expect
            generate_single_system_plot(system_name, system_data)

def main():
    """Main function to parse arguments and generate plots."""
    parser = argparse.ArgumentParser(description="Generate performance graphs from a reframe report file.")
    parser.add_argument("report_file", help="Path to the reframe_performance_report.txt file.")
    args = parser.parse_args()

    print(f"Parsing report file: {args.report_file}")
    parsed_data = parse_report_file(args.report_file)
    
    print("Generating separate performance graphs for each system...")
    generate_separate_plots(parsed_data)
    print("Done.")

if __name__ == "__main__":
    main()