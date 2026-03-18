"""controller"""

import numpy as np

class Controller:
    """Controller"""

    def __init__(self, use_controller=True):

        self.use_controller = use_controller
        self.k_p = 1.5  # rad/s
        self.k_i = 0.64  # rad/s^2

        self.kk = 14  # gain reduction in degrees

        self.omega_rated = 9.6*np.pi/30  # rad/s
        self.omega_ref = self.omega_rated * 1.02

        self.pitch_min = 0
        self.pitch_max = 90

        self.rated_power = 10.64e6  # W

        self.torque_gen = None
        self.gk = 0
        self.pitch_p = 0
        self.pitch_i = 0
        self.pitch_i_prev = 0

    def simulation_init(self, simulation):
        """Initialize the controller with the simulation instance."""

        rho = simulation.aero.RHO 
        R = simulation.structure.R
        A = simulation.structure.A
        tsr = 8
        Cp_max = 0.466

        self.k_opt = 1/2 * rho * (R / tsr)**3 * A * Cp_max

        self.torque_gen = self.torque_gen_func(simulation)

    
    def step(self, simulation):
        if self.use_controller == True:
            omega = simulation.structure.omega_shaft
            omega_ref = self.omega_ref
            inertia_rotor = simulation.structure.inertia_rotor
            aero_torque = simulation.aero.rotor.torque

            pitch_min = self.pitch_min
            pitch_max = self.pitch_max

            pitch = simulation.structure.pitch[0] # Assuming all blades have the same pitch angle, we can just take the pitch of the first blade.

            # compute the GK
            self.gk = 1 / (1+(pitch / self.kk))

            # compute proportional term
            pitch_p = np.rad2deg(self.gk * self.k_p * (omega - omega_ref))

            # compute integral term

            self.pitch_i = np.rad2deg(self.pitch_i_prev + self.gk * self.k_i * (omega - omega_ref) * simulation.dt)

            # limit integral term between min and max pitch
            self.pitch_i = np.clip(self.pitch_i, pitch_min, pitch_max)

            # compute setpoint
            pitch_sp = pitch_p + self.pitch_i
            # pitch_sp = pitch_p 

            # limit setpoint between min and max pitch
            pitch_sp = np.clip(pitch_sp, pitch_min, pitch_max)
            
            # update the pitch of the structure
            # broadcast scalar setpoint to all blades
            simulation.structure.pitch[:] = [pitch_sp] * len(simulation.structure.pitch)

            # update the rotational speed
            self.torque_gen = self.torque_gen_func(simulation)

            simulation.structure.omega_shaft = omega + (aero_torque - self.torque_gen) / inertia_rotor * simulation.dt

            self.pitch_i_prev = np.radians(self.pitch_i)

    
    def torque_gen_func(self, simulation):
        """Compute the generator torque."""

        omega = float(simulation.structure.omega_shaft)

        if omega < self.omega_rated:
            torque_gen = self.k_opt * omega**2
        else:
            torque_gen = self.rated_power / omega

        return torque_gen