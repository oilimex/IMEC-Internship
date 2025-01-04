from qelectrooptics.instruments.attocube.amc300 import AMC300
from qelectrooptics.instruments.keysight.n7744c import N7744C
import numpy as np
from time import sleep
import matplotlib.pyplot as plt

left = AMC300('amc300', address='192.168.1.3', port=9090)                 # replace with the correct VISA address
powermeter = N7744C('n774c', address='TCPIP0::10.82.2.0::inst0::INSTR')   # replace with the correct VISA address

######## SPIRAL EXPLORATION ###########
# First move manually to a relatively good position where you couple some light, then adjust your exploration radius and run the script.

# Define axes
axis_y = left.get_axis(0)
axis_x = left.get_axis(1)

# Activate axes
axis_y.control_output(True)
axis_x.control_output(True)

# Function generating the spiral points to be explored
# b measures how much radial distance is covered in a certain amount of loops (in a certain angle)
# x_0 and y_0 are the points were the spiral is centered (will be the initial current position)
def spiral_eq(a, b, x_0, y_0, num_points, loops):
    theta = np.linspace(0, loops*2*np.pi, num_points)
    r = a + b * theta
    x_spir: np.ndarray = x_0 + r * np.cos(theta)
    y_spir: np.ndarray = y_0 + r * np.sin(theta)
    return x_spir.astype(int), y_spir.astype(int)

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
    
    # Ensure piezo is within range of tolerance
    while (axis_x.position() - x) ** 2 + (axis_y.position() - y) ** 2 > tol**2:
        sleep(0.1)
    
    # Define and return the new current positions for each axis
    curr_y = axis_y.position()
    curr_x = axis_x.position()
    return [curr_x, curr_y]

# Spiral epxloration function
def move_spiral():
    
    # Define current position from which spiral stems from
    curr_y, curr_x, _, _, _, _ = left.get_positions_and_voltages()
   
    # Generate spirally spaced points
    x_spir, y_spir = spiral_eq(0, 30000 / 3 / 2 / np.pi, curr_x, curr_y, 25, loops=3) # change here parameters for the exploration
   
    
    actual_xs, actual_ys = [], [] # store positions and power readings
    power_readings = []
   
    max_power = power_read() # initial coordinates and power
    max_x, max_y = curr_x, curr_y
   
    idx = 1
    for coords in zip(x_spir, y_spir):
        print(
            f"Current x: {coords[0]/1000}, Current y: {coords[1]/1000}, Progress: {idx}%" #print coordinates we move to in um (coords is in nm)
        )
       
        actual_x, actual_y = move_to(*coords) # move to the generated spiral points and measure the power
        power = power_read()
       
        if power > max_power: # keep track of the best found position so far for the final moving
            max_power = power
            max_x = actual_x
            max_y = actual_y
 
        actual_xs.append(actual_x)
        actual_ys.append(actual_y)
        power_readings.append(power)
       
        idx = idx + 1
    
    # Print the best position with the best power value and move there with less tolerance
    print(f"Max power {max_power} dBm found at x {max_x/1000} um, y {max_y/1000} um. Moving there...")
    move_to(max_x, max_y, 50)

    # Plot the result
    plt.plot(x_spir, y_spir)
    plt.plot(actual_xs, actual_ys)