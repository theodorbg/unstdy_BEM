import numpy as np
from numpy import sin, cos, arctan, sqrt
import matplotlib.pyplot as plt
import pandas as pd
from plots import *

# reading in airfoil data
# print(df_polar.head())

def interp(aoa, df):
    cl = np.interp(aoa,df['alpha'], df['cl_stdy'])
    cd = np.interp(aoa,df['alpha'], df['cd_stdy'])
    
    return cl, cd

class results:
    def __init__(self, aoa):
        self.aoa = aoa # degrees
        
        
    def aerodyn_forcings(self, A, omega, v0, t, theta, df, c=1.0, rho=1.225):
        """Calculate the aerodynamic work done on a vibrating airfoil given its direction of motion and angle of attack
        
        Parameters
        ----------
        A : float
            Amplitude of vibration (m)
        omega : float
            Angular frequency of vibration (rad/s)
        aoa : float
            Angle of attack (degrees)
        v0 : float
            Freestream velocity (m/s)
        t : numpy.ndarray
            Time array (s)
        theta : numpy.ndarray
            Direction of motion (radians)
        df : pandas.DataFrame
            Airfoil polar data
        c : float, optional
            Chord length (m), by default 1.0
        rho : float, optional
            Air density (kg/m^3), by default 1.225

        """
        
        aoa = np.deg2rad(self.aoa)
        self.x = A * sin(omega * t)
        self.xdot = A * omega * cos(omega * t)

        self.vy = v0 * cos(aoa) + self.xdot * cos(theta)
        self.vz = v0 * sin(aoa) + self.xdot * sin(theta)

        self.vrel = sqrt(self.vy**2 + self.vz**2)

        self.alpha = arctan(self.vz / self.vy)

        self.cl, self.cd = interp(self.alpha, df)
        # Fx = l * sin(alpha - theta) - d * cos(alpha - theta) = 1/2 * rho * Vrel**2 * c * (Cl * sin(alpha - theta) - Cd * cos(alpha - theta))
        self.f_x = 1/2 * rho * self.vrel**2 * c * (self.cl * sin(self.alpha - theta) - self.cd * cos(self.alpha - theta))
        self.fx_lift = 1/2 * rho * self.vrel**2 * c * self.cl*sin(self.alpha - theta)
        self.fx_drag = -1/2 * rho * self.vrel**2 * c * self.cd*cos(self.alpha - theta)
        
        dt = t[1] - t[0]

        # instantaneous power [W/m]
        self.power = self.f_x * self.xdot
        self.power_lift = self.fx_lift * self.xdot
        self.power_drag = self.fx_drag * self.xdot

        # incremental work per step [J/m]
        self.dW = self.power * dt
        self.dW_lift = self.power_lift * dt
        self.dW_drag = self.power_drag * dt

        # cumulative work over time [J/m]
        self.W_t = np.concatenate(([0.0], np.cumsum(self.dW[:-1])))
        self.W_t_lift = np.concatenate(([0.0], np.cumsum(self.dW_lift[:-1])))
        self.W_t_drag = np.concatenate(([0.0], np.cumsum(self.dW_drag[:-1])))

        # total work over full signal (more accurate integral)
        self.work = np.trapezoid(self.power, t)
        self.work_lift = np.trapezoid(self.power_lift, t)
        self.work_drag = np.trapezoid(self.power_drag, t)


# PARAMETERS
A = 0.2 #m
omega = 5 #rad/s
aoa_vals = np.array([5, 10, 15, 20]) #deg
v0 = 10 #m/s
#airfoil = FFA 241

t = np.linspace(0, 25, 300)
theta_vals = np.deg2rad(np.linspace(0, 360, 360))

df_polar = pd.read_csv('data/FFA-W3-241_ds.csv')

# test one instance first
result  = results(0)
theta = 0
result.aerodyn_forcings(A, omega, v0, t, theta, df_polar)

plot_flexible(
        t,
        [[result.dW],
         [result.W_t],
         [result.fx_lift, result.fx_drag],
         [result.cl, result.cd],
         [result.alpha],
         [result.vrel]],
        [[r"$W$"],
         [r"$W$ (cumulative)"],
         [r"$F_{x,l}$", r"$F_{x,d}$"],
         [r"$C_{l}$", r"$C_{d}$"],
         [r"$\alpha$"],
         [r"$V_{rel}$"]],
        "Time [s]",
        ["dW [J]",
         r"$W$ [J]", 
         r"$F_{x,l} [N/m]$", 
         r"$C_{l} / C_{d} [-]$", 
         r"$\alpha$ [deg]", 
         r"$V_{rel}$ [m/s]"],
        save_name="aero_dyn_example"
    )



results_dict = {}

# for aoa in aoa_vals:
#     for theta in theta_vals:
#         res = results(aoa)
#         res.aerodyn_forcings(A, omega, v0, t, theta, df_polar)
#         results_dict[aoa] = res