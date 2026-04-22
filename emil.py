import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import pandas as pd
from pathlib import Path


# Parameters
m = 1.0         # mass (kg)
k = 61.7        # spring constant (N/m)
chord = 0.2     # chord length (m)
s = 1.0         # span (m)
rho = 1.225     # air density (kg/m^3)
V0 = 2.0        # initial wind velocity (m/s)
aoa_g_cases = [0, 20] # angles of attack (degrees)
dynamic_stall_cases = [False, True] # dynamic stall on or off cases

# Time span for the simulation
t_span = (0, 10)  # from 0 to 10 seconds
t_eval = np.linspace(t_span[0], t_span[1], 2000)  # 2000 time points

# Initial conditions
x0 = 0.02       # initial position of the mass (m)
v0 = 0          # initial velocity of the mass (m/s)
f0 = 0.0        # initial aerodynamic state variable (for dynamic stall)
y0 = [x0, v0, f0]   # initial state vector

# Import lift coefficient data
script_dir = Path(__file__).resolve().parent
data_dir = script_dir.parent
file_path = data_dir / "data" / "FFA-W3-241_ds.csv"

data = pd.read_csv(file_path)

# Extract the angle of attack and lift coefficient data
alpha = data['alpha'].values
cl = data['cl_stat'].values
# Dynamic stall case data:
cl_inv = data['cl_inv'].values
cl_fs = data['cl_fs'].values
f_stat = data['f_stat'].values


# Make functions to interpolate lift coefficients and stall state as a function of angle of attack
def Cl_interp(aoa):
    return np.interp(aoa, alpha, cl)
def f_stat_interp(aoa):
    return np.interp(aoa, alpha, f_stat)
def Cl_inv_interp(aoa):
    return np.interp(aoa, alpha, cl_inv)
def Cl_fs_interp(aoa):
    return np.interp(aoa, alpha, cl_fs)



# Solve for the two cases of angle of attack with and without dynamic stalls and store the results in a dictionary
solutions = {}
for aoa_g in aoa_g_cases:
    for dynamic_stall in dynamic_stall_cases:
        # EOM: m*x'' = -k*x - L*cos(theta)
        def equations_of_motion(t, y):
            x, v, f = y
            z1 = x # To match the notation in the lecture, we can define z1 as x
            z2 = x_dot = v # and z2 as x' (velocity)
            z3 = f # and z3 as the aerodynamic state variable for dynamic stall
            
            # Calculate the flow angle 
            theta = np.arctan2(z2, V0) 
            
            # Calculate angle of attack (aoa) in degrees
            aoa = aoa_g + np.degrees(theta)
            
            # Calculate the relative velocity magnitude
            V_rel = np.sqrt(V0**2 + z2**2)
            
            # Calcaulate the lift coefficient with or without dynamic stall
            if dynamic_stall:
                Cl = z3 * Cl_inv_interp(aoa) + (1 - z3) * Cl_fs_interp(aoa)
            else:
                Cl = Cl_interp(aoa)
                
            # Time factor tau
            tau = 4*chord/V_rel
            
            # Calculate the aerodynamic force
            F_x = 0.5 * rho * V_rel**2 * chord * s * Cl * np.cos(theta)  # Lift force * cos(theta) component
            
            # Calculate the derivatives
            x_ddot = z_ddot = (-k*z1 - F_x) / m
            df = z3_dot = (f_stat_interp(aoa) - z3) / tau
            
            return [x_dot, x_ddot, df] # Return the derivatives [x', x'', f'] or [z2, z2', z3']


        # Solve the system of equations
        sol = solve_ivp(equations_of_motion, t_span=t_span, y0=y0, method='RK45', t_eval=t_eval, rtol=1e-9, atol=1e-9)

        # Store the solution in the dictionary
        solutions[(aoa_g, dynamic_stall)] = sol
    


# Extract the results
# Case: aoa_g = 0 
time = solutions[(aoa_g_cases[0], dynamic_stall_cases[0])].t
x_0_nostall = solutions[(aoa_g_cases[0], dynamic_stall_cases[0])].y[0]
v_0_nostall = solutions[(aoa_g_cases[0], dynamic_stall_cases[0])].y[1]
x_0_stall = solutions[(aoa_g_cases[0], dynamic_stall_cases[1])].y[0]
v_0_stall = solutions[(aoa_g_cases[0], dynamic_stall_cases[1])].y[1]

# Case: aoa_g = 20
x_20_nostall = solutions[(aoa_g_cases[1], dynamic_stall_cases[0])].y[0]
v_20_nostall = solutions[(aoa_g_cases[1], dynamic_stall_cases[0])].y[1]
x_20_stall = solutions[(aoa_g_cases[1], dynamic_stall_cases[1])].y[0]
v_20_stall = solutions[(aoa_g_cases[1], dynamic_stall_cases[1])].y[1]


# Plot the results in 4 subplots with position and velocity for both angles of attack and dynamic stall cases
plt.figure(figsize=(18, 9))
# Position of aoa_g = 0
plt.subplot(2, 2, 1)
plt.plot(time, x_0_nostall, label=r'$x(t)$, $\alpha_g=0^\circ$, No Stall')
plt.plot(time, x_0_stall, label=r'$x(t)$, $\alpha_g=0^\circ$, Dynamic Stall')
plt.title(r'Position vs Time, $\alpha_g=0^\circ$')
plt.xlabel('Time (s)')
plt.ylabel('Position (m)')
plt.legend(loc='upper right')
plt.grid()
# Position of aoa_g = 20
plt.subplot(2, 2, 2)
plt.plot(time, x_20_nostall, label=r'$x(t)$, $\alpha_g=20^\circ$, No Stall')
plt.plot(time, x_20_stall, label=r'$x(t)$, $\alpha_g=20^\circ$, Dynamic Stall')
plt.title(r'Position vs Time, $\alpha_g=20^\circ$')
plt.xlabel('Time (s)')
plt.ylabel('Position (m)')
plt.legend(loc='upper right')
plt.grid()
# Velocity of aoa_g = 0
plt.subplot(2, 2, 3)
plt.plot(time, v_0_nostall, label=r'$v(t)$, $\alpha_g=0^\circ$, No Stall')
plt.plot(time, v_0_stall, label=r'$v(t)$, $\alpha_g=0^\circ$, Dynamic Stall')
plt.title(r'Velocity vs Time, $\alpha_g=0^\circ$')  
plt.xlabel('Time (s)')
plt.ylabel('Velocity (m/s)')
plt.legend(loc='upper right')
plt.grid()
# Velocity of aoa_g = 20
plt.subplot(2, 2, 4)
plt.plot(time, v_20_nostall, label=r'$v(t)$, $\alpha_g=20^\circ$, No Stall')
plt.plot(time, v_20_stall, label=r'$v(t)$, $\alpha_g=20^\circ$, Dynamic Stall')
plt.title(r'Velocity vs Time, $\alpha_g=20^\circ$')
plt.xlabel('Time (s)')
plt.ylabel('Velocity (m/s)')
plt.legend(loc='upper right')
plt.grid()

plt.tight_layout()
plt.show()









# # Plot the results
# plt.figure(figsize=(18, 9))
# plt.subplot(2, 1, 1)
# plt.plot(time, x_0_nostall, label=r'$x(t)$, $\alpha_g=0^\circ$')
# plt.plot(time, x_20_nostall, label=r'$x(t)$, $\alpha_g=20^\circ$')
# plt.plot(time, x_0_stall, label=r'$x(t)$, $\alpha_g=0^\circ$, Dynamic Stall')
# plt.plot(time, x_20_stall, label=r'$x(t)$, $\alpha_g=20^\circ$, Dynamic Stall')
# plt.title('Position vs Time')
# plt.xlabel('Time (s)')
# plt.ylabel('Position (m)')
# plt.legend(loc='upper right')
# plt.grid()
# plt.subplot(2, 1, 2)
# plt.plot(time, v_0_nostall, label=r'$v(t)$, $\alpha_g=0^\circ$')
# plt.plot(time, v_20_nostall, label=r'$v(t)$, $\alpha_g=20^\circ$')
# plt.plot(time, v_0_stall, label=r'$v(t)$, $\alpha_g=0^\circ$, Dynamic Stall')
# plt.plot(time, v_20_stall, label=r'$v(t)$, $\alpha_g=20^\circ$, Dynamic Stall')
# plt.title('Velocity vs Time')
# plt.xlabel('Time (s)')
# plt.ylabel('Velocity (m/s)')
# plt.legend(loc='upper right')
# plt.grid()

# plt.tight_layout()
# plt.show()    






""" #This code is just for either dynamic stall on or off, not both at the same time.

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import pandas as pd
from pathlib import Path


# Parameters
m = 1.0         # mass (kg)
k = 61.7        # spring constant (N/m)
chord = 0.2     # chord length (m)
s = 1.0         # span (m)
rho = 1.225     # air density (kg/m^3)
V0 = 2.0        # initial velocity (m/s)
aoa_g_cases = [0, 20] # angles of attack (degrees)

# Time span for the simulation
t_span = (0, 10)  # from 0 to 10 seconds
t_eval = np.linspace(t_span[0], t_span[1], 2000)  # 2000 time points

# Dynamic stall flag
dynamic_stall = True  # Set to True to include dynamic stall effects, False for static

# Initial conditions
x0 = 0.02       # initial position (m)
v0 = V0         # initial velocity (m/s)
f0 = 0.0        # initial aerodynamic state variable (for dynamic stall)
y0 = [x0, v0, f0]   # initial state vector

# Import lift coefficient data
script_dir = Path(__file__).resolve().parent
data_dir = script_dir.parent
file_path = data_dir / "data" / "FFA-W3-241_ds.csv"

data = pd.read_csv(file_path)

# Extract the angle of attack and lift coefficient data
alpha = data['alpha'].values
cl = data['cl_stat'].values
# Dynamic stall case data:
cl_inv = data['cl_inv'].values
cl_fs = data['cl_fs'].values
f_stat = data['f_stat'].values


# Make function to interpolate lift coefficient as a function of angle of attack
def Cl_interp(aoa):
    return np.interp(aoa, alpha, cl)
def f_stat_interp(aoa):
    return np.interp(aoa, alpha, f_stat)
def Cl_inv_interp(aoa):
    return np.interp(aoa, alpha, cl_inv)
def Cl_fs_interp(aoa):
    return np.interp(aoa, alpha, cl_fs)



# Solve for the two cases of angle of attack and store the results in a dictionary
solutions = {}
for aoa_g in aoa_g_cases:
    # EOM: m*x'' = -k*x - L*cos(theta)
    def equations_of_motion(t, y):
        x, v, f = y
        z1 = x # To match the notation in the lecture, we can define z1 as x
        z2 = v # and z2 as x' (velocity)
        z3 = f # and z3 as the aerodynamic state variable for dynamic stall
        
        
        # Calculate the flow angle 
        theta = np.arctan2(z2, V0) 
        
        # Calculate angle of attack (aoa) in degrees
        aoa = aoa_g + np.degrees(theta)
        
        # Calculate the relative velocity magnitude
        V_rel = np.sqrt(V0**2 + z2**2)
        
        # Calcaulate the lift coefficient with or without dynamic stall
        if dynamic_stall:
            Cl = z3 * Cl_inv_interp(aoa) + (1 - z3) * Cl_fs_interp(aoa)
        else:
            Cl = Cl_interp(aoa)
            
        # Time factor tau
        tau = 4*chord/V_rel
        
        # Calculate the aerodynamic force
        F_x = 0.5 * rho * V_rel**2 * chord * s * Cl * np.cos(theta)  # Lift force * cos(theta) component
        
        # Calculate the derivatives
        x_ddot = z_ddot = (-k*z1 - F_x) / m
        df = z3_dot = (f_stat_interp(aoa) - z3) / tau
        
        return [v, x_ddot, df] # Return the derivatives [x', x'', f'] or [z2, z2', z3']


    # Solve the system of equations
    sol = solve_ivp(equations_of_motion, t_span=t_span, y0=y0, method='RK45', t_eval=t_eval, rtol=1e-9, atol=1e-9)

    # Store the solution in the dictionary
    solutions[aoa_g] = sol
    


# Extract the results
# Case: aoa_g = 0
time = solutions[aoa_g_cases[0]].t
x_0 = solutions[aoa_g_cases[0]].y[0]
v_0 = solutions[aoa_g_cases[0]].y[1]

# Case: aoa_g = 20
x_20 = solutions[aoa_g_cases[1]].y[0]
v_20 = solutions[aoa_g_cases[1]].y[1]

# Plot the results
plt.figure(figsize=(18, 9))
plt.subplot(2, 1, 1)
plt.plot(time, x_0, label=r'$x(t)$, $\alpha_g=0^\circ$')
plt.plot(time, x_20, label=r'$x(t)$, $\alpha_g=20^\circ$')
plt.title('Position vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Position (m)')
plt.legend(loc='upper right')
plt.grid()
plt.subplot(2, 1, 2)
plt.plot(time, v_0, label=r'$v(t)$, $\alpha_g=0^\circ$')
plt.plot(time, v_20, label=r'$v(t)$, $\alpha_g=20^\circ$')
plt.title('Velocity vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Velocity (m/s)')
plt.legend(loc='upper right')
plt.grid()

plt.tight_layout()
plt.show()    




"""