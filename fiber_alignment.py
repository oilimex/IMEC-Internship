from qelectrooptics.instruments.attocube.amc300 import AMC300
from qelectrooptics.instruments.keysight.n7744c import N7744C
import numpy as np
from time import sleep
import matplotlib.pyplot as plt
from skopt import gp_minimize
from skopt.space import Integer

left = AMC300('amc300', address='192.168.1.3', port=9090)                 # replace with the correct VISA address
powermeter = N7744C('n774c', address='TCPIP0::10.82.2.0::inst0::INSTR')   # replace with the correct VISA address

######## BAYESIAN OPTIMIZATION #########

# Define axes
axis_y = left.get_axis(0)
axis_x = left.get_axis(1)

# Define range of exploration from your current position
curr_y, curr_x, _, _, _, _ = left.get_positions_and_voltages()
x = np.linspace(curr_x-35000, curr_x+35000, 100)
y = np.linspace(curr_y-20000, curr_y+20000, 100)

# Activate axes
axis_y.control_output(True)
axis_x.control_output(True)

# Create arrays to store visited positions and power readings.
visited_positions = []
power_readings = []

# Function that reads power in dBm from the powermeter
def power_read() -> float:
    return np.abs(powermeter.get_channel(0).read_power())

# Function to move to the target position with a certain tolerance/accuracy
def move_to(x, y, tol):

    # Set target position for each axis
    axis_x.control_target_position(x)
    axis_y.control_target_position(y)

    # Activate the movement
    axis_x.control_move(True)
    axis_y.control_move(True)
    
    # Ensure piezo is within tolerance range
    while (axis_x.position() - x) ** 2 + (axis_y.position() - y) ** 2 > tol**2:
        sleep(0.1)
    
    # Define and return the current new positions for each axis
    curr_y = axis_y.position()
    curr_x = axis_x.position()
    return [curr_x, curr_y]

# Function that combines providing the input (move_to) and giving the output (power_read).
# This is the function to minimize.
def move_to_and_measure(coords: list):
    
    # Move and read power
    curr_x, curr_y = move_to(coords[0], coords[1], 1000)
    power = power_read()
    
    # Store values
    visited_positions.append([curr_x, curr_y])
    power_readings.append(power)
    
    return power

# Define optimizer object amnd perform optimization.
result = gp_minimize(
    func=move_to_and_measure, # Function to minimize.
    dimensions=[              # Search space dimensions
        Integer(x[0], x[-1]),
        Integer(y[0], y[-1])
    ],
    n_calls=25,               # Number of calls to 'func'.
    n_random_starts=5,        # Number of evaluations of 'func' with random points.
    verbose=True              # Print progress.
)

# Deactivate axes
axis_y.control_output(False)
axis_x.control_output(False)

# Recover best found position and power reading
optimal_power = min(power_readings)
optimal_position = visited_positions[power_readings.index(optimal_power)]

# Print the best position-power and move there with more accuracy/less tolerance
print(f"Optimal position found: x = {optimal_position[0]}, y = {optimal_position[1]}, Power = {optimal_power}")
axis_y.control_output(True)
axis_x.control_output(True)
move_to(optimal_position[0], optimal_position[1], 100)
axis_y.control_output(False)
axis_x.control_output(False)

# Plot the exploration pattern.
from skopt.plots import plot_objective_2D
plot_objective_2D(result, 0, 1)