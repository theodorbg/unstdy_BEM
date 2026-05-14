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
        self.inertia_rotor = 1.6e8
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

class FlexibleStructure_5dof(Structure):
    
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
            pitch_init=pitch_init)
        # Initialize additional attributes for flexible structure here
        # only blade 1/0 is flexible so:
        self.FLEX_BLADE_IDX = 0
        self. tower_stiffness = 1.7e6 # N/m
        (self.u1_flap, self.u1_edge, self.u2_flap,
         self.m,
         self.omega1f, self.omega1e, self.omega2f) = self.read_modeshapes_file(file_modes)
        
        self.DOF = 5
        self.STATES = 3
        # initialize solution variables for the 5 DOF system
        # self.z = np.array([0, 0, 0]) # tower deflection in wind direction (position, velocity, acceleration)
        # self.theta = np.array([0, self.omega_init, 0]) # rotor azimuthal position (position, velocity, acceleration)
        # self.q1 = np.array([0, 0, 0]) # flapwise 1: q, qdot, qddot (position, velocity, acceleration)
        # self.q2 = np.array([0, 0, 0]) # edge-wise 1: q, qdot, qddot (position, velocity, acceleration)
        # self.q3 = np.array([0, 0, 0]) # flapwise 2: q, qdot, qddot (position, velocity, acceleration)
        # define x as vector to store the 5 DOF solution variables for position, velocity, and acceleration
        self.x = np.zeros(self.DOF) # [z, theta, q1, q2, q3]
        self.x_dot = np.zeros(self.DOF) # [z_dot, theta_dot, q1_dot, q2_dot, q3_dot]
        self.x_dot[1] = self.omega_shaft # set initial condition for theta_dot
        self.x_ddot = np.zeros(self.DOF) # [z_ddot, theta_ddot, q1_ddot, q2_ddot, q3_ddot]
        
        self.z =np.zeros(self.STATES) # tower deflection in wind direction (position, velocity, acceleration)
        self.theta = np.zeros(self.STATES) 
        self.q1 = np.zeros(self.STATES) 
        self.q2 = np.zeros(self.STATES) 
        self.q3 = np.zeros(self.STATES) 

        self.GF = np.zeros(self.DOF)


        # initialize constants from avg. acceleration method (Newmark-beta) for time integration
        self.beta = 0.25
        self.gamma = 0.5
        self.tolerance_r = 1e-7
        self.tolerance_u = 1e-7
        self.delta_u = np.ones_like(self.x) # initialize delta_u to enter the while loop
        self.max_iter = 1000



    def step(self, simulation):
        self.z, self.theta, self.q1, self.q2, self.q3 = self.time_integration(simulation, solver="newmark")

    def simulation_init(self, simulation):
        
        # initialize solutions to 0 so the recorder doesn't break, but we will overwrite them in the first time step of the simulation
        
        # compute the matrices at t=0
        self.gm1, self.gm2, self.gm3 = self.GM()
        self.K = self.K_matrix()
        self.M = self.M_matrix()
        # we pretend that the forces:GF at t=0 is 0
        # self.GF = self.GF_vector(simulation, T=0, M_G=0, M_R=0))
        
        # compute initial acceleration
        self.x_ddot = np.linalg.solve(self.M, self.GF - self.K @ self.x)

    
    def read_modeshapes_file(self, file_modes: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float, float]:
        """Read the modeshapes text file into a DataFrame."""
        cols = ["r", "u1fy", "u1fz", "u1ey", "u1ez", "u2fy", "u2fz", "m"]
        # create standard modeshapes dataframe (only 18 radial positions)
        df_modeshapes_std = pd.read_csv(
            file_modes,
            sep=r"\s+",
            comment="#",
            header=None,
            names=cols,
            engine="python",
        )

        df_modeshapes = pd.DataFrame({"r": self.r})

        for col in cols[1:]:  # interpolate all columns except r
            df_modeshapes[col] = np.interp(
                self.r,
                df_modeshapes_std["r"].to_numpy(),
                df_modeshapes_std[col].to_numpy(),
                left=df_modeshapes_std[col].iloc[0],
                right=df_modeshapes_std[col].iloc[-1],
            )
            
        u1fy = df_modeshapes["u1fy"].to_numpy()
        u1fz = df_modeshapes["u1fz"].to_numpy()
        u1_flap = np.array([u1fy, u1fz])
        
        u1ey = df_modeshapes["u1ey"].to_numpy()
        u1ez = df_modeshapes["u1ez"].to_numpy()
        u1_edge = np.array([u1ey, u1ez])
        
        u2fy = df_modeshapes["u2fy"].to_numpy()
        u2fz = df_modeshapes["u2fz"].to_numpy()
        u2_flap = np.array([u2fy, u2fz])
        
        m = df_modeshapes["m"].to_numpy()
        
        # Extract frequencies from comment lines
        with open(file_modes, "r", encoding="utf-8") as f:
            for line in f:
                if "omega1f" in line and "omega1e" in line and "omega2f" in line:
                    vals = re.findall(r"omega1f=([\d.]+)|omega1e=([\d.]+)|omega2f=([\d.]+)", line)
                    flat = [x for group in vals for x in group if x]
                    omega1f, omega1e, omega2f = map(float, flat)
                    break

        
        return u1_flap, u1_edge, u2_flap, m, omega1f, omega1e, omega2f

    def time_integration(self, simulation, solver="newmark"):
        if solver == "newmark":
            h = simulation.dt
            
            # at each time step, we need to update the system matrices
            self.gm1, self.gm2, self.gm3 = self.GM()
            self.K = self.K_matrix()
            self.M = self.M_matrix()
            self.GF = self.GF_vector(simulation)
                        
            # (2) predict x and x_dot at next time step
            
            self.x_dot = self.x_dot + h * self.x_ddot
            self.x = self.x + h * self.x_dot + 0.5 * h**2 * self.x_ddot
            
            # compute the residual before we enter the whiel loop
            self.residual = self.GF - self.M @ self.x_ddot -self.K @ self.x
            
            it = 0
            while (np.linalg.norm(self.residual) > self.tolerance_r or
                   np.linalg.norm(self.delta_u) > self.tolerance_u
                   and it<self.max_iter):
                
                it += 1

                # (4) system matrices and increment correction
                K_star = self.K + 1/(self.beta * h) * self.M
                self.delta_u = np.linalg.inv(K_star) @ self.residual
                
                self.x += self.delta_u
                self.x_dot += self.gamma/(self.beta*h) * self.delta_u
                self.x_ddot += 1/(self.beta*h**2) * self.delta_u
                
                # move the residual computation to the bottom to avoid doing it twice in the first iteration
                # (3) compute residual: r = f-Mx_ddot-Kx - Cx_dot, but we don't have damping yet, so C=0
                self.residual = self.GF - self.M @ self.x_ddot -self.K @ self.x
            
            
            z = np.array([self.x[0], self.x_dot[0], self.x_ddot[0]])
            theta = np.array([self.x[1], self.x_dot[1], self.x_ddot[1]])
            q1 = np.array([self.x[2], self.x_dot[2], self.x_ddot[2]])
            q2 = np.array([self.x[3], self.x_dot[3], self.x_ddot[3]])
            q3 = np.array([self.x[4], self.x_dot[4], self.x_ddot[4]])
            
            return z, theta, q1, q2, q3
                
        
                
    
    def GM(self):
        # combine y,z components -> scalar generalized masses
        y1 = np.sum(self.u1_flap**2 * self.m, axis=0)
        y2 = np.sum(self.u1_edge**2 * self.m, axis=0)
        y3 = np.sum(self.u2_flap**2 * self.m, axis=0)

        # integrate over radius (use x=self.r)
        gm1 = np.trapz(y1, x=self.r)
        gm2 = np.trapz(y2, x=self.r)
        gm3 = np.trapz(y3, x=self.r)
        
        return gm1, gm2, gm3

    def K_matrix(self):
        # omega = natural frequencies

        K = np.diag([self.tower_stiffness, 0, self.omega1f**2 * self.gm1, self.omega1e**2 * self.gm2, self.omega2f**2 * self.gm3])
        return K    
    
    def M_matrix(self):
        
        # create 5x5 matrix
        M = np.zeros((5, 5))
        M[0, 0] = self.nacelle_mass + 3 * np.trapezoid(self.m, self.r)
        # fill out row by row
        # row 1
        M[0, 1] = 0
        M[0, 2] = np.trapezoid(self.m * self.u1_flap[1], self.r)
        M[0, 3] = np.trapezoid(self.m * self.u1_edge[1], self.r)
        M[0, 4] = np.trapezoid(self.m * self.u2_flap[1], x=self.r)
        # row 2
        M[1, 0] = 0
        M[1, 1] = self.inertia_rotor 
        M[1, 2] = np.trapezoid(self.m * self.r * self.u1_flap[0], self.r)
        M[1, 3] = np.trapezoid(self.m * self.r * self.u1_edge[0], self.r)
        M[1, 4] = np.trapezoid(self.m * self.r * self.u2_flap[0], self.r)
        # row 3
        M[2, 0] = np.trapezoid(self.m * self.u1_flap[1], self.r)
        M[2, 1] = np.trapezoid(self.m * self.r * self.u1_flap[0], self.r)
        M[2, 2] = self.gm1
        M[2, 3] = 0
        M[2, 4] = 0
        # row 4
        M[3, 0] = np.trapezoid(self.m * self.u1_edge[1], self.r)
        M[3, 1] = np.trapezoid(self.m * self.r * self.u1_edge[0], self.r)
        M[3, 2] = 0
        M[3, 3] = self.gm2
        M[3, 4] = 0
        # row 5
        M[4, 0] = np.trapezoid(self.m * self.u2_flap[1], self.r)
        M[4, 1] = np.trapezoid(self.m * self.r * self.u2_flap[0], self.r)
        M[4, 2] = 0
        M[4, 3] = 0
        M[4, 4] = self.gm3
        
        return M
        
    def GF_vector(self, simulation):
        T = simulation.aero.rotor._thrust
        M_R = simulation.aero.rotor._torque
        M_G = simulation.controller.torque_gen_func(simulation)

        p = simulation.aero.rotor.blades[self.FLEX_BLADE_IDX].p  # shape (2, N)

        gf3 = np.trapezoid(np.sum(p * self.u1_flap, axis=0), x=self.r)  # scalar
        gf4 = np.trapezoid(np.sum(p * self.u1_edge, axis=0), x=self.r)  # scalar
        gf5 = np.trapezoid(np.sum(p * self.u2_flap, axis=0), x=self.r)  # scalar

        GF = np.array([T, M_R - M_G, gf3, gf4, gf5], dtype=float)
        
        return GF
    
            
    def blade_vibration(self):
        u_blade = self.q1[1] * self.u1_flap + self.q2[1] * self.u1_edge + self.q3[1] * self.u2_flap
        tower = np.array([0, self.z[1]])
        return u_blade, tower            
    
    def blade_x1(self, blade_idx: int) -> np.ndarray:
        # Implement the logic to return the coordinates of blade number `blade_idx` in coordinate system 1
        pass

    def blade_u5(self, blade_idx: int) -> np.ndarray:
        # Implement the logic to return the velocities due to the motion of the blade in coordinate system 5
        pass

    def x15(self, array: np.ndarray, blade_idx: int) -> np.ndarray:
        # Implement the logic to transform an array from coordinate system 1 into the blade coordinate system 5
        pass

