import numpy as np
from numpy import sin, cos, arctan, sqrt
import matplotlib.pyplot as plt
import pandas as pd
from plots import *


def interp(alpha_rad, df):
    aoa_deg = np.rad2deg(alpha_rad)
    cl = np.interp(aoa_deg,df['alpha'], df['cl_stdy'])
    cd = np.interp(aoa_deg,df['alpha'], df['cd_stdy'])
    
    return cl, cd

def interp_dyn_stall(aoa):
    # aoa = np.rad2deg(alpha_rad)
    cl_inv = np.interp(aoa, df_polar['alpha'], df_polar['cl_lin'])
    cl_fs = np.interp(aoa, df_polar['alpha'], df_polar['cl_stall'])
    fs_stat = np.interp(aoa, df_polar['alpha'], df_polar['cl_sep'])
    
    return cl_inv, cl_fs, fs_stat    

class Results:
    def __init__(self, aoa):
        self.aoa = aoa # radians
        self.fs = 0.0 # initial flow separation state (0 = fully separated, 1 = fully attached)
        

    def dyn_stall(self, alpha_rad, vrel, dt, fs, chord):
        aoa = np.rad2deg(alpha_rad)
        cl_inv, cl_fs, fs_stat = interp_dyn_stall(aoa)        
        tau = 4*chord/vrel 
        fs = fs_stat + (fs-fs_stat)*np.exp(-dt/tau)
        cl = fs*cl_inv + (1-fs)*cl_fs
        return cl, fs
        
    def aerodyn_forcings(self, A, omega, v0, t, N_cycles, dt, theta, df, c=1.0, rho=1.225, use_dyn_stall=True):
        """Calculate aerodynamic forcing/work using a time-marching loop."""

        self.chord = c
        n_t = len(t)

        # Kinematics (known from imposed motion)
        self.x = A * np.sin(omega * t)
        self.xdot = A * omega * np.cos(omega * t)

        # Pre-allocate time histories
        self.vy = np.zeros(n_t)
        self.vz = np.zeros(n_t)
        self.vrel = np.zeros(n_t)
        self.alpha_rad = np.zeros(n_t)
        self.cl = np.zeros(n_t)
        self.cd = np.zeros(n_t)

        # Keep a local separation state and march in time
        fs = self.fs

        for n in range(n_t):
            vy_n = v0 * np.cos(self.aoa) + self.xdot[n] * np.cos(theta)
            vz_n = v0 * np.sin(self.aoa) + self.xdot[n] * np.sin(theta)
            vrel_n = np.sqrt(vy_n**2 + vz_n**2)
            alpha_n = np.arctan2(vz_n, vy_n)  # safer than arctan(vz/vy)

            cl_qs, cd_n = interp(alpha_n, df)

            if use_dyn_stall:
                cl_n, fs = self.dyn_stall(alpha_n, vrel_n, dt, fs, c)
            else:
                cl_n = cl_qs

            self.vy[n] = vy_n
            self.vz[n] = vz_n
            self.vrel[n] = vrel_n
            self.alpha_rad[n] = alpha_n
            self.cl[n] = cl_n
            self.cd[n] = cd_n

        # Store latest state
        self.fs = fs

        # Forces
        self.f_x = 0.5 * rho * self.vrel**2 * c * (
            self.cl * np.sin(self.alpha_rad - theta) - self.cd * np.cos(self.alpha_rad - theta)
        )
        self.fx_lift = 0.5 * rho * self.vrel**2 * c * self.cl * np.sin(self.alpha_rad - theta)
        self.fx_drag = -0.5 * rho * self.vrel**2 * c * self.cd * np.cos(self.alpha_rad - theta)

        integrand = self.f_x * np.cos(omega * t)
        self.W = A * omega * np.trapezoid(integrand, t)

        # Power/work histories
        self.power = self.f_x * self.xdot
        self.power_lift = self.fx_lift * self.xdot
        self.power_drag = self.fx_drag * self.xdot

        self.dW = self.power * dt
        self.dW_lift = self.power_lift * dt
        self.dW_drag = self.power_drag * dt

        self.W_t = np.concatenate(([0.0], np.cumsum(self.dW[:-1])))
        self.W_t_lift = np.concatenate(([0.0], np.cumsum(self.dW_lift[:-1])))
        self.W_t_drag = np.concatenate(([0.0], np.cumsum(self.dW_drag[:-1])))

        self.work = np.trapezoid(self.power, t)
        self.work_lift = np.trapezoid(self.power_lift, t)
        self.work_drag = np.trapezoid(self.power_drag, t)

        return self
    
    # def aero_work(self, theta_range: np.ndarray, A: float, omega: float, f_x: np.ndarray):
    #     """
    #     work = A*omega*np.trapezoid(f_x * cos(theta_range), theta_range)
    #     return work
    
    # def aero_work_slides(self):
    #     # define one period
    #     T = 2 * np.pi / omega
        
    #     self.work_slides = A * omega * np.trapezoid(self.f_x * cos(omega *t), T)
    
    def work_one_cycle(self, t: np.ndarray, omega: float, A: float):
        T = 2.0 * np.pi / omega
        t_end = t[-1]
        mask = t >= (t_end - T)  # last full cycle
        
        self.work_cycle = A * omega * np.trapezoid(self.f_x[mask] * np.cos(omega * t[mask]), t[mask])
        

# PARAMETERS
A = 0.2 #m
omega = 5 #rad/s
aoa_deg = np.array([5, 10, 15, 20]) #deg
aoa_rad = np.deg2rad(aoa_deg)
theta_deg = np.arange(0, 361)  # degrees, 0..360
theta_rad = np.deg2rad(theta_deg)
v0 = 10 #m/s
#airfoil = FFA 241

# t = np.linspace(0, 25, 300)

# --- Time discretisation ---
N_cycles = 5  # total simulation cycles (first skipped in integration)
T_period = 2 * np.pi / omega  # one oscillation period [s]
dt = 0.05  # time step [s]
t = np.arange(0, N_cycles * T_period + dt / 2, dt)
t_last = (N_cycles - 1) * T_period
t_int = t[t >= t_last]




df_polar = pd.read_csv('data/FFA-W3-241_ds.csv')

# test one instance first
stall  = Results(aoa_rad[0])
no_stall = Results(aoa_rad[0])
theta = 0

# Switch between static and dynamic stall models here by toggling
use_dyn_stall=True

stall.aerodyn_forcings(A=A, omega=omega, v0=v0, t=t, N_cycles=N_cycles, dt=dt, theta=theta, df=df_polar, use_dyn_stall=True)
no_stall.aerodyn_forcings(A=A, omega=omega, v0=v0, t=t, N_cycles=N_cycles, dt=dt, theta=theta, df=df_polar, use_dyn_stall=False)

plot_flexible(
    t,
    [
        [stall.dW, no_stall.dW],
        [stall.W_t, no_stall.W_t],
        [stall.fx_lift, stall.fx_drag, no_stall.fx_lift, no_stall.fx_drag],
        [stall.cl, stall.cd, no_stall.cl, no_stall.cd],
        [stall.alpha_rad, no_stall.alpha_rad],
        [stall.vrel, no_stall.vrel],
    ],
    [
        [r"stall", r"no stall"],
        [r"stall", r"no stall"],
        [r"$F_{x,l}$ stall", r"$F_{x,d}$ stall", r"$F_{x,l}$ no stall", r"$F_{x,d}$ no stall"],
        [r"$C_l$ stall", r"$C_d$ stall", r"$C_l$ no stall", r"$C_d$ no stall"],
        [r"stall", r"no stall"],
        [r"stall", r"no stall"],
    ],
    "Time [s]",
    [
        "dW [J]",
        r"$W$ [J]",
        r"$F_x$ [N/m]",
        r"$C_l / C_d$ [-]",
        r"$\alpha$ [deg]",
        r"$V_{rel}$ [m/s]",
    ],
    save_name="aero_dyn_example_dynStall_comparison",
)

results_dict = {}

for aoa in aoa_rad:
    for theta in theta_rad:
        stall = Results(aoa)
        no_stall = Results(aoa)
        stall.aerodyn_forcings(A=A, omega=omega, v0=v0, t=t, N_cycles=N_cycles, dt=dt, theta=theta, df=df_polar, use_dyn_stall=True)
        no_stall.aerodyn_forcings(A=A, omega=omega, v0=v0, t=t, N_cycles=N_cycles, dt=dt, theta=theta, df=df_polar, use_dyn_stall=False)
        stall.work_one_cycle(t, omega, A)
        no_stall.work_one_cycle(t, omega, A)
        results_dict[aoa, theta] = (stall, no_stall)
        

# plot the results

# Build one subplot: multiple curves (stall + no_stall for each aoa)

stall_series = [
    [results_dict[(aoa, theta)][0].work_cycle for theta in theta_rad]
    for aoa in aoa_rad
]
no_stall_series = [
    [results_dict[(aoa, theta)][1].work_cycle for theta in theta_rad]
    for aoa in aoa_rad
]

# Solid lines => No dynamic stall
# Dashed lines => With dynamic stall
# show only legend for one curve per aoa (same color for each aoa, different linestyle for stall vs no stall)
# plot only 0-180 degrees for better visibility
mask = (theta_deg >= 0.0) & (theta_deg <= 180.0)
theta_plot = theta_deg[mask]

# ---- font/size controls (adjust these) ----
FS_LABEL =          1        # axis label font size
FS_TICK =           1        # tick-number font size
FS_LEGEND =         1        # legend text font size
FS_LEGEND_TITLE =   1        # legend title font size
# -------------------------------------------

fig, ax = plt.subplots(figsize=(10, 6))
colors = plt.cm.tab10(np.arange(len(aoa_rad)))

for i, aoa in enumerate(aoa_deg):
    no_stall_y = np.asarray(no_stall_series[i])[mask]
    stall_y = np.asarray(stall_series[i])[mask]

    # same color for same aoa
    ax.plot(theta_plot, no_stall_y, color=colors[i], linestyle='-', label=f"AOA {aoa}°")
    ax.plot(theta_plot, stall_y, color=colors[i], linestyle='--', label="_nolegend_")
    ax.axhline(0, color='black', linestyle=':', linewidth=1.5)

# legend 1: AOA colors
leg1 = ax.legend(
    title="AOA",
    loc="best",
    fontsize=FS_LEGEND,
    title_fontsize=FS_LEGEND_TITLE,
)
ax.add_artist(leg1)

# legend 2: line style meaning
from matplotlib.lines import Line2D
style_handles = [
    Line2D([0], [0], color='k', linestyle='-', label='No dynamic stall'),
    Line2D([0], [0], color='k', linestyle='--', label='With dynamic stall'),
]
ax.legend(
    handles=style_handles,
    loc="lower right",
    title="Model",
    fontsize=FS_LEGEND,
    title_fontsize=FS_LEGEND_TITLE,
)

ax.set_xlabel("Direction of motion (degrees)", fontsize=FS_LABEL)
ax.set_ylabel("Work per cycle (J/m)", fontsize=FS_LABEL)
ax.tick_params(axis='both', which='major', labelsize=FS_TICK)

ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("plots/aero_work_vs_theta.png", dpi=300)
plt.close()

# Build two subplots, one for stall and one for no stall, each showing the effect of aoa on work vs theta
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
colors = [f"C0{i}" for i in range(len(aoa_rad))]

# Convert to numpy arrays for proper boolean indexing
stall_series = np.array(stall_series)
no_stall_series = np.array(no_stall_series)

for idx, (a0, color) in enumerate(zip(aoa_deg, colors)):
    ax1.plot(theta_plot, stall_series[idx][mask], color=color, label=f"AOA {a0}°")
    ax2.plot(theta_plot, no_stall_series[idx][mask], color=color, label=f"AOA {a0}°")
for ax, title in zip((ax1, ax2), ("Quasi-steady", "Dynamic stall")):
    ax.axhline(0, color="k", linewidth=0.8, linestyle="--")
    ax.set_xlim(0, 360)
    ax.set_ylabel("Aerodynamic work $W$ of the last period (J/m)")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
ax2.set_xlabel(r"Vibration direction $\theta$ (°)")
fig.suptitle(rf"Exercise 7 — FFA 241, $A = {A}$ m, $\omega = {omega}$ rad/s, $V_0 = {v0}$ m/s, $c = 1.0$ m")
plt.tight_layout()
plt.savefig("plots/exercise_7_work.png")


