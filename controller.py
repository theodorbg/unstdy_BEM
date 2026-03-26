"""controller"""

import numpy as np
class NoController:
    def simulation_init(self, simulation):
        pass
    def step(self, simulation):
        pass
    
class Controller:
    """Controller"""

    @classmethod
    def create(cls, use_controller: bool = True, **kwargs):
        """
        Factory: returns Controller or NoController.
        Keeps main script free of if/else controller wiring.
        """
        if use_controller:
            return cls(use_controller=True, **kwargs)
        return NoController()

    def __init__(self, tsr: float = 8.0,
                 cp_max: float = 0.466, 
                 rated_power: float = 10.64e6, 
                 omega_rated: float = 9.6*np.pi/30, 
                 ref_scale: float = 1.02, 
                 k_p: float = 1.5, 
                 k_i: float = 0.64, 
                 kk: float = 14, 
                 use_controller: bool = True):
        
        """Initialize the controller with the given parameters.
        
        Parameters
        ----------
        tsr : float
            Tip speed ratio.
        cp_max : float
            Maximum power coefficient.
        rated_power : float, optional
            Rated power of the turbine (default is 10.64e6 W).
        omega_rated : float, optional
            Rated rotational speed of the turbine (default is 9.6*np.pi/30 rad/s).
        ref_scale : float, optional
            Scale factor for the reference rotational speed (default is 1.02).
        k_p : float, optional
            Proportional gain (default is 1.5 rad/s).
        k_i : float, optional
            Integral gain (default is 0.64 rad/s^2).
        kk : float, optional
            Gain reduction factor (default is 14 degrees).
        use_controller : bool, optional
            Whether to use the controller (default is True).
        """

        self.use_controller = use_controller
        self.k_p = k_p  # rad/s
        self.k_i = k_i  # rad/s^2

        self.kk = kk  # gain reduction in degrees

        self.omega_rated = omega_rated  # rad/s
        self.omega_ref = self.omega_rated * ref_scale

        self.pitch_min = 0
        self.pitch_max = 90

        self.rated_power = rated_power  # W

        self.torque_gen = None
        self.gk = 0
        self.pitch_p = 0
        self.pitch_i = 0
        self.pitch_i_prev = 0
        self.tsr = tsr
        self.cp_max = cp_max
        
    def simulation_init(self, simulation):
        """Initialize the controller with the simulation instance."""

        rho = simulation.aero.RHO 
        R = simulation.structure.R
        A = simulation.structure.A

        self.k_opt = 1/2 * rho * (R / self.tsr)**3 * A * self.cp_max

        self.torque_gen = self.torque_gen_func(simulation)
        
        # parameter for 2nd order filter
        self.pitch_prev = simulation.structure.pitch[0] # Assuming all blades have the same pitch angle, we can just take the pitch of the first blade.


    
    def step(self, simulation):
        omega = simulation.structure.omega_shaft
        omega_ref = self.omega_ref
        inertia_rotor = simulation.structure.inertia_rotor
        aero_torque = simulation.aero.rotor._torque

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
        
        # add pitch actuator dynamics (2nd order filter)
        omega0 = 8.0
        zeta = 0.7
        dt = simulation.dt
        
        pitch_current = pitch
        pitch_new = (
            omega0**2 * dt**2 * pitch_sp
            + (2- omega0**2 * dt**2) * pitch_current
            + (zeta * omega0 * dt - 1) * self.pitch_prev 
        ) / (1 + zeta * omega0 * dt)
        
        pitch_new = np.clip(pitch_new, pitch_min, pitch_max)
        
        self.pitch_prev = pitch_current
        
        # update the pitch of the structure
        # broadcast scalar setpoint to all blades
        simulation.structure.pitch[:] = [pitch_new] * len(simulation.structure.pitch)

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