from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from rotation import Rotation
import re

class Structure(ABC):
    """
    Base (parent) class for the structure. This is not supposed to be used during the simulations. Using the @abstractmethod line defines which methods the children classes need to implement.

    This class defines some functionalities that are useful for the child classes (RigidStructure and at some
    point a flexible structure).
    """

    def __init__(
        self,
        omega_init=0.0,        
        file_blade="data/blade_data.csv",
        hub_height=119.0,
        bot_thickness = 3.32,
        top_thickness = 3.32,
        l_shaft=7.1,
        cone=0.0,
        yaw=0.0,
        tilt=0.0,
        pitch_init=[0.0, 0.0, 0.0],
        inertia_rotor=1.6e8,
    ) -> None:
        """
        Sets up some instance variables for the child classes.

        Parameters
        ----------
        omega_init : float, optional
            The initial rotational speed of the rotor, by default 0.0
        file_blade : str, optional
            Path to the file defining the blade structure. The path is expected to be a csv file
            with columns `r,c,twist,rel_thickness` for the radial position `r`, chord `c`, twist `twist`, and
            relative thickness `rel_thickness`, by default "data/blade_data.csv"
        hub_height : float, optional
            Hub height of the wind turbine, by default 119.0
        bot_thickness : float, optional
            bottom thickness of tower, default 3.32
        top_thickness : float, optional
            top thickness of tower, default 3.32
        l_shaft : float, optional
            Length of the shaft, by default 7.1
        cone : float, optional
            Coning of the rotor, by default 0.0
        yaw : float, optional
            Yaw of the rotor, by default 0.0
        tilt : float, optional
            Tilt of the shaft, by default 0.0
        pitch_init : list, optional
            The initial pitch angles for each blade. From this, the number of blades are defined, by default [0, 0, 0]
        """
        # self.r  = pd.read_csv(file_blade)["r"].to_numpy()
        # self.c = pd.read_csv(file_blade)["c"].to_numpy()
        # self.twist = pd.read_csv(file_blade)["twist"].to_numpy()
        # self.tc = pd.read_csv(file_blade)["rel_thickness"].to_numpy()

        blade_data = pd.read_csv(file_blade)

        self.r_old = blade_data["r"].to_numpy()
        c_old = blade_data["c"].to_numpy()
        twist_old = blade_data["twist"].to_numpy()
        tc_old = blade_data["rel_thickness"].to_numpy()

        # 1 m grid, starting at r=1 m
        dr = 1.0
        r_new = np.arange(1.0, np.floor(self.r_old[-1]) + 1.0, dr)  # 1,2,3,...,89

        # Interpolate (constant extrapolation at the left boundary)
        self.r = r_new
        self.c = np.interp(r_new, self.r_old, c_old, left=c_old[0], right=c_old[-1])
        self.twist = np.interp(r_new, self.r_old, twist_old, left=twist_old[0], right=twist_old[-1])
        self.tc = np.interp(r_new, self.r_old, tc_old, left=tc_old[0], right=tc_old[-1])

        # Optional: no blade below original root radius
        root_mask = self.r < self.r_old[0]
        self.c[root_mask] = 0.0

        self.R = self.r[-1]
        self.A = np.pi * self.R**2
        self.r_hub = self.r[0]

        self.hub_height = hub_height
        self.bot_thickness = bot_thickness
        self.top_thickness = top_thickness
        self.l_shaft = l_shaft
        self._cone = np.deg2rad(cone)
        self._yaw = np.deg2rad(yaw)
        self._tilt = np.deg2rad(tilt)
        self.n_blades = len(pitch_init)
        self.pitch = pitch_init

        self.phi_shaft = 0
        self.omega_shaft = omega_init
        self.inertia_rotor = inertia_rotor
        self.nacelle_mass = 446e3
        self._x5_blade = np.c_[self.r, np.zeros_like(self.r), np.zeros_like(self.r)]

        self.max_downstream_azi = self._max_downstream_azimuth(self._yaw, self._tilt)
        self.rotor_normal = self._rotor_normal(self.yaw, self.tilt)

        self.tower_radius = np.asarray([
            [0, bot_thickness],
            [hub_height, top_thickness],
            ]
        )


    @abstractmethod
    def step(self, simulation):
        pass

    @abstractmethod
    def blade_x1(self, blade_idx: int) -> np.ndarray:
        """
        Returns the coordinates of blade number `blade_idx` in the coordinate system 1.

        Parameters
        ----------
        blade_idx : int
            Index of blade.

        Returns
        -------
        np.ndarray
            The coordinates of the blade in coordinate system 1 as [x, y, z].
        """
        pass

    @abstractmethod
    def blade_u5(self, blade_idx: int) -> np.ndarray:
        """
        The velocities only due to the motion of the blade in the blade coordinate system.

        Parameters
        ----------
        blade_idx : int
            Blade index for which to get the velocities.

        Returns
        -------
        np.ndarray
            Velocities as numpy array as [u, v, w] in coordinate system 5.
        """
        pass

    
    @abstractmethod
    def x15(self, array: np.ndarray, blade_idx: int) -> np.ndarray:
        """
        Transforms an array from coordinate system 1 into the blade coordinate system 5.

        Parameters
        ----------
        array : np.ndarray
            The array with shape (n, 3) where each row is in the directions [x, y, z]
        blade_idx : int
            Blade index.

        Returns
        -------
        np.ndarray
            The transformed array in the blade coordinate system.
        """
        pass

    @property
    def yaw(self):
        return self._yaw

    @property
    def tilt(self):
        return self._tilt

    @property
    def cone(self):
        return self._cone

    @yaw.setter
    def yaw(self, yaw):
        self._set_angle("_yaw", yaw)

    @cone.setter
    def cone(self, cone):
        self._set_angle("_cone", cone)

    @tilt.setter
    def tilt(self, tilt):
        self._set_angle("_tilt", tilt)


    def blade_azimuth(self, blade_idx):
        if blade_idx > self.n_blades:
            raise ValueError(f"Structure only has '{self.n_blades}' blades, but {blade_idx=}.")
        return self.phi_shaft + blade_idx * 2 * np.pi / self.n_blades

    def _set_angle(self, angle_name: str, angle_value: float):
        """
        Set the angle `angle_name` of the instance to the value `np.deg2rad(value)`. Afterwards, update
        `max_downstream_azimuth` and `rotor_normal`.

        Parameters
        ----------
        angle_name : str
            Name of the angle attribute of the `StructureBase` instance.
        angle_value : float
            Angle in radians.
        """
        setattr(self, angle_name, np.deg2rad(angle_value))
        self.max_downstream_azimuth = self._max_downstream_azimuth(self.yaw, self.tilt)
        self.rotor_normal = self._rotor_normal(self.yaw, self.tilt)

    @staticmethod
    def _max_downstream_azimuth(yaw: float, tilt: float) -> float:
        if np.isclose(tilt, 0):  # Equation from the lecture doesn't hold for tilt=0.
            return np.pi / 2 if yaw >= 0 else -np.pi / 2
        return np.arctan(-np.tan(yaw) / (np.sin(tilt)))

    @staticmethod
    def _rotor_normal(yaw: float, tilt: float) -> np.ndarray:
        # Cone doesn't influence the rotor normal for the wake skew calculation
        normal4 = np.asarray([0, 0, 1])
        normal2 = Rotation.rotate_3d_y(normal4, tilt)
        return Rotation.rotate_3d_x(normal2, yaw)

class RigidStructure(Structure):

    def __init__(
        self,
        omega_init=0.0,
        file_blade="data/blade_data.csv",
        hub_height=119,
        bot_thickness=3.32,
        top_thickness=3.32,
        l_shaft=7.1,
        cone=0.0,
        yaw=0.0,
        tilt=0.0,
        pitch_init=[0.0, 0.0, 0.0],
        drive_train_dynamics=False,
    ) -> None:
        """
        Creates an instance for a rigid wind turbine.

        Parameters
        ----------
        omega_init : float, optional
            The initial rotational speed of the rotor, by default 0.0
        file_blade : str, optional
            Path to the file defining the blade structure. The path is expected to be a csv file
            with columns `r,c,twist,rel_thickness` for the radial position `r`, chord `c`, twist `twist`, and
            relative thickness `rel_thickness`, by default "data/blade_data.csv"
        hub_height : float, optional
            Hub height of the wind turbine, by default 119.0
        l_shaft : float, optional
            Length of the shaft, by default 7.1
        cone : float, optional
            Coning of the rotor, by default 0.0
        yaw : float, optional
            Yaw of the rotor, by default 0.0
        tilt : float, optional
            Tilt of the shaft, by default 0.0
        pitch_init : list, optional
            The initial pitch angles for each blade. From this, the number of blades are defined, by default [0, 0, 0]
        drive_train_dynamics : bool, optional
            Whether or not to include drive train dynamics, by default False
        """
        self.tower_radius = np.asarray([
            [0, bot_thickness],
            [hub_height, top_thickness],
            ]
        )
        super().__init__(
            omega_init=omega_init,
            file_blade=file_blade,
            hub_height=hub_height,
            bot_thickness=bot_thickness,
            top_thickness=top_thickness,
            l_shaft=l_shaft,
            cone=cone,
            yaw=yaw,
            tilt=tilt,
            pitch_init=pitch_init,
        )

        self.drive_train_dynamics = drive_train_dynamics

    def step(self, simulation):
        """
        Advances the structure one time step.

        Parameters
        ----------
        simulation : Simulation
            The simulation object

        Raises
        ------
        NotImplementedError
            Drive train dynamics are not yet implemented.
        """
        if not self.drive_train_dynamics:
            self.phi_shaft += self.omega_shaft * simulation.dt
        else:
            raise NotImplementedError("You'll have to implement the drive train dynamcis at some point :)")
        
        # # Update time-varying pitch if a pitch schedule is defined
        # if hasattr(self, 'pitch_schedule') and self.pitch_schedule is not None:
        #     self.pitch = self.pitch_schedule(simulation.time)

    def blade_x1(self, blade_idx: int) -> np.ndarray:
        """
        Returns the coordinates of blade number `blade_idx` in the coordinate system 1.

        Parameters
        ----------
        blade_idx : int
            Index of blade.

        Returns
        -------
        np.ndarray
            The coordinates of the blade in coordinate system 1 as [x, y, z].
        """
        x4_blade = Rotation.rotate_3d_y(self._x5_blade, self.cone)
        x3_blade = Rotation.rotate_3d_z(x4_blade, self.blade_azimuth(blade_idx))
        x2_blade = Rotation.rotate_3d_y(x3_blade + np.asarray([0, 0, -self.l_shaft]), self.tilt)
        return Rotation.rotate_3d_x(x2_blade + np.asarray([self.hub_height, 0, 0]), self.yaw)

    def blade_u5(self, blade_idx: int) -> np.ndarray:
        """
        The velocities only due to the motion of the blade in the blade coordinate system.

        Parameters
        ----------
        blade_idx : int
            Blade index for which to get the velocities.

        Returns
        -------
        np.ndarray
            Velocities as numpy array as [u, v, w] in coordinate system 5.
        """
        # wr = self.omega_shaft * self.r
        # pitch_rad = np.deg2rad(self.pitch[blade_idx])  # convert degrees to radians
        # v = np.cos(pitch_rad) * wr
        # w = np.sin(pitch_rad) * wr
        # #TODO CHANGE THIS WITH ASSIGNMENT 1 UPLOAD
        # return np.c_[np.zeros_like(self.r), v, w]
        return np.c_[np.zeros_like(self.r), self.omega_shaft * self.r, np.zeros_like(self.r)]


    def x15(self, array: np.ndarray, blade_idx: int) -> np.ndarray:
        """
        Transforms an array from coordinate system 1 into the blade coordinate system 5.

        Parameters
        ----------
        array : np.ndarray
            The array with shape (n, 3) where each row is in the directions [x, y, z]
        blade_idx : int
            Blade index.

        Returns
        -------
        np.ndarray
            The transformed array in the blade coordinate system.
        """
        x2 = Rotation.rotate_3d_x(array, -self.yaw)
        x3 = Rotation.rotate_3d_y(x2, -self.tilt)
        x4 = Rotation.rotate_3d_z(x3, -self.blade_azimuth(blade_idx))
        return Rotation.rotate_3d_y(x4, -self.cone)

class FlexibleStructure5DOF(Structure):
    """
        5DOF aeroelastic wind turbine model (Lecture 10).

        State vector GX = (x_tow, theta, q1_b0, q2_b0, q3_b0)
        x_tow  : tower fore-aft displacement [m]
        theta  : rotor azimuth [rad] — full dynamic DOF driven by aero torque - gen torque
        q1..q3 : modal amplitudes of blade 0 (1F, 1E, 2F)
        Blades 1 and 2 are rigid.

        The full 5x5 coupled system M(pitch)*GX'' + C*GX' + K*GX = GF is solved
        in a single Newmark-beta step each timestep.
    """
    # Class constants for 5DOF model
    # only blade 1/0 is flexible so:
    FLEX_BLADE_IDX = 0
    NO_BLADE_MODES = 3 # 1F, 1E, 2F
    TOWER_DOF = 2 # tower fore-aft and azimuth
    BLADE_MODE_START_IDX = 2
    BLADE_MODE_END_IDX = 5
    DOF = 5
    
    #NOTE GM1: flapwise 1, gm2: e1, gm3: f2
    def __init__(
        self,
        omega_init=0.0,
        file_blade="data/blade_data.csv",
        hub_height=119,
        bot_thickness=3.32,
        top_thickness=3.32,
        l_shaft=7.1,
        cone=0.0,
        yaw=0.0,
        tilt=0.0,
        pitch_init=[0.0, 0.0, 0.0],
        inertia_rotor=1.6e8,
        omega_modes=[3.93, 6.10, 11.28],
        tower_stiffness=1.7e6,
        nacelle_mass=446000.0,
        zeta_modal=0.0,
        zeta_tower=0.0,
        use_gravity=True,
        file_modes="data/modeshapes.txt"):
        super().__init__(
            omega_init=omega_init,
            file_blade=file_blade,
            hub_height=hub_height,
            bot_thickness=bot_thickness,
            top_thickness=top_thickness,
            l_shaft=l_shaft,
            cone=cone,
            yaw=yaw,
            tilt=tilt,
            pitch_init=pitch_init,
            inertia_rotor=inertia_rotor)
        
        # Make sure that the flexible structure controls the rotor speed
        self.omega_from_structure = True
        
        self.omega_modes = np.asarray(omega_modes, dtype=float)
        self.tower_stiffness = float(tower_stiffness)  # N/m
        self.nacelle_mass = float(nacelle_mass)
        self.zeta_modal  = float(zeta_modal)
        self.zeta_tower  = float(zeta_tower)
        self.use_gravity = bool(use_gravity)
        self.g = 9.81 # gravity acceleration in m/s^2
        
        # load modeshapes and frequencies from file
        # # lets use 
        # (self.u1_flap, self.u1_edge, self.u2_flap,
        #  self.m,
        #  self.omega1f, self.omega1e, self.omega2f) = self.read_modeshapes_file(file_modes)
        modeshapes = np.loadtxt(file_modes, comments="#")
        r_ms = modeshapes[:, 0]
        self.u_y = np.array([
            np.interp(self.r, r_ms, modeshapes[:, 1]), # u1fy
            np.interp(self.r, r_ms, modeshapes[:, 3]), # u1ey
            np.interp(self.r, r_ms, modeshapes[:, 5])  # u2fy
        ])
        self.u_z = np.array([
            np.interp(self.r, r_ms, modeshapes[:, 2]), # u1fz
            np.interp(self.r, r_ms, modeshapes[:, 4]), # u1ez
            np.interp(self.r, r_ms, modeshapes[:, 6])  # u2fz
        ])
        self.m = np.interp(self.r, r_ms, modeshapes[:, 7]) # kg/m
        
        # Calculate the total blade mass by integrating the mass distribution along the blade, used for the effective mass of the tower-blade system.
        self.blade_mass = np.trapezoid(self.m, self.r)   # single blade mass [kg]

        # The effective mass of the tower-blade system is the nacelle mass plus the mass of all blades, used for the tower dynamics and natural frequency calculations.
        self.M_eff   = self.nacelle_mass + self.n_blades * self.blade_mass
        
        # For now C is zero, but it could be implemented as well if we want to include damping in the system.
        self.C_sys = np.zeros((self.DOF, self.DOF))

        
        self.GF = np.zeros(self.DOF)
        # State vector: GX = [x_tow, theta, q1_b0, q2_b0, q3_b0] = tower deflection, rotor azimuth, modal amplitudes of blade 0 (1F, 1E, 2F)
        self.GX = np.zeros(self.DOF)
        self.GX_dot = np.zeros(self.DOF)
        self.GX_ddot = np.zeros(self.DOF)
        self.GX_dot[1] = self.omega_shaft  # set initial condition for theta_dot
        
        # Initialize outputs so recorders can access them before the first step
        self.deflection_y = np.zeros(len(self.r))
        self.deflection_z = np.zeros(len(self.r))
        self.M_bend_y = 0.0
        self.M_bend_z = 0.0
        self.tower_displacement = 0.0
        self.tower_azimuth = 0.0


        # initialize constants from avg. acceleration method (Newmark-beta) for time integration
        self.beta = 0.25
        self.gamma = 0.5
        self.tolerance_r = 1e-6
        self.tolerance_u = 1e-6
        # self.delta_u = np.ones_like(self.x) # initialize delta_u to enter the while loop
        self.max_iter = 600

    def _pitch_rotated_modes(self):
        """Rotate mode shapes about the spanwise (x5) axis by pitch angle."""
        c, s = np.cos(np.deg2rad(self.pitch[self.FLEX_BLADE_IDX])), np.sin(np.deg2rad(self.pitch[self.FLEX_BLADE_IDX]))
        u_y_R = self.u_y * c + self.u_z * s
        u_z_R = self.u_z * c - self.u_y * s
        return u_y_R, u_z_R
                 
    def _calc_GM(self, u_y_R, u_z_R):
        """Calculate the modal mass for each mode at a given pitch, which is the integral of m*(Phi_y^2 + Phi_z^2) dr at a given pitch.
        This is used for the mass matrix and natural frequency calculations."""
        GM = np.array([
            np.trapezoid(self.m * (u_y_R[i]**2 + u_z_R[i]**2), self.r)
            for i in range(self.NO_BLADE_MODES)
        ])
        return GM

    def _build_K(self, GM):
        K = np.zeros((self.DOF, self.DOF))
        K[0, 0] = self.tower_stiffness
        for i in range(self.NO_BLADE_MODES):
            idx = self.BLADE_MODE_START_IDX + i
            K[idx, idx] = self.omega_modes[i]**2 * GM[i]
        return K

    def _build_M(self, GM, u_y_R, u_z_R):
        M = np.zeros((self.DOF, self.DOF))
        M[0, 0] = self.M_eff
        M[1, 1] = self.inertia_rotor

        for i in range(self.NO_BLADE_MODES):
            idx = self.BLADE_MODE_START_IDX + i
            c_ti = np.trapezoid(self.m * u_z_R[i], self.r)
            M[0, idx] = c_ti
            M[idx, 0] = c_ti
            c_ai = np.trapezoid(self.m * self.r * u_y_R[i], self.r)
            M[1, idx] = c_ai
            M[idx, 1] = c_ai
            M[idx, idx] = GM[i]

        return M


    def _build_GF(self, simulation, u_y_R, u_z_R):
        GF = np.zeros(self.DOF)

        T = simulation.aero.rotor._thrust
        GF[0] = float(T) if isinstance(T, (int, float, np.floating)) else 0.0

        Q_aero = simulation.aero.rotor._torque
        Q_gen  = simulation.controller.torque_gen
        GF[1]  = float(Q_aero) - float(Q_gen)

        # Average gravity over all blades (sum cancels for equally-spaced blades)
        if self.use_gravity:
            g1 = np.array([-self.g, 0.0, 0.0])
            g5 = self.x15(g1, self.FLEX_BLADE_IDX)
            Fg_y = g5[1] * self.m
            Fg_z = g5[2] * self.m
            # average over blades — or keep as sum if GF represents all blades
        else:
            Fg_y = np.zeros_like(self.r)
            Fg_z = np.zeros_like(self.r)

        # Extract the aerodynamic force distribution along the blade in the blade coordinate system
        if simulation.aero.rotor.blades[self.FLEX_BLADE_IDX].p is None:
            p_y = np.zeros_like(self.r)
            p_z = np.zeros_like(self.r)
        else:
            p_y = simulation.aero.rotor.blades[self.FLEX_BLADE_IDX].p[0]
            p_z = simulation.aero.rotor.blades[self.FLEX_BLADE_IDX].p[1]

        # Add gravitational force contributions to spanwise and flapwise loads (copies, not views)
        p_y = p_y + Fg_y
        p_z = p_z + Fg_z

        for i in range(self.NO_BLADE_MODES):
            idx = self.BLADE_MODE_START_IDX + i
            GF[idx] += np.trapezoid(p_y * u_y_R[i] + p_z * u_z_R[i], self.r)

        return GF
    
    def _newmark_step(self, simulation, M, C, K, GF, GX, GX_dot):
        """Newmark-beta average acceleration step (beta=0.25, gamma=0.5, unconditionally stable)."""
        # Newmark parameters
        beta = self.beta
        gamma = self.gamma
        dt = simulation.dt
        tolerance_r = self.tolerance_r
        max_iter = self.max_iter

        # (1) Calculate the initial acceleration based on the current state and generalized forces, used for predictor step
        GX_ddot = np.linalg.solve(M, GF - C @ GX_dot - K @ GX) 
        
        # (2) Predictor step: calculate predicted GX and GX_dot based on current state and acceleration
        GX_ddot_pred = GX_ddot  # predicted acceleration at time step n+1 used for converging n+1
        GX_dot_pred = GX_dot + dt * GX_ddot  # predicted velocity at time step n+1 used for converging n+1
        GX_pred = GX + dt * GX_dot + 0.5 * dt**2 * GX_ddot  
        
        # (3) Residual calculation and iteration for convergence:
        NOT_CONVERGED = True
        iter = 0
        
        while NOT_CONVERGED:
            iter += 1
            
            # Get the pitch-rotated mode shapes for the predicted state
            u_y_R_pred, u_z_R_pred = self._pitch_rotated_modes()
            
            # Update generalized force and mass and stiffness matrix based on the predicted state
            GF_pred = self._build_GF(simulation, u_y_R_pred, u_z_R_pred)
            GM_pred = self._calc_GM(u_y_R_pred, u_z_R_pred)
            M_pred = self._build_M(GM_pred, u_y_R_pred, u_z_R_pred)
            K_pred = self._build_K(GM_pred)
            
            # Calculate residual
            r = GF_pred - M_pred @ GX_ddot_pred - C @ GX_dot_pred - K_pred @ GX_pred
            r_max = max(abs(r))
            
            # (4) System matrices and increment correction:
            K_star = K_pred + gamma/(beta*dt)*C + 1/(beta*dt**2)*M_pred
            du = np.linalg.solve(K_star, r)
            
            # Update predicted GX, GX_dot, GX_ddot
            GX_pred += du
            GX_dot_pred += gamma/(beta*dt)*du
            GX_ddot_pred += 1/(beta*dt**2)*du
            
            # Print the residual and iteration number for debugging and also the K, M, 
            # and GF matrices to see how they change during the iterations
            # print(f"\nIteration {iter}: r_max = {r_max}")
            # print(f"\nK_pred = {K_pred}, M_pred = {M_pred}, GF_pred = {GF_pred}")
            # print(f"\nK = {K}, M = {M}, GF = {GF}")
            
            # NOTE: The matrices K, M, and GF are not changing, so we could simplify the code 
            # by calculating them only once before the iteration and not updating them during the iteration. 

            # Convergence check
            if r_max < tolerance_r:
                NOT_CONVERGED = False
                
            if iter > max_iter:
                raise ValueError('Warning! Convergence was not reached in step 4.')
        
        # Update step n+1 with the converged value
        GX_new = GX_pred
        GX_dot_new = GX_dot_pred
        GX_ddot_new = GX_ddot_pred
        
        return GX_new, GX_dot_new, GX_ddot_new
                        
    def blade_vibration(self):
        u_blade = self.q1[1] * self.u1_flap + self.q2[1] * self.u1_edge + self.q3[1] * self.u2_flap
        tower = np.array([0, self.z[1]])
        return u_blade, tower            
    
    def blade_x1(self, blade_idx: int) -> np.ndarray:
        """
        Returns the coordinates of blade number `blade_idx` in the coordinate system 1.

        Parameters
        ----------
        blade_idx : int
            Index of blade.

        Returns
        -------
        np.ndarray
            The coordinates of the blade in coordinate system 1 as [x, y, z].
        """
        
        # Blade 0 is elastic: include modal deflection. Blades 1 & 2 are rigid.
        if blade_idx == 0:
            c, s = np.cos(self.pitch[0]), np.sin(self.pitch[0])
            u_y_R = self.u_y * c + self.u_z * s
            u_z_R = self.u_z * c - self.u_y * s
            q = self.GX[2:5]
            x5 = np.c_[self.r, u_y_R.T @ q, u_z_R.T @ q]
        else:
            x5 = self._x5_blade

        x4_blade = Rotation.rotate_3d_y(x5, self.cone)
        x3_blade = Rotation.rotate_3d_z(x4_blade, self.blade_azimuth(blade_idx))
        x2_blade = Rotation.rotate_3d_y(x3_blade + np.asarray([0, 0, -self.l_shaft]), self.tilt)
        x1 = Rotation.rotate_3d_x(x2_blade + np.asarray([self.hub_height, 0, 0]), self.yaw)
        x1 += np.array([[0, 0, self.GX[0]]])  # tower fore-aft displacement (streamwise)
        return x1

    def blade_u5(self, blade_idx: int) -> np.ndarray:
        """
            The velocities only due to the motion of the blade in the blade coordinate system.

            Parameters
            ----------
            blade_idx : int
                Blade index for which to get the velocities.

            Returns
            -------
            np.ndarray
                Velocities as numpy array as [u, v, w] in coordinate system 5.
        """
        # Rotation: always purely edgewise (y5), independent of pitch
        u5 = np.c_[np.zeros_like(self.r), self.omega_shaft * self.r, np.zeros_like(self.r)]

        # Elastic modal velocity (only blade 0 is elastic in 5DOF)
        if blade_idx == 0:
            c, s = np.cos(self.pitch[0]), np.sin(self.pitch[0])
            u_y_R = self.u_y * c + self.u_z * s
            u_z_R = self.u_z * c - self.u_y * s
            q_dot = self.GX_dot[self.BLADE_MODE_START_IDX:self.BLADE_MODE_END_IDX]
            u5[:, 1] += q_dot @ u_y_R
            u5[:, 2] += q_dot @ u_z_R

        # Tower fore-aft velocity enters flapwise (z5) velocity triangle for all blades
        u5[:, 2] += self.GX_dot[0]
        return u5

    def x15(self, array: np.ndarray, blade_idx: int) -> np.ndarray:
        """
            Transforms an array from coordinate system 1 into the blade coordinate system 5.

            Parameters
            ----------
            array : np.ndarray
                The array with shape (n, 3) where each row is in the directions [x, y, z]
            blade_idx : int
                Blade index.

            Returns
            ------
            np.ndarray
                The transformed array in the blade coordinate system.
        """
        
        x2 = Rotation.rotate_3d_x(array, -self.yaw)
        x3 = Rotation.rotate_3d_y(x2, -self.tilt)
        x4 = Rotation.rotate_3d_z(x3, -self.blade_azimuth(blade_idx))
        
        return Rotation.rotate_3d_y(x4, -self.cone)

    def step(self, simulation):
        # Calculate the pitch-rotated mode shapes and modal masses for the current pitch angle
        u_y_R, u_z_R = self._pitch_rotated_modes()
        
        # Build the mass matrix M and stiffness matrix K for the current pitch angle
        GM = self._calc_GM(u_y_R, u_z_R)
        M = self._build_M(GM, u_y_R, u_z_R)
        K = self._build_K(GM)
        
        # Build the generalized force vector GF for the current simulation state
        GF = self._build_GF(simulation, u_y_R, u_z_R)
        
        # Perform a Newmark-beta step to solve for the new state GX, GX_dot, GX_ddot
        self.GX, self.GX_dot, self.GX_ddot = self._newmark_step(simulation, M, self.C_sys, K, GF, self.GX, self.GX_dot)
        
        # Calculate the bending moments at the blade root for blade 0
        r0 = self.r[0]                              # hub/root radius
        u_ddot_z = self.GX_ddot[self.BLADE_MODE_START_IDX:self.BLADE_MODE_END_IDX] @ u_z_R   # (19,) flapwise accel at each station
        u_ddot_y = self.GX_ddot[self.BLADE_MODE_START_IDX:self.BLADE_MODE_END_IDX] @ u_y_R   # (19,) edgewise accel at each station

        p_eff_y = simulation.aero.rotor.blades[self.FLEX_BLADE_IDX].p[0] - self.m * u_ddot_y
        p_eff_z = simulation.aero.rotor.blades[self.FLEX_BLADE_IDX].p[1] - self.m * u_ddot_z

        self.M_bend_y = np.trapezoid(p_eff_z * (self.r - r0), self.r)
        self.M_bend_z = np.trapezoid(p_eff_y * (self.r - r0), self.r)

        # Calculate blade deflection for blade 0
        self.deflection_y = u_y_R.T @ self.GX[self.BLADE_MODE_START_IDX:self.BLADE_MODE_END_IDX]   # shape (19,)
        self.deflection_z = u_z_R.T @ self.GX[self.BLADE_MODE_START_IDX:self.BLADE_MODE_END_IDX]   # shape (19,)
        
        # Update the shaft azimuth and speed from the state vector
        self.phi_shaft = self.GX[1]
        self.omega_shaft = self.GX_dot[1]

class FlexibleStructure11DOF(Structure):
    """
        11DOF aeroelastic wind turbine model.

        State vector GX = (x_tow, theta, q1_b0, q2_b0, q3_b0,
                                        q1_b1, q2_b1, q3_b1,
                                        q1_b2, q2_b2, q3_b2)
        x_tow      : tower fore-aft displacement [m]
        theta      : rotor azimuth [rad]
        q1..q3_bN  : modal amplitudes of blade N (1F, 1E, 2F)
        All three blades are elastic.

        The full 11x11 coupled system M(pitch)*GX'' + C*GX' + K*GX = GF is solved
        in a single Newmark-beta step each timestep.
    """
    
    # Class constants for 11DOF model
    NO_BLADE_MODES = 3      # 1F, 1E, 2F
    TOWER_DOF = 2           # tower fore-aft and azimuth
    BLADE_MODE_START_IDX = 2
    DOF = 11                # 2 + 3*3
    
    def __init__(
        self,
        omega_init=0.0,
        file_blade="data/blade_data.csv",
        hub_height=119,
        bot_thickness=3.32,
        top_thickness=3.32,
        l_shaft=7.1,
        cone=0.0,
        yaw=0.0,
        tilt=0.0,
        pitch_init=[0.0, 0.0, 0.0],
        inertia_rotor=1.6e8,
        omega_modes=[3.93, 6.10, 11.28],
        tower_stiffness=1.7e6,
        nacelle_mass=446000.0,
        zeta_modal=0.0,
        zeta_tower=0.0,
        use_gravity=True,
        file_modes="data/modeshapes.txt"
    ):
        super().__init__(
            omega_init=omega_init,
            file_blade=file_blade,
            hub_height=hub_height,
            bot_thickness=bot_thickness,
            top_thickness=top_thickness,
            l_shaft=l_shaft,
            cone=cone,
            yaw=yaw,
            tilt=tilt,
            pitch_init=pitch_init,
            inertia_rotor=inertia_rotor
        )
        
        # Make sure that the flexible structure controls the rotor speed
        self.omega_from_structure = True

        self.omega_modes     = np.asarray(omega_modes, dtype=float)
        self.tower_stiffness = float(tower_stiffness)
        self.nacelle_mass    = float(nacelle_mass)
        self.zeta_modal      = float(zeta_modal)
        self.zeta_tower      = float(zeta_tower)
        self.use_gravity = bool(use_gravity)
        self.g               = 9.81

        # Load mode shapes — columns: r, u1fy, u1fz, u1ey, u1ez, u2fy, u2fz, m
        modeshapes = np.loadtxt(file_modes, comments="#")
        r_ms = modeshapes[:, 0]
        self.u_y = np.array([
            np.interp(self.r, r_ms, modeshapes[:, 1]),   # u1fy
            np.interp(self.r, r_ms, modeshapes[:, 3]),   # u1ey
            np.interp(self.r, r_ms, modeshapes[:, 5]),   # u2fy
        ])
        self.u_z = np.array([
            np.interp(self.r, r_ms, modeshapes[:, 2]),   # u1fz
            np.interp(self.r, r_ms, modeshapes[:, 4]),   # u1ez
            np.interp(self.r, r_ms, modeshapes[:, 6]),   # u2fz
        ])
        self.m = np.interp(self.r, r_ms, modeshapes[:, 7])   # kg/m

        self.blade_mass = np.trapezoid(self.m, self.r)
        self.M_eff      = self.nacelle_mass + self.n_blades * self.blade_mass

        self.C_sys = np.zeros((self.DOF, self.DOF))

        self.GF      = np.zeros(self.DOF)
        self.GX      = np.zeros(self.DOF)
        self.GX_dot  = np.zeros(self.DOF)
        self.GX_ddot = np.zeros(self.DOF)
        self.GX_dot[1] = self.omega_shaft

        # Initialize outputs
        self.deflection_y = np.zeros((self.n_blades, len(self.r)))
        self.deflection_z = np.zeros((self.n_blades, len(self.r)))
        self.M_bend_y = np.zeros(self.n_blades)
        self.M_bend_z = np.zeros(self.n_blades)
        self.tower_displacement = 0.0
        self.tower_azimuth = 0.0

        # Newmark-beta parameters
        self.beta        = 0.25
        self.gamma       = 0.5
        self.tolerance_r = 1e-6
        self.tolerance_u = 1e-6
        # self.delta_u     = np.ones_like(self.x)
        self.max_iter    = 600

    def _blade_mode_slice(self, blade_idx: int) -> slice:
        """Return the GX slice for the modal DOFs of blade `blade_idx`."""
        start = self.BLADE_MODE_START_IDX + blade_idx * self.NO_BLADE_MODES
        return slice(start, start + self.NO_BLADE_MODES)

    def _pitch_rotated_modes(self):
        """Rotate mode shapes about the spanwise (x5) axis by pitch angle (collective)."""
        c = np.cos(np.deg2rad(self.pitch[0]))
        s = np.sin(np.deg2rad(self.pitch[0]))
        u_y_R = self.u_y * c + self.u_z * s
        u_z_R = self.u_z * c - self.u_y * s
        return u_y_R, u_z_R

    def _calc_GM(self, u_y_R, u_z_R):
        """Modal mass for each mode: integral of m*(u_y_R^2 + u_z_R^2) dr."""
        return np.array([
            np.trapezoid(self.m * (u_y_R[i]**2 + u_z_R[i]**2), self.r)
            for i in range(self.NO_BLADE_MODES)
        ])

    def _build_K(self, GM):
        """
        Build the 11x11 stiffness matrix K.
        GM : list/array of shape (n_blades, NO_BLADE_MODES) — modal masses per blade.
        """
        K = np.zeros((self.DOF, self.DOF))
        K[0, 0] = self.tower_stiffness
        for b in range(self.n_blades):
            s = self._blade_mode_slice(b)
            for i in range(self.NO_BLADE_MODES):
                idx = s.start + i
                K[idx, idx] = self.omega_modes[i]**2 * GM[i]
        return K

    def _build_M(self, GM, u_y_R, u_z_R):
        """
        Build the 11x11 mass matrix M.
        GM    : (NO_BLADE_MODES,) — modal masses (same for all blades, collective pitch)
        u_y_R : (NO_BLADE_MODES, n_r)
        u_z_R : (NO_BLADE_MODES, n_r)
        """
        M = np.zeros((self.DOF, self.DOF))
        M[0, 0] = self.M_eff
        M[1, 1] = self.inertia_rotor

        for b in range(self.n_blades):
            s = self._blade_mode_slice(b)
            for i in range(self.NO_BLADE_MODES):
                idx = s.start + i
                # Tower-blade coupling: integral m * u_z_R[i] dr
                c_ti = np.trapezoid(self.m * u_z_R[i], self.r)
                M[0, idx] = c_ti
                M[idx, 0] = c_ti
                # Azimuth-blade coupling: integral m * r * u_y_R[i] dr
                c_ai = np.trapezoid(self.m * self.r * u_y_R[i], self.r)
                M[1, idx] = c_ai
                M[idx, 1] = c_ai
                # Blade diagonal
                M[idx, idx] = GM[i]

        return M

    def _build_GF(self, simulation, u_y_R, u_z_R):
        """Build the 11-element generalized force vector GF."""
        GF = np.zeros(self.DOF)

        # Tower: total aerodynamic thrust
        T = simulation.aero.rotor._thrust
        GF[0] = float(T) if isinstance(T, (int, float, np.floating)) else 0.0

        # Azimuth: aero torque - generator torque
        Q_aero = simulation.aero.rotor._torque
        Q_gen  = simulation.controller.torque_gen
        GF[1]  = float(Q_aero) - float(Q_gen)

        for b in range(self.n_blades):
            s = self._blade_mode_slice(b)

            if self.use_gravity:
                g1 = np.array([-self.g, 0.0, 0.0])
                g5 = self.x15(g1, b)
                Fg_y = g5[1] * self.m
                Fg_z = g5[2] * self.m
            else:
                Fg_y = np.zeros_like(self.r)
                Fg_z = np.zeros_like(self.r)

            if simulation.aero.rotor.blades[b].p is None:
                p_y = np.zeros_like(self.r)
                p_z = np.zeros_like(self.r)
            else:
                p_y = simulation.aero.rotor.blades[b].p[0]
                p_z = simulation.aero.rotor.blades[b].p[1]

            p_y = p_y + Fg_y
            p_z = p_z + Fg_z

            for i in range(self.NO_BLADE_MODES):
                GF[s.start + i] += np.trapezoid(p_y * u_y_R[i] + p_z * u_z_R[i], self.r)

        return GF

    def _newmark_step(self, simulation, M, C, K, GF, GX, GX_dot):
        """Newmark-beta average acceleration step (beta=0.25, gamma=0.5, unconditionally stable)."""
        beta        = self.beta
        gamma       = self.gamma
        dt          = simulation.dt
        tolerance_r = self.tolerance_r
        max_iter    = self.max_iter

        GX_ddot = np.linalg.solve(M, GF - C @ GX_dot - K @ GX)

        GX_ddot_pred = GX_ddot
        GX_dot_pred  = GX_dot + dt * GX_ddot
        GX_pred      = GX + dt * GX_dot + 0.5 * dt**2 * GX_ddot

        NOT_CONVERGED = True
        iter_count = 0

        while NOT_CONVERGED:
            iter_count += 1

            # Get pitch-rotated mode shapes and modal masses (collective pitch — same for all blades)
            u_y_R_pred, u_z_R_pred = self._pitch_rotated_modes()
            GF_pred  = self._build_GF(simulation, u_y_R_pred, u_z_R_pred)
            GM_pred  = self._calc_GM(u_y_R_pred, u_z_R_pred)
            M_pred   = self._build_M(GM_pred, u_y_R_pred, u_z_R_pred)
            K_pred   = self._build_K(GM_pred)

            # Calculate the residual for the predicted state
            r     = GF_pred - M_pred @ GX_ddot_pred - C @ GX_dot_pred - K_pred @ GX_pred
            r_max = max(abs(r))

            K_star = K_pred + gamma / (beta * dt) * C + 1.0 / (beta * dt**2) * M_pred
            du     = np.linalg.solve(K_star, r)

            GX_pred      += du
            GX_dot_pred  += gamma / (beta * dt) * du
            GX_ddot_pred += 1.0 / (beta * dt**2) * du

            if r_max < tolerance_r:
                NOT_CONVERGED = False

            if iter_count > max_iter:
                raise ValueError('Warning! Convergence was not reached in Newmark step.')
            
            # update step n+1 with the converged value
            GX_new = GX_pred
            GX_dot_new = GX_dot_pred
            GX_ddot_new = GX_ddot_pred

        return GX_pred, GX_dot_pred, GX_ddot_pred

    def x15(self, array: np.ndarray, blade_idx: int) -> np.ndarray:
        """Transforms an array from coordinate system 1 into blade coordinate system 5."""
        x2 = Rotation.rotate_3d_x(array, -self.yaw)
        x3 = Rotation.rotate_3d_y(x2, -self.tilt)
        x4 = Rotation.rotate_3d_z(x3, -self.blade_azimuth(blade_idx))
        return Rotation.rotate_3d_y(x4, -self.cone)

    def blade_x1(self, blade_idx: int) -> np.ndarray:
        """Returns coordinates of blade `blade_idx` in coordinate system 1 (with elastic deflection)."""
        u_y_R, u_z_R = self._pitch_rotated_modes()  # collective pitch — same for all blades
        q  = self.GX[self._blade_mode_slice(blade_idx)]
        x5 = np.c_[self.r, u_y_R.T @ q, u_z_R.T @ q]

        x4_blade = Rotation.rotate_3d_y(x5, self.cone)
        x3_blade = Rotation.rotate_3d_z(x4_blade, self.blade_azimuth(blade_idx))
        x2_blade = Rotation.rotate_3d_y(x3_blade + np.asarray([0, 0, -self.l_shaft]), self.tilt)
        x1 = Rotation.rotate_3d_x(x2_blade + np.asarray([self.hub_height, 0, 0]), self.yaw)
        x1 += np.array([[0, 0, self.GX[0]]])
        return x1

    def blade_u5(self, blade_idx: int) -> np.ndarray:
        """Velocities due to blade motion in coordinate system 5."""
        # Rotation: edgewise (y5), scaled by cos(cone) to project onto rotation plane
        u5 = np.c_[np.zeros_like(self.r), self.omega_shaft * self.r * np.cos(self.cone), np.zeros_like(self.r)]

        # Elastic modal velocity — pitch-rotated mode shapes (collective pitch)
        u_y_R, u_z_R = self._pitch_rotated_modes()
        q_dot = self.GX_dot[self._blade_mode_slice(blade_idx)]
        u5[:, 1] += q_dot @ u_y_R
        u5[:, 2] += q_dot @ u_z_R

        # Tower fore-aft velocity enters flapwise (z5) for all blades
        u5[:, 2] += self.GX_dot[0]
        return u5

    def simulation_init(self, simulation):
        pass
    
    def step(self, simulation):
        # Collective pitch — one set of mode shapes for all blades
        u_y_R, u_z_R = self._pitch_rotated_modes()
        GM = self._calc_GM(u_y_R, u_z_R)
        M  = self._build_M(GM, u_y_R, u_z_R)
        K  = self._build_K(GM)
        GF = self._build_GF(simulation, u_y_R, u_z_R)

        self.GX, self.GX_dot, self.GX_ddot = self._newmark_step(
            simulation, M, self.C_sys, K, GF, self.GX, self.GX_dot)

        # Bending moments and deflections for each blade
        r0 = self.r[0]
        for b in range(self.n_blades):
            s = self._blade_mode_slice(b)

            u_ddot_y = self.GX_ddot[s] @ u_y_R
            u_ddot_z = self.GX_ddot[s] @ u_z_R

            p_eff_y = simulation.aero.rotor.blades[b].p[0] - self.m * u_ddot_y
            p_eff_z = simulation.aero.rotor.blades[b].p[1] - self.m * u_ddot_z

            self.M_bend_y[b] = np.trapezoid(p_eff_z * (self.r - r0), self.r)
            self.M_bend_z[b] = np.trapezoid(p_eff_y * (self.r - r0), self.r)

            self.deflection_y[b] = u_y_R.T @ self.GX[s]
            self.deflection_z[b] = u_z_R.T @ self.GX[s]

        # Update shaft azimuth and speed
        self.phi_shaft   = self.GX[1]
        self.omega_shaft = self.GX_dot[1]

