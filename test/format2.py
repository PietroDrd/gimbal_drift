import os
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import scipy.stats as stats

# Function to plot data from the second format of the input file (time series)
def plot_data_format2(log_file):
    # Regular expression pattern to match lines with timestamp1, v1, v2, and timestamp2
    line_pattern = r'(?=\d{8} - \d{1,3} - \d{1,3} - \d{8}\n)'
    # Regular expression pattern to extract timestamp1, v1, v2, and timestamp2
    extract_pattern = r'(\d{8}) - (\d{1,3}) - (\d{1,3}) - (\d{8})\n'

    # Lists to store extracted values
    timestamp1_values = []
    timestamp2_values = []
    variable1 = []
    variable2 = []

    # Read the log file line by line
    with open(log_file, 'r') as file:
        for line in file:
            # Check if the line matches the pattern
            if re.match(line_pattern, line):
                # Extract timestamp1, v1, v2, and timestamp2 using regex
                match = re.search(extract_pattern, line)
                if match:
                    timestamp1_values.append(int(match.group(1)))
                    variable1.append(int(match.group(2)))
                    variable2.append(int(match.group(3)))
                    timestamp2_values.append(int(match.group(4)))

    # Plot the data as time series with a second subplot for format 2
    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(timestamp2_values, variable2, label='Variable 2')
    ax1.plot(timestamp2_values, variable1, label='Variable 1')
    ax1.set_xlabel('Timestamp')
    ax1.set_ylabel('Value')
    ax1.set_title(f'Time Series Plot for {log_file} (Format 2)')
    ax1.grid(True)
    ax1.legend()

    # Third subplot for comparison plot
    ax2 = plt.subplot(2, 1, 2)
    ax2.plot(timestamp1_values, [1 if v2 > v1 else 0 for v1, v2 in zip(variable1, variable2)], color='b', marker='o', linestyle='-')
    ax2.set_xlabel('Timestamp')
    ax2.set_ylabel('Comparison Result')
    ax2.set_title(f'Comparison of V2 and V1 for {log_file} (Format 2)')
    ax2.grid(True)

    ax1.sharex(ax2)

    # Synchronize x-axis zooming
    # def on_xlims_change_ax2(ax):
    #     ax1.set_xlim(ax2.get_xlim())
    # ax2.callbacks.connect('xlim_changed', on_xlims_change_ax2)
    
    # def on_xlims_change_ax1(ax):
    #     ax2.set_xlim(ax1.get_xlim())
    # ax1.callbacks.connect('xlim_changed', on_xlims_change_ax1)
    
    plt.show()

# # Function to plot data from the second format of the input file
# def plot_data_format2(log_file):
#     # Regular expression pattern to match the second format of the input file
#     pattern = r'(?=\d\d\d\d\d\d\d\d - \d\d?\d? - \d\d?\d? - \d\d\d\d\d\d\d\d\n)'

#     # Lists to store extracted values
#     middle_numbers1 = []
#     middle_numbers2 = []

#     # Read the log file line by line
#     with open(log_file, 'r') as file:
#         for line in file:
#             # Extract two middle numbers from each line using regex
#             match = re.search(pattern, line)
#             if match:
#                 numbers = line.split(' - ')
#                 if len(numbers) >= 4:
#                     middle_numbers1.append(int(numbers[1]))
#                     middle_numbers2.append(int(numbers[2]))

#     # Plot the data as scatter plot with smaller markers
#     plt.figure(figsize=(10, 6))
#     plt.scatter(middle_numbers1, middle_numbers2, marker='o', s=5)  # Set the marker size to 5
#     plt.xlabel('Number 1')
#     plt.ylabel('Number 2')
#     plt.title('Number 1 vs Number 2 for {} (Format 2)'.format(log_file))
#     plt.grid(True)
#     plt.show()