import os
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import scipy.stats as stats

# Function to plot data from the third format of the input file (time series)
def plot_data_format3(log_file):
    # Regular expression pattern to match lines with timestamp1, v1, v2, v3, v4, and timestamp2
    # 4586960,0,0,0,0,4587408
    # (?=\d{1,4},\d{7,8},\d{1,3},\d{7,8},\d{1,3},\d{7,8},\d{1,3},\d{7,8},\d{1,3}\n)
    # ^(?=\d{1,4},\d{7,8},\d{1,3},\d{7,8},\d{1,3},\d{7,8},\d{1,3},\d{7,8},\d{1,3}\n)
    # 7\d\d\d\d\d\d\d
    line_pattern = r'(?=\d{1,4}\,\d{7,8}\,\d{1,3}\,\d{7,8}\,\d{1,3}\,\d{7,8}\,\d{1,3}\,\d{7,8}\,\d{1,3}\n)'
    # Regular expression pattern to extract timestamp1, v1, v2, and timestamp2
    extract_pattern = r'(\d{1,4})\,(\d{7,8})\,(\d{1,4})\,(\d{7,8})\,(\d{1,4})\,(\d{7,8})\,(\d{1,4})\,(\d{7,8})\,(\d{1,4})\,(\d{7,8})\,(\d{1,4})\n'

    # Lists to store extracted values
    timestamp1_values = []
    timestamp2_values = []
    timestamp3_values = []
    timestamp4_values = []
    timestamp5_values = []
    variable1 = []
    variable2 = []
    variable3 = []
    variable4 = []
    load_cell = []
    throttle = []

    # Read the log file line by line
    with open(log_file, 'r') as file:
        for line in file:
            # Check if the line matches the pattern
            if re.match(line_pattern, line):
                # Extract timestamp1, v1, v2, and timestamp2 using regex
                match = re.search(extract_pattern, line)
                if match:
                    throttle.append(int(match.group(1)))
                    timestamp1_values.append(int(match.group(2)))
                    variable1.append(int(match.group(3)))
                    timestamp2_values.append(int(match.group(4)))
                    variable2.append(int(match.group(5)))
                    timestamp3_values.append(int(match.group(6)))
                    variable3.append(int(match.group(7)))
                    timestamp4_values.append(int(match.group(8)))
                    variable4.append(int(match.group(9)))
                    timestamp5_values.append(int(match.group(10)))
                    load_cell.append(int(match.group(11)))

    # Plot the data as time series with a second subplot for format 2
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
    ax1 = plt.subplot(3, 1, 1)
    ax1.plot(timestamp4_values, variable4, label='Phase White 4', color='black')
    ax1.plot(timestamp3_values, variable3, label='Phase Yellow 3', color='orange')
    ax1.plot(timestamp2_values, variable2, label='Phase Green 2', color='green')
    ax1.plot(timestamp1_values, variable1, label='Neutral 1', color='blue')
    ax1.set_xlabel('Timestamp')
    ax1.set_ylabel('Value')
    ax1.set_title(f'Time Series Plot for {log_file} (Format 3)')
    ax1.grid(True)
    ax1.legend()

    comp2 = [1 if v2 > v1 else 0 for v1, v2 in zip(variable1, variable2)]
    comp3 = [1 if v3 > v1 else 0 for v1, v3 in zip(variable1, variable3)]
    comp4 = [1 if v4 > v1 else 0 for v1, v4 in zip(variable1, variable4)]

    # Second subplot for comparison plot
    ax2 = plt.subplot(3, 1, 2)
    ax2.plot(timestamp4_values, comp4, color='black', marker='o', linestyle='-', alpha=0.5)
    ax2.plot(timestamp2_values, comp2, color='green', marker='o', linestyle='-', alpha=0.5)
    ax2.plot(timestamp3_values, comp3, color='orange', marker='o', linestyle='-', alpha=0.5)
    ax2.set_xlabel('Timestamp')
    ax2.set_ylabel('Comparison Result')
    ax2.set_title(f'Comparison of Phases and Neutral for {log_file} (Format 3)')
    ax2.grid(True)

    ax1.sharex(ax2)

    majority = [((a and b) or (a and c) or (b and c)) for a, b, c in zip(comp2, comp3, comp4)]

    # Third subplot for comparison plot
    ax3 = plt.subplot(3, 1, 3)
    ax3.plot(timestamp4_values, [v if (a==1 and b==0) or (a==0 and b==1) else None for a, b, c, v in zip(comp2, comp3, comp4, variable4)], color='black', label='Phase White 4')
    ax3.plot(timestamp3_values, [v if (a==1 and c==0) or (a==0 and c==1) else None for a, b, c, v in zip(comp2, comp3, comp4, variable3)], color='orange', label='Phase Yellow 3')
    ax3.plot(timestamp2_values, [v if (b==1 and c==0) or (b==0 and c==1) else None for a, b, c, v in zip(comp2, comp3, comp4, variable2)], color='green', label='Phase Green 2')
    ax3.plot(timestamp1_values, variable1, label='Neutral 1', color='blue')
    ax3.set_xlabel('Timestamp')
    ax3.set_ylabel('Comparison Result')
    ax3.set_title(f'Comparison of Phases and Neutral for {log_file} (Format 3)')
    ax3.grid(True)

    ax2.sharex(ax3)

    # Synchronize x-axis zooming
    # def on_xlims_change_ax2(ax):
    #     ax1.set_xlim(ax2.get_xlim())
    # ax2.callbacks.connect('xlim_changed', on_xlims_change_ax2)
    
    # def on_xlims_change_ax1(ax):
    #     ax2.set_xlim(ax1.get_xlim())
    # ax1.callbacks.connect('xlim_changed', on_xlims_change_ax1)
    
    plt.show()
