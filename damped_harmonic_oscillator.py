import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

"""
sdof_forced_response
spring_mass_rk45
forced_vibration

Forced Damped Spring-Mass System Simulation (SDOF)
===================================================
Simulates the dynamic response of a single degree of freedom (SDOF)
spring-mass-damper system subjected to a harmonic cosine forcing function.

The system is governed by Newton's 2nd Law:
    m*x'' + c*x' + k*x = F0 * cos(omega * t)

where:
    m      - mass [kg]
    c      - viscous damping coefficient [N·s/m]
    k      - spring stiffness [N/m]
    F0     - force amplitude [N]
    omega  - forcing frequency [rad/s]

Parameters
----------
kstiff : float
    Spring stiffness [N/m]
mass : float
    Mass of the oscillator [kg]
ksi : float
    Damping ratio [-]
fampl : float
    Amplitude of the external harmonic force [N]
fomeg : float
    Forcing frequency, set to 0.95 * omega_nat (just below resonance) [rad/s]

Output
------
Plot of the normalised displacement (x * k / F0) vs. time, representing
the dynamic amplification factor relative to the static deflection.

Solver
------
Uses scipy.integrate.solve_ivp with the RK45 method, equivalent to
MATLAB's ode45.

"""

# Parameters
kstiff = 2
mass = 0.5
ksi = 0.2                              # Damping ratio
cdamp = ksi * 2 * np.sqrt(kstiff * mass)  # Damping coefficient
fampl = 3                              # Force amplitude
omega_nat = np.sqrt(kstiff / mass)    # Natural cyclic frequency
fomeg = 0.95 * omega_nat              # Forcing frequency

# ODE system (equivalent to the MATLAB springmass function)
def springmass(t, z):
    force = fampl * np.cos(fomeg * t)
    dzdt = [
        z[1],
        (-kstiff * z[0] - cdamp * z[1] + force) / mass
    ]
    return dzdt

# Solve (equivalent to ode45 with tspan=[0,50] and z0=[0,0])
sol = solve_ivp(
    springmass,
    t_span=(0, 50),
    y0=[0, 0],
    method='RK45',          # RK45 is the Python equivalent of ode45
    dense_output=True,
    max_step=0.1            # Optional: controls output resolution
)

# Plot (equivalent to plot(t, z(:,1)*kstiff/fampl))
plt.figure()
plt.plot(sol.t, sol.y[0] * kstiff / fampl)
plt.xlabel('Time [s]')
plt.ylabel('Normalised displacement x·k/F')
plt.title('Spring-Mass System Response')
plt.grid(True)
plt.tight_layout()
plt.show()