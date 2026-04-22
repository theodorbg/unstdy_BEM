"""
Airfoil case with aerodynamic damping
An airfoil suspended in a wind tunnel at a 
geometrical angle of attack αg. 
Ignoring drag
"""
import numpy as np
from numpy import arctan, sqrt
import pandas as pd
from scipy.integrate import solve_ivp

class Airfoil:
    def __init__(self, 
                 aoa_geo_deg: float,
                 use_dyn_stall: bool=True,
                 v0: float=2, 
                 m: float=1.0, 
                 k: float=61.7, 
                 chord: float=0.2, 
                 span: float=1, 
                 rho: float=1.225, 
                 thickness_polar: str='data/FFA-W3-241_ds.csv'):

        self.aoa_geo_deg = aoa_geo_deg
        self.aoa_geo_rad = np.deg2rad(aoa_geo_deg)
        self.use_dyn_stall = use_dyn_stall

        self.m = m
        self.k = k
        self.chord = chord
        self.span = span
        self.rho = rho
        self.v0 = v0
        self.df_polar = pd.read_csv(thickness_polar)
        self.polar_alpha = self.df_polar['alpha']
        self.cl_stdy = self.df_polar['cl_stdy']
        self.cd_stdy = self.df_polar['cd_stdy']
        self.cm_stdy = self.df_polar['cm_stdy']
        self.cl_sep = self.df_polar['cl_sep']
        self.cl_lin = self.df_polar['cl_lin']
        self.cl_stall = self.df_polar['cl_stall']

    def eom(self, t, y):
        # --- EOM --- (Equations of Motion) #
        # Without dynamic stall
        x, x_dot, f = y
        z1 = x # position
        z2 = x_dot # velocity

        flow_angle_rad = arctan(z2 / self.v0) # radians (flow angle)

        self.aoa_rad = self.aoa_geo_rad + flow_angle_rad # radians (angle of attack)

        self.v_rel_sq = z2**2 + self.v0**2

        if self.use_dyn_stall:
            df_dt, Cl = self.dyn_stall(t, y)
        else:
            Cl = self.Cl_interp(np.rad2deg(self.aoa_rad)) # lift coefficient
            df_dt = 0 # No dynamic stall, so df/dt = 0

        lift = 0.5 * self.rho * self.v_rel_sq * self.chord * self.span * Cl
        fx = lift * np.cos(flow_angle_rad)

        dz1 = z2
        dz2 = (-self.k * z1 - fx) / self.m

        
        return [dz1, dz2, df_dt] # No dynamic stall, so df/dt = 0
        
    def dyn_stall(self, t, y):
        x, x_dot, f = y
        alpha = np.rad2deg(self.aoa_rad)
        c = self.chord
        Vrel = sqrt(self.v_rel_sq)
        fstat = self.f_stat_interp(alpha) # Steady-state separation point
        Cl_inv = self.Cl_inv_interp(alpha) # Inviscid lift coefficient
        Cl_fs = self.Cl_fs_interp(alpha) # Fully separated lift coefficient
        
        tau = 4 * c / Vrel
        
        df_dt = (fstat - f) / tau
        Cl = f * Cl_inv + (1 - f) * Cl_fs
        
        return df_dt, Cl
    
    def solve_soe(self, eom, t_span, y0, method,
                  t_eval, rtol, atol):
        
        sol = solve_ivp(
            fun=lambda t, y: eom(t, y),
            t_span=t_span,
            y0=y0,
            method=method,
            t_eval=t_eval,
            rtol=rtol,
            atol=atol,
        )
        
        self.sol = sol
        self.t = self.sol.t
        self.x = self.sol.y[0] # Displacement
        self.x_dot = self.sol.y[1] # Velocity
        self.f = self.sol.y[2] # Dynamic stall parameter
    
    def Cl_interp(self, aoa):
        return np.interp(aoa, self.polar_alpha, self.cl_stdy)
    def f_stat_interp(self, aoa):
        return np.interp(aoa, self.polar_alpha, self.cl_sep)
    def Cl_inv_interp(self, aoa):
        return np.interp(aoa, self.polar_alpha, self.cl_lin)
    def Cl_fs_interp(self, aoa):
        return np.interp(aoa, self.polar_alpha, self.cl_stall)


        

airfoil_0_stall = Airfoil(aoa_geo_deg=0, use_dyn_stall=True)
airfoil_20_stall = Airfoil(aoa_geo_deg=20, use_dyn_stall=True)
airfoil_0_no_stall = Airfoil(aoa_geo_deg=0, use_dyn_stall=False)
airfoil_20_no_stall = Airfoil(aoa_geo_deg=20, use_dyn_stall=False)

airfoils = [airfoil_0_stall, airfoil_20_stall, airfoil_0_no_stall, airfoil_20_no_stall]


# --- INITIAL CONDITIONS --- #
x0 = 0.02
x_dot0 = 0.0
f0 = 0.0
y0 = [x0, x_dot0, f0]

# --- SIMULATION PARAMETERS --- #
t_span = (0, 10)
t_eval = np.linspace(t_span[0], t_span[1], 1000)

# --- SOLVE ODE'S --- #
for airfoil in airfoils:
    airfoil.sol = airfoil.solve_soe(
        eom=airfoil.eom,
        t_span=t_span,
        y0=y0,
        method='RK45',
        t_eval=t_eval,
        rtol=1e-6,
        atol=1e-9
    )
    
# Create 2 subplots in 1 figure
# subplot 1: displacement
# subplot 2: velocity
# show only one legend, indicating stall or not, and angle of attack  (aoa). Displacement vs velocity can be in the y axis, and time in the x axis.
import matplotlib.pyplot as plt
fig, axs = plt.subplots(2, 1, figsize=(10, 8))
for airfoil in airfoils:
    label = f"AOA={airfoil.aoa_geo_deg}°, {'Stall' if airfoil.use_dyn_stall else 'No Stall'}"
    axs[0].plot(airfoil.t, airfoil.x, label=label)
    axs[1].plot(airfoil.t, airfoil.x_dot, label=label)
    
# Show only one legend for both subplots
handles, labels = axs[0].get_legend_handles_labels()
axs[0].legend(handles, labels, loc='upper right')
axs[1].legend(handles, labels, loc='upper right')
axs[0].set_title('Displacement vs Time')
axs[0].set_xlabel('Time [s]')
axs[1].set_title('Velocity vs Time')
axs[1].set_xlabel('Time [s]')
plt.tight_layout()
plt.show()

# Create 4 subplots in 1 figure, showing the 4 cases separately,
# plot1: alpha=0, no stall and stall, position
# plot2: alpha=20, no stall and stall, position
# plot3: alpha=0, no stall and stall, velocity
# plot4: alpha=20, no stall and stall, velocity
fig, axs = plt.subplots(2, 2, figsize=(12, 10))
for airfoil in airfoils:
    label = f"{'Stall' if airfoil.use_dyn_stall else 'No Stall'}"
    if airfoil.aoa_geo_deg == 0:
        axs[0, 0].plot(airfoil.t, airfoil.x, label=label)
        axs[1, 0].plot(airfoil.t, airfoil.x_dot, label=label)
    else:
        axs[0, 1].plot(airfoil.t, airfoil.x, label=label)
        axs[1, 1].plot(airfoil.t, airfoil.x_dot, label=label)
# Show legends for each subplot
axs[0, 0].legend(loc='upper right')
axs[1, 0].legend(loc='upper right')
axs[0, 1].legend(loc='upper right')
axs[1, 1].legend(loc='upper right')
plt.tight_layout()
plt.show()