from abc import ABC, abstractmethod
import warnings

import numpy as np
from numpy import cos, sin, sqrt, arctan2, pi, arccos, arcsin
from scipy.interpolate import interp1d
import pandas as pd

from rotation import Rotation
from wind import Wind
from structure import Structure
from airfoils import airfoils

class Aero:
    """
    Calculate aerodynamic properties like:
    - velocity triangle
    - 2d aerodynamics: lift, drag, spanwise loads py pz
    - update induced wind from momentum equations
    
    Attributes:
        Vrel (type): Relative velocity vector.
        W (type): Induced velocity vector.
        V0 (type): Free stream velocity vector.
        phi (type): Flow angle in radians.
        aoa (type): Angle of attack in radians.
        twist (type): Blade twist angle in radians.
        pitch (type): Blade pitch angle in radians.
        cl (type): Lift coefficient.
        cd (type): Drag coefficient.
        lift (type): Lift force.
        drag (type): Drag force.
        chord (type): chord length
        p_z (type): spanwise load z direction
        p_y (type): spanwise load y direction
        a (type): axial induction factor
        f_g (type): Glauert correction factor
        F (type): Prandtl tip loss factor
        RHO (type): Air density in kg/m^3
    
    """
    
    # Class attributes (shared by all instances)
    RHO = 1.225
    
    def __init__(self,
                 V_hub,
                 glauert = False,
                 use_dyn_wake = False,
                 use_dyn_stall = False,
                 use_wake_effects: bool | str = True,
                 use_structural_dynamics: bool | str = False) -> None:
           
           """Initialize the Aero class with given parameters."""
           self.V_hub = V_hub
           self.rotor = None
           self.use_dyn_wake = use_dyn_wake
           self.use_dyn_stall = use_dyn_stall
           self.use_wake_effects = use_wake_effects
           self.use_structural_dynamics = use_structural_dynamics
           self._wake_r_idx = 0


    def step(self, simulation):
        """
        Perform some operation on instance data.
        
        Args:
            arg (type): Description.
        
        Returns:
            return_type: Description of return value.
        
        Raises:
            ValueError: If invalid input.
        """
        # Method logic here
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
        

            B = len(self.rotor.blades)
            
            for blade in self.rotor.blades:
                blade.w_qs_prev[:] = blade.w_qs

                # Read pitch dynamically for time-varying pitch
                blade.pitch = simulation.structure.pitch[blade.blade_idx]
                
                xyz = simulation.structure.blade_x1(blade.blade_idx)
                
                blade_v0_1 = simulation.wind(xyz)
                
                # transform to coordinate system 5
                blade.v0 = simulation.structure.x15(blade_v0_1, blade.blade_idx)

                blade.v0 = blade.v0.T # make shape (n_sections, 2) for easier handling in calculations

                blade.v0 = np.array([blade.v0[1], blade.v0[2]]) # only y and z components are relevant for calculations, shape (2, n_sections)
                
                omega = simulation.structure.omega_shaft
                cone = simulation.structure.cone
                x = blade.r
                
                u5_blade = simulation.structure.blade_u5(blade.blade_idx)

                # calculate relative velocity components with previous induced velocities
                if self.use_dyn_wake:
                    blade.vrel[0] = blade.v0[0]+ blade.w[0] - u5_blade[:, 1] # y 
                    blade.vrel[1] = blade.v0[1] + blade.w[1] - u5_blade[:, 2] #z
                else:
                    blade.vrel[0] = blade.v0[0]+ blade.w_qs_prev[0] - u5_blade[:, 1] # y 
                    blade.vrel[1] = blade.v0[1] + blade.w_qs_prev[1] - u5_blade[:, 2] #z
                

                # calculate norm of relative velocity
                norm_vrel = np.linalg.norm(blade.vrel, axis=0)
                norm_vrel = np.maximum(norm_vrel, 1e-6)  # Prevent zero velocity
                
                # calculate flow angle
                phi = arctan2(blade.vrel[1], -blade.vrel[0]) # in radians

                # calculate angle of attack
                # print("blade pitch = ", blade.pitch)
                aoa = np.degrees(phi)-(blade.twist+blade.pitch)
                

                cl = airfoils.cl_stat_interp((aoa, blade.tc))
                cd = airfoils.cd_stat_interp((aoa, blade.tc))

                # interpolate cl and cd from airfoil data
                if self.use_dyn_stall:
                    cl, blade.fs = self.dyn_stall(simulation, aoa, norm_vrel, blade)                
                            
                # calculate lift and drag per unit length
                lift = 0.5*self.RHO*norm_vrel**2*blade.chord*cl       
                drag = 0.5*self.RHO*norm_vrel**2*blade.chord*cd

                # calculate spanwise loads
                blade.p[0] = lift*sin(phi)-drag*cos(phi)
                blade.p[1] = lift*cos(phi)+drag*sin(phi)

                blade.p[:,-1] = float(0.0) # set loads to 0 at tip

                # estimate local induction factor
                if self.use_dyn_wake:
                    a = -blade.w[1] / self.V_hub
                else:
                    a = -blade.w_qs[1] / self.V_hub
                
                # calculate glauert correction factor ( if statement on array)
                f_g = np.where(a <= 1/3, 1, 1/4 * (5 - 3*a))
                
                # calculate Prandtl tip loss F
                R = simulation.structure.R
                r = blade.r
                r_nd = r/R # mitigatio when r=0
                
                sin_phi = np.maximum(np.sin(np.abs(phi)), 1e-6)
                F = 2/pi * arccos(np.exp(-B/2*(1-r_nd)/(r_nd * sin_phi)))

                # calculate v0+fg*Wn to insert easily into formula for Wz_qs
                
                if self.use_dyn_wake:
                    w_z_term = f_g * blade.w[1]
                else:
                    w_z_term = f_g * blade.w_qs[1]
                mag_v0_fW = sqrt(blade.v0[0]**2 + (blade.v0[1] + w_z_term)**2)
                
                # Add small epsilon to prevent division by zero 
                denominator = np.maximum(4*pi*self.RHO*r*F*mag_v0_fW, 1e-5)
                # calculate quasi steady induction wind 
                blade.w_qs[0] = (-B*lift*sin(phi)) / denominator
                blade.w_qs[1] = (-B*lift*cos(phi)) / denominator

                
                #TODO: update sec. yaw to mean over blade sections instead of 0.7R
                if self.use_wake_effects and simulation.structure.yaw != 0:
                    blade_azi = simulation.structure.blade_azimuth(blade.blade_idx)
                    d_azi = blade_azi - simulation.structure.max_downstream_azi
                    if self.use_wake_effects == "geometrical" or self.use_wake_effects is True:
                        # take the mean over the blades, at the radius where the wake effects are calculated (0.7R)
                        W_wake_yz = np.mean([b.w[:, self._wake_r_idx] for b in self.rotor.blades],axis=0)  # shape (2,) -> [Wy, Wz]

                        # rotation functions expect 3D vectors, prepend x=0
                        W_wake5 = np.array([0.0, W_wake_yz[0], W_wake_yz[1]])

                        W_wake2 = Rotation.rotate_3d_y(W_wake5, simulation.structure.tilt)
                        W_wake1 = Rotation.rotate_3d_x(W_wake2, simulation.structure.yaw)
                        V_wake = np.asarray([0, 0, simulation.wind.v_hub_mean]) + W_wake1
                        chi = np.arccos(np.dot(simulation.structure.rotor_normal, V_wake) / np.linalg.norm(V_wake))

                    elif self.use_wake_effects == "empirical":
                        Ct = self.rotor._thrust / (0.5 * self.RHO * np.pi * R**2 * simulation.wind.v_hub_mean**2)
                        a_glob = 0.246 * Ct + 0.0586 * Ct**2 + 0.0883 * Ct**3
                        chi = (0.6 * a_glob + 1) * simulation.structure.yaw
                    else:
                        raise NotImplementedError(f"{self.use_wake_effects=} but implemented are 'geometrical', 'empirical'.")
                    blade.w_qs *= 1 + blade.r / R * np.tan(chi / 2) * np.cos(d_azi)
                    


                if self.use_dyn_wake:
                    blade.w, blade.w_int = self.dyn_wake(simulation,
                                                        blade.w_qs,
                                                        blade.w_qs_prev,
                                                        blade.w_int,
                                                        blade.w,
                                                        a,
                                                        R,
                                                        self.V_hub, 
                                                        r)

                r_eff = blade.r * cos(cone) # effective radius 
                # compute thrust
                blade._thrust = np.trapezoid(blade.p[1], r_eff)
                blade._torque = np.trapezoid(blade.p[0]*r_eff, r_eff)
                blade._power = blade._torque * omega

            # sum thrust, torque and power over blades
            self.rotor._torque = sum(blade._torque for blade in self.rotor.blades)
            self.rotor._thrust = sum(blade._thrust for blade in self.rotor.blades)
            self.rotor._power = sum(blade._power for blade in self.rotor.blades)

    def simulation_init(self, simulation):
        self.no_blades = simulation.structure.n_blades
        self.no_blade_sections = len(simulation.structure.r)
        self.rotor = Rotor(simulation, self.no_blades, self.no_blade_sections)
        self._wake_r_idx = np.argmax(self.rotor.blades[0].r >= simulation.structure.R * 0.7)  # used for the geometrical wake effects


    def dyn_wake(self, simulation, w_qs, w_qs_prev, w_int, w, a, R, V_hub, r):
        """
        Calculate the dynamic wake effect on the induced velocity using a simple first-order model.

        Parameters
        ----------
        simulation : Simulation
            The simulation object containing the current state of the simulation.
        w_qs : np.ndarray
            The quasi-steady induced velocities calculated from the current blade loads.
        w_ws_prev : np.ndarray
            The induced velocities from the previous time step.
        a : float
            The axial induction factor.
        R : float
            The rotor radius.
        V0 : float
            The free-stream wind velocity.
        r : float
            The radial position of the blade section.
        Returns
        -------
        w : np.ndarray
            The updated induced velocities accounting for dynamic wake effects.
        """
        dt = simulation.dt
        k = 0.6
        a = np.clip(a, 0, 0.5)  # Element-wise minimum
         # Protect against division by zero in tau_1 and V0
        tau_1 = 1.1 / (1 - 1.3 * a) * R / V_hub
        # print("tau_1", tau_1[10])
        tau_2 = (0.39-0.26*(r/R)**2)*tau_1
        # print("tau_2", tau_2[10])

        # Estimate rhs of eq3
        d_w_qs = (w_qs-w_qs_prev)/dt
        H = w_qs + k*tau_1*d_w_qs

        # solve eq3 analytically
        w_int = H + (w_int-H)*np.exp(-dt/tau_1)
        # solve eq4 analytically
        w = w_int + (w-w_int)*np.exp(-dt/tau_2)

        return w, w_int

    def dyn_wake_emil(self, simulation, w_qs, w_qs_prev, w_int, w, a, R, V_hub, r):
        dt = simulation.dt
        k = 0.6    # empirical constant

        w_qs_y = w_qs[0]
        w_qs_z = w_qs[1]

        w_qs_prev_y = w_qs_prev[0]
        w_qs_prev_z = w_qs_prev[1]

        w_int_y = w_int[0]
        w_int_z = w_int[1]

        w_y = w[0]
        w_z = w[1]

        # Use axial induction a = -Wn / V0  (slide). In the code, the "normal/axial" induction is the z-component (W[...,2]).
        # Use the actual W from previous step (NOT W_sq).
        a = - w_z / V_hub       # NOTE that W is not sq here, wake model dependent
        a = np.clip(a, 0, 0.5) #np.minimum(a, 0.5)    # slide note: a must not exceed 0.5

        # time constants
        tau1 = (1.1 / (1 - 1.3*a)) * (R / V_hub)     # Eq (5)
        tau2 = (0.39 - 0.26*(r/R)**2) * tau1 # Eq (6)

        # --- Eq (3): compute H using backward difference of W_sq
        dWqs_dt_y = (w_qs_y - w_qs_prev_y) / dt
        dWqs_dt_z = (w_qs_z - w_qs_prev_z) / dt

        H_y = w_qs_y + k * tau1 * dWqs_dt_y
        H_z = w_qs_z + k * tau1 * dWqs_dt_z

        # Solve Eq (3) analytically
        exp1 = np.exp(-dt / tau1)
        w_int_y = H_y + (w_int_y - H_y) * exp1
        w_int_z = H_z + (w_int_z - H_z) * exp1

        # Solve Eq (4) analytically
        exp2 = np.exp(-dt / tau2)
        w_y = w_int_y + (w_y - w_int_y) * exp2
        w_z = w_int_z + (w_z - w_int_z) * exp2

        w = np.array([w_y, w_z])
        w_int = np.array([w_int_y, w_int_z])

        return w, w_int

    def dyn_stall(self, simulation, aoa, vrel, blade):
        
        cl_inv = airfoils.cl_inv_interp((aoa, blade.tc))
        cl_fs = airfoils.cl_fs_interp((aoa, blade.tc))
        fs_stat = airfoils.f_stat_interp((aoa, blade.tc))
        A = 4.0 # Typical empirical constant for dynamic stall model
        tau = A*blade.chord/vrel 
        blade.fs = fs_stat + (blade.fs-fs_stat)*np.exp(-simulation.dt/tau)
        cl = blade.fs*cl_inv + (1-blade.fs)*cl_fs
        return cl, blade.fs

class Rotor:    

    def __init__(self, simulation, no_blades, no_blade_sections) -> None:
        self._torque = 0.0
        self._thrust = 0.0
        self._power = 0.0
        self.blades = []
        for i in range(no_blades):
             self.blades.append(Blade(simulation, i, no_blade_sections))

class Blade:

    def __init__(self, simulation, blade_idx, blade_sections) -> None:
        
        self.blade_idx = blade_idx # blade index
        self.w_qs       = np.zeros((2, blade_sections)) # quasi-steady induced velocity
        self.w_qs_prev  = np.zeros((2, blade_sections)) # quasi-steady induced velocity from previous time step, used for dynamic wake calculation
        self.w_int      = np.zeros((2, blade_sections)) # intermediate variable for dynamic wake calculation
        self.w          = np.zeros((2, blade_sections)) # induced velocity with dynamic wake effects
        self.vrel       = np.zeros((2,blade_sections)) # relative velocity
        self.v0         = np.zeros((2,blade_sections)) # free stream velocity
        
        self.p          = np.zeros((2,blade_sections)) # pressure distribution along the blade

        self.fs         = np.zeros(blade_sections) # dynamic stall state variable, between 0 and 1, where 1 means fully stalled and 0 means no stall. Updated in dyn_stall function.

        # blade data from structure for easy access in the step function
        self.chord = simulation.structure.c # chord distribution along the blade
        self.r = simulation.structure.r # radial positions of blade sections
        self.R = simulation.structure.R # rotor radius
        self.twist = simulation.structure.twist # twist distribution along the blade
        self.tc = simulation.structure.tc # thickness to chord ratio distribution along the blade
        # outcommented for dynamic pitch
        # self.pitch = simulation.structure.pitch[self.blade_idx]


        self._thrust = 0.0 
        self._torque = 0.0
        self._power = 0.0

    @property
    def get_p(self):
        return self.p
    
    @property
    def thrust(self):
        return np.trapezoid(self.p[1], self.r)

    @property
    def torque(self):
        return np.trapezoid(self.p[0]*self.r, self.r)
    
    def power(self, simulation):
        return self.torque * simulation.structure.omega_shaft