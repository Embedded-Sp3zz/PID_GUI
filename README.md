# PID_GUI

Flow Rate Control for a Pressurized Reservoir with a Proportional Pinch Valve

This Python script provides a GUI for controlling the flow rate of fluid out of a pressurized reservoir. The reservoir is equipped with a proportional pinch valve at the outlet, and the outlet drains into a bucket placed on a scale measuring its weight. The weight data from the scale is streamed to a computer. The weight data is updated every second and is located in a working directory as a numpy file which can be read. The goal is to achieve a specified flow rate while maintaining a steady output.

Task Requirements
    Develop a Python script to control the proportional pinch valve connected to the outlet of a pressurized reservoir.
    Read the weight data from the scale measuring the weight of the bucket.
    Calculate the flow rate based on the change in weight and time, ensuring that the flow rate is within the specified limits.
    Implement a control algorithm (e.g., PID) to adjust the proportional pinch valve position based on the calculated flow rate.
    Create a user interface that allows users to input the desired flow rate and monitor the current flow rate and valve position.

Installation
1. Install Python 3 on your computer.

2. Install the necessary libraries by running the following command:

    pip install PyQt5 simple_pid matplotlib numpy

Usage
1. Connect the scale and the proportional pinch valve to your computer.

2. Run the Flow_Rate_Control.py script in the command line:

    python Flow_Rate_Control.py

3. Enter the desired flow rate (in mL/s) in the input field and click on "Set Flow Rate".

4. Monitor the current flow rate and valve position in the GUI.

5. Adjust the flow rate as needed.