import os
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.stats import linregress
import scipy.stats as stats

TICKS_PER_ROTATION = 14

# Function to plot data from the third format of the input file (time series)
def plot_data_format7(log_file):
    # Regular expression pattern to match lines with throttle, timestamp1, timestamp2, hall_ticks, and load_cell
    line_pattern = r'(?=\d{1,4}\,\d{7,12}\,\d{1,5}\,\d{7,12}\,\d{1,5}\n)'
    # Regular expression pattern to extract throttle, timestamp1, timestamp2, hall_ticks, and load_cell
    extract_pattern = r'(\d{1,4})\,(\d{7,12})\,(\d{1,5})\,(\d{7,12})\,(\d{1,5})'

    # Lists to store extracted values
    timestamp1 = []
    timestamp2 = []
    hall_ticks = []
    load_cell = []
    throttle = []

    # Read the log file line by line
    with open(log_file, 'r') as file:
        for line in file:
            # print(line)
            # Check if the line matches the pattern
            if re.match(line_pattern, line):
                # Extract throttle, timestamp1, timestamp2, hall_ticks, and load_cell using regex
                match = re.search(extract_pattern, line)
                if match:
                    throttle.append(int(match.group(1)))
                    timestamp1.append(int(match.group(2)))
                    hall_ticks.append(int(match.group(3)))
                    timestamp2.append(int(match.group(4)))
                    load_cell.append(int(match.group(5)))

    timestamp1 = np.array(timestamp1)
    timestamp2 = np.array(timestamp2)
    hall_ticks = np.array(hall_ticks)
    load_cell = np.array(load_cell)
    throttle = np.array(throttle)
    rpm = np.divide(hall_ticks / TICKS_PER_ROTATION, (timestamp2 - timestamp1) / 1e6) * 60
    # Filter load cell data with a moving average, then downsample it
    # Smoothing the data with a moving average filter
    def moving_average(data, window_size):
        return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

    window_size = 200  # Adjust this value based on the degree of smoothing desired
    smoothed_load_cell = moving_average(load_cell, window_size)
    # smoothed_load_cell = load_cell

    # Downsampling the data
    downsample_factor = 100
    downsampled_timestamp2 = timestamp2[int(window_size/2):-int(window_size/2 - 1):downsample_factor]
    downsampled_load_cell = smoothed_load_cell[::downsample_factor]

    # Plot RPM and Load Cell vs time
    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1 = plt.subplot(2, 1, 1)
    ax1_2 = ax1.twinx()
    ax1_3 = ax1.twinx()
    p1, = ax1.plot(timestamp2, throttle, label='PWM', color='orange')
    p2, = ax1_2.plot(timestamp2, hall_ticks, label='Hall Ticks', color='green', alpha=0.5)
    p3, = ax1_3.plot(timestamp2, rpm, label='RPM', color='blue')
    ax1.set_xlabel('Timestamp')
    ax1.set_ylabel('PWM')
    ax1_2.set_ylabel('Hall Ticks')
    ax1_3.set_ylabel('RPM')
    ax1.set_title(f'RPM over time for {log_file} (Format 7)')
    ax1.grid(True)

    lines = [p1, p2, p3]
    ax1.legend(lines, [l.get_label() for l in lines])

    ax1_3.spines["right"].set_position(("axes", 1.05))
    ax1.yaxis.label.set_color(p1.get_color())
    ax1_2.yaxis.label.set_color(p2.get_color())
    ax1_3.yaxis.label.set_color(p3.get_color())

    ax1_2.spines["right"].set_edgecolor(p2.get_color())
    ax1_3.spines["right"].set_edgecolor(p3.get_color())

    ax1.tick_params(axis='y', colors=p1.get_color())
    ax1_2.tick_params(axis='y', colors=p2.get_color())
    ax1_3.tick_params(axis='y', colors=p3.get_color())

    # Second subplot for comparison plot
    ax2 = plt.subplot(2, 1, 2)
    ax2.plot(timestamp2, load_cell, label='Load Cell', color='blue')
    ax2.plot(timestamp2[int(window_size/2):-int(window_size/2 - 1)], smoothed_load_cell, label=f'Smoothed Load Cell (Factor = {window_size})', color="orange")
    ax2.set_xlabel('Timestamp')
    ax2.set_ylabel('Load Cell Result')
    ax2.set_title(f'Load Cell over time for {log_file} (Format 7)')
    ax2.grid(True)
    # ax2.legend()

    ax1.sharex(ax2)

    scale_x = 1e6
    ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_x))
    ax1.xaxis.set_major_formatter(ticks_x)
    ax2.xaxis.set_major_formatter(ticks_x)
    
    fig.subplots_adjust(left=0.05, right=0.9, top=0.95, bottom=0.05, hspace=0.2)
    # fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show(block=False)

    # Load cell vs time
    fig, ax = plt.subplots(figsize=(10, 6))
    # ax.scatter(timestamp2, load_cell, marker='o', s=2, label='Data', alpha=0.5)
    # ax.plot(timestamp2[int(window_size/2):-int(window_size/2 - 1)], smoothed_load_cell, label=f'Smoothed (Window Size = {window_size})', linestyle='--')
    ax.scatter(timestamp2[int(window_size/2):-int(window_size/2 - 1)], smoothed_load_cell, label=f'Smoothed (Window Size = {window_size})', s=2)
    ax.plot(downsampled_timestamp2, downsampled_load_cell, label=f'Downsampled (Factor = {downsample_factor})', color="orange")
    # ax.plot(xp, poly(xp), 'r-', label='Polynomial Regression')
    # ax.fill_between(xp, poly(xp) - confidence, poly(xp) + confidence, color='gray', alpha=0.3, label='95% Confidence Interval')
    ax.xaxis.set_major_formatter(ticks_x)
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Load Cell')
    ax.set_title(f'Load cell over time for {log_file} (SMA = {window_size}, downsampling = {downsample_factor})')
    ax.grid(True)
    ax.legend()
    plt.show(block=False)

    # Load cell vs RPM
    # Apply same downsampling to the RPM outputs
    downsampled_rpm = rpm[int(window_size/2):-int(window_size/2 - 1):downsample_factor]

    fig, ax = plt.subplots(figsize=(10, 6))
    # ax.plot(rpm, load_cell, label=f'RPM', color="orange", alpha=0.5)
    # ax.scatter(rpm, load_cell, marker='o', s=2, label='Data', alpha=0.5)
    # ax.plot(downsampled_rpm, downsampled_load_cell, label=f'Downsampled (Factor = {downsample_factor})', color="green", alpha=0.5)
    ax.plot(downsampled_rpm, downsampled_load_cell, label=f'Downsampled (Factor = {downsample_factor})', color="orange", alpha=0.5)
    ax.scatter(downsampled_rpm, downsampled_load_cell, s=2, label=f'Downsampled (Factor = {downsample_factor})')
    # ax.plot(xp, poly(xp), 'r-', label='Polynomial Regression')
    # ax.fill_between(xp, poly(xp) - confidence, poly(xp) + confidence, color='gray', alpha=0.3, label='95% Confidence Interval')
    ax.set_xlabel('Motor RPM')
    ax.set_ylabel('Load Cell')
    ax.set_title(f'Load Cell vs RPM {log_file} (downsampling = {downsample_factor})')
    ax.grid(True)
    ax.legend()
    plt.show(block=False)

    # Load cell vs PWM
    # Apply same downsampling to the PWM inputs
    downsampled_throttle = throttle[int(window_size/2):-int(window_size/2 - 1):downsample_factor]

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

    all_timestamps = np.concatenate((timestamp1, timestamp2))
    all_timestamps.sort(kind='mergesort')
    dt1 = timestamp1[1:] - timestamp1[:-1]
    dt2 = timestamp2[1:] - timestamp2[:-1]
    dtall = all_timestamps[1:] - all_timestamps[:-1]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(timestamp1[1:], dt1, label='Timestamp 1', color="orange", alpha=0.5)
    ax.plot(timestamp2[1:], dt2, label='Timestamp 2', color="green", alpha=0.5)
    ax.plot(all_timestamps[1:], dtall, marker='o', label='All samples', color="red", alpha=0.5)
    ax.xaxis.set_major_formatter(ticks_x)
    ax.yaxis.set_major_formatter(ticks_x)
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('dt since last sample')
    ax.set_title(f'Sampling interval for {log_file}')
    ax.grid(True)
    ax.legend()
    plt.show()
