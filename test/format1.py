import os
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import scipy.stats as stats

# Function to plot data from a log file with polynomial regression and confidence intervals
# def plot_data_with_regression(log_file):
def plot_data_format1(log_file):
    # Regular expression pattern to extract throttle and load cell values
    pattern = r'Pin \d+ - Set throttle to (\d+) - Load cell (\d+)'
    # pattern = r'^(?=\d\d\d\d\d\d\d\d - \d\d?\d? - \d\d?\d? - \d\d\d\d\d\d\d\d\n)'

    # Lists to store extracted values
    throttle_values = []
    load_cell_values = []

    # Read the log file line by line
    with open(log_file, 'r') as file:
        for line in file:
            # Extract throttle and load cell values using regex
            match = re.search(pattern, line)
            if match:
                throttle_values.append(int(match.group(1)))
                load_cell_values.append(int(match.group(2)))

    # Perform polynomial regression
    x = np.array(throttle_values)
    y = np.array(load_cell_values)
    coeffs = np.polyfit(x, y, 3)  # Adjust the polynomial degree as needed
    poly = np.poly1d(coeffs)
    xp = np.linspace(1100, 2000, 100)  # Create points for plotting the regression line

    # Calculate confidence intervals
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    y_pred = intercept + slope * x
    residual = y - y_pred
    dof = len(x) - 2
    t = 2.0  # 95% confidence interval
    # Calculate t value for 50% confidence interval
    # t = stats.t.ppf(1 - (1 - 0.50) / 2, dof)
    confidence = t * np.std(residual) * np.sqrt(1 / len(x) + (xp - np.mean(x)) ** 2 / np.sum((x - np.mean(x)) ** 2))

    # Plot the data with polynomial regression and confidence intervals
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, marker='o', s=5, label='Data')
    plt.plot(xp, poly(xp), 'r-', label='Polynomial Regression')
    plt.fill_between(xp, poly(xp) - confidence, poly(xp) + confidence, color='gray', alpha=0.3, label='95% Confidence Interval')
    plt.xlabel('Throttle (PWM)')
    plt.ylabel('Load Cell')
    plt.title('Throttle vs Load Cell for {} (Polynomial Regression)'.format(log_file))
    plt.grid(True)
    plt.legend()
    plt.show()