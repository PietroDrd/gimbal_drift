import os
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.stats import linregress
import scipy.stats as stats

# Function to plot data from the third format of the input file (time series)
def plot_data_format5(log_file):
    # Regular expression pattern to match lines with timestamp1, v1, v2, v3, v4, and timestamp2
    # 1100,6030475,496,6030480,581,6030484,563,6030490,591,6030472,4095
    # 1060,126554019,0,126554024,0,126554029,0,126554034,0,126554013,2270
    # (?=\d{1,4},\d{7,8},\d{1,3},\d{7,8},\d{1,3},\d{7,8},\d{1,3},\d{7,8},\d{1,3}\n)
    # ^(?=\d{1,4},\d{7,8},\d{1,3},\d{7,8},\d{1,3},\d{7,8},\d{1,3},\d{7,8},\d{1,3}\n)
    # 7\d\d\d\d\d\d\d
    line_pattern = r'(?=\d{1,4}\,\d{7,12}\,\d{1,4}\,\d{7,12}\,\d{1,4}\,\d{7,12}\,\d{1,4}\,\d{7,12}\,\d{1,4}\,\d{7,12}\,\d{1,4}\n)'
    # Regular expression pattern to extract timestamp1, v1, v2, and timestamp2
    extract_pattern = r'(\d{1,4})\,(\d{7,12})\,(\d{1,4})\,(\d{7,12})\,(\d{1,4})\,(\d{7,12})\,(\d{1,4})\,(\d{7,12})\,(\d{1,4})\,(\d{7,12})\,(\d{1,4})'

    # Lists to store extracted values
    timestamp1_values = []
    timestamp2_values = []
    timestamp3_values = []
    timestamp4_values = []
    timestampc_values = []
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
                    timestampc_values.append(int(match.group(10)))
                    load_cell.append(int(match.group(11)))

    timestamp1_values = np.array(timestamp1_values)
    timestamp2_values = np.array(timestamp2_values)
    timestamp3_values = np.array(timestamp3_values)
    timestamp4_values = np.array(timestamp4_values)
    timestampc_values = np.array(timestampc_values)
    variable1 = np.array(variable1)
    variable2 = np.array(variable2)
    variable3 = np.array(variable3)
    variable4 = np.array(variable4)
    load_cell = np.array(load_cell)
    throttle = np.array(throttle)
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

    scale_x = 1e6
    ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_x))
    ax1.xaxis.set_major_formatter(ticks_x)
    ax2.xaxis.set_major_formatter(ticks_x)
    ax3.xaxis.set_major_formatter(ticks_x)
    
    plt.show(block=False)

    # Load cell vs time
    # Filter load cell data with a moving average, then downsample it
    # Smoothing the data with a moving average filter
    def moving_average(data, window_size):
        return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

    window_size = 200  # Adjust this value based on the degree of smoothing desired
    smoothed_load_cell = moving_average(load_cell, window_size)

    # Downsampling the data
    downsample_factor = 100
    downsampled_timestampc_values = timestampc_values[:len(smoothed_load_cell):downsample_factor]
    downsampled_load_cell = smoothed_load_cell[::downsample_factor]

    fig, ax = plt.subplots(figsize=(10, 6))
    # ax.scatter(timestampc_values, load_cell, marker='o', s=2, label='Data', alpha=0.5)
    # ax.plot(timestampc_values[:len(smoothed_load_cell)], smoothed_load_cell, label=f'Smoothed (Window Size = {window_size})', linestyle='--')
    ax.scatter(timestampc_values[:len(smoothed_load_cell)], smoothed_load_cell, label=f'Smoothed (Window Size = {window_size})', s=2)
    ax.plot(downsampled_timestampc_values, downsampled_load_cell, label=f'Downsampled (Factor = {downsample_factor})', color="orange")
    # ax.plot(xp, poly(xp), 'r-', label='Polynomial Regression')
    # ax.fill_between(xp, poly(xp) - confidence, poly(xp) + confidence, color='gray', alpha=0.3, label='95% Confidence Interval')
    ax.xaxis.set_major_formatter(ticks_x)
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Load Cell')
    ax.set_title(f'Load cell over time for {log_file} (SMA = {window_size}, downsampling = {downsample_factor})')
    ax.grid(True)
    ax.legend()
    plt.show(block=False)

    # Load cell vs PWM
    # Apply same downsampling to the PWM inputs
    downsampled_throttle = throttle[:len(smoothed_load_cell):downsample_factor]

    fig, ax = plt.subplots(figsize=(10, 6))
    # ax.scatter(throttle, load_cell, marker='o', s=2, label='Data', alpha=0.5)
    ax.plot(downsampled_throttle, downsampled_load_cell, label=f'Downsampled (Factor = {downsample_factor})', color="orange", alpha=0.5)
    ax.scatter(downsampled_throttle, downsampled_load_cell, s=2, label=f'Downsampled (Factor = {downsample_factor})')
    # ax.plot(xp, poly(xp), 'r-', label='Polynomial Regression')
    # ax.fill_between(xp, poly(xp) - confidence, poly(xp) + confidence, color='gray', alpha=0.3, label='95% Confidence Interval')
    ax.set_xlabel('Throttle PWM')
    ax.set_ylabel('Load Cell')
    ax.set_title(f'Load Cell vs PWM {log_file} (downsampling = {downsample_factor})')
    ax.grid(True)
    ax.legend()
    plt.show(block=False)

    all_timestamps = np.concatenate((timestamp1_values, timestamp2_values, timestamp3_values, timestamp4_values))
    all_timestamps.sort(kind='mergesort')
    dt1 = timestamp1_values[1:] - timestamp1_values[:-1]
    dt2 = timestamp2_values[1:] - timestamp2_values[:-1]
    dt3 = timestamp3_values[1:] - timestamp3_values[:-1]
    dt4 = timestamp4_values[1:] - timestamp4_values[:-1]
    dtall = all_timestamps[1:] - all_timestamps[:-1]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(timestamp4_values[1:], dt4, label='Phase Black 4', color="black", alpha=0.5)
    ax.plot(timestamp3_values[1:], dt3, label='Phase Orange 3', color="orange", alpha=0.5)
    ax.plot(timestamp2_values[1:], dt2, label='Phase Green 2', color="green", alpha=0.5)
    ax.plot(timestamp1_values[1:], dt1, label='Neutral 2', color="blue", alpha=0.5)
    ax.plot(all_timestamps[1:], dtall, marker='o', label='All samples', color="red", alpha=0.5)
    ax.xaxis.set_major_formatter(ticks_x)
    ax.yaxis.set_major_formatter(ticks_x)
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('dt since last sample')
    ax.set_title(f'Sampling interval for {log_file}')
    ax.grid(True)
    ax.legend()
    plt.show()
