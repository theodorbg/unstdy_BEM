import numpy as np
import pandas as pd


class Controller():
    """ PI controller for the simulation of wind turbines. """
    def __init__(self):
        self.pitch_min = 0              # [rad] Minimum pitch angle
        self.pitch_max = 90             # [rad] Maximum pitch angle
        self.k_p = 1.5                   # [rad/(rad/s)] Proportional gain
        self.k_i = 0.64                  # [rad/rad] Integral gain
        self.kk = np.deg2rad(14)        # [rad] Gain scheduling parameter
        self.rated_power = 10.64e6          # [W] Rated power of the turbine
        self.omega_rated = 9.6 * np.pi / 30  # [rad/s] Reference rotational speed of the rotor, corresponding to rated power
        self.omega_ref = self.omega_rated * 1.02 # [rad/s] Reference rotational speed of the rotor, set slightly above rated
        
        
    def simulation_init(self, simulation):
        # Initialize the integral term
        self.theta_i = 0
        
        # Calculate the MPPT gain K_opt
        R = simulation.structure.R
        A = np.pi * R**2 # Swept area of the rotor
        rho = simulation.aero.RHO # Air density
        Cp_max = 0.466 # Power coefficient at optimal pitch (0 deg) and tip speed ratio
        lambda_opt = 8 # Optimal tip speed ratio
        self.K_opt = 0.5 * rho * A * Cp_max * (R / lambda_opt)**3
        
        
    
    def step(self, simulation):

        pitch = simulation.structure.pitch
        omega = simulation.structure.omega_shaft
        Q_aero = simulation.aero.rotor.torque
        inertia_rotor = simulation.structure.inertia_rotor

        # compute the GK
        self.GK = 1 / (1+(pitch / self.kk)) # [-]

        # compute proportional term
        self.theta_p = self.GK * self.k_p * (omega - self.omega_ref)

        # compute integral term
        self.theta_i = self.theta_i + self.GK * self.k_i * (omega - self.omega_ref) * simulation.dt

        # limit integral term between min and max pitch
        self.theta_i = np.clip(self.theta_i, self.pitch_min, self.pitch_max)

        # compute setpoint
        self.theta_sp = np.rad2deg(self.theta_p + self.theta_i)

        # limit setpoint between min and max pitch
        self.pitch_sp = np.clip(self.theta_sp, self.pitch_min, self.pitch_max)
        
        # Update the pitch of the structure
        simulation.structure.pitch[:] = self.pitch_sp
        
        
        # Torque controller
        # Calculate generator torque
        if omega <= self.omega_rated:
            Q_gen = self.K_opt * omega**2
        elif omega > self.omega_rated:
            Q_gen = self.rated_power / omega
            
        # Forwards Euler update of the rotor speed (Changed later for better time integration)
        simulation.structure.omega_shaft = omega + (Q_aero - Q_gen) / inertia_rotor * simulation.dt
    
        
        