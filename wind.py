from abc import ABC, abstractmethod

import numpy as np
from scipy.interpolate import interp1d
import xarray as xr
import os
from hipersim import MannTurbulenceField


class Wind(ABC):
    """
    Base (parent) class for the wind. This is not supposed to be used during the simulations (and also doesn't do
    anything). Using the @abstractmethod line defines which methods the children classes need to implement.
    """

    @abstractmethod
    def __call__(self, xyz) -> np.ndarray:
        pass

    @abstractmethod
    def step(self, simulation) -> None:
        pass

    @property
    @abstractmethod
    def v_hub_mean(self) -> float:
        pass

class ConstantWind(Wind):
    def __init__(self, ws: float) -> None:
        """
        Initialises a wind instance that returns a constant wind speed everywhere.

        Parameters
        ----------
        ws : float
            The wind speed.
        """
        self.ws = ws

    def __call__(self, xyz):
        xyz = np.atleast_2d(xyz)
        return (np.c_[np.zeros_like(xyz[:, 0]), np.zeros_like(xyz[:, 0]), np.full_like(xyz[:, 0], self.ws)]).squeeze()

    def step(self, simulation):
        # Nothing needs to happen here; the wind speed simply stays constant everywhere.
        pass

    @property
    def v_hub_mean(self) -> float:
        return self.ws


class NoWind(ConstantWind):
    def __init__(self) -> None:
        """
        Initialises an instance that returns a wind speed of zero everywhere.
        """
        super().__init__(0)


class ShearWind(Wind):
    def __init__(self, x_ref: float, v_ref: float, exponent: float) -> None:
        """
        Initialises an instance that returns wind speeds based on the defined shear.

        Parameters
        ----------
        x_ref : float
            The x coordinate at which the reference wind speed `v_ref` is defined.
        v_ref : float
            The reference wind speed at height `x_ref`
        exponent : float
            The exponent of for the shear.
        """
        self.shear = lambda x: v_ref * (x / x_ref) ** exponent

    def __call__(self, xyz):
        xyz = np.atleast_2d(xyz)
        return np.c_[np.zeros_like(xyz[:, 0]), np.zeros_like(xyz[:, 0]), self.shear(xyz[:, 0])]
    
    def simulation_init(self, simulation):
        self.hub_height = simulation.structure.hub_height


    def step(self, simulation):
        # Nothing needs to happen here either.
        pass

    @property
    def v_hub_mean(self) -> float:
        return self.shear(self.hub_height)


class WindWithTower(Wind):

    def __init__(self, y_tower: float, z_tower: float, xa: np.ndarray, surrounding_wind: Wind) -> None:
        """
        Initialises and instance that returns wind speeds based on `surrounding_wind` including the
        tower effect.

        Example
        ----------
        To use a shear with `x_ref=119`, `u_ref=10`, `exponent=0.2` that includes the tower effect (tower at
        `y_tower=0`, `z_tower=0`, with a constant radius of 3.32m from the bottom to the top), do this:

        >>> shear_wind = ShearWind(119, 10, 0.2)
        >>> xa = np.asarray([[0, 3.32], [119, 3.32]])
        >>> shear_with_tower = WindWithTower(0, 0, xa, shear_wind)

        Parameters
        ----------
        y_tower : float
            The y coordinate of the tower base.
        z_tower : float
            The z coordiante of the tower base.
        xa : np.ndarray
            A 2D array of shape (n, 2) defining the radius of the tower over height x. Each row defines
            [x coordinate, radius at this x coordinate].
        surrounding_wind : Wind
            An instance of a wind class that has the `Wind` class as parent class.
        """
        self.centre = np.asarray([y_tower, z_tower])
        self.a = interp1d(xa[:, 0], xa[:, 1], fill_value=(0, 0), bounds_error=False)
        self.surrounding_wind = surrounding_wind

    def __call__(self, xyz):
        xyz = np.atleast_2d(xyz)

        x, y, z = xyz.T
        r = np.linalg.norm(xyz[:, 1:3] - self.centre, axis=1)
        V_0 = np.atleast_2d(self.surrounding_wind(xyz))[:, 2]
        v_r = z / r * V_0 * (1 - (self.a(x) / r) ** 2)
        v_theta = y / r * V_0 * (1 + (self.a(x) / r) ** 2)

        v_y = y / r * v_r - z / r * v_theta
        v_z = z / r * v_r + y / r * v_theta
        return (np.c_[np.zeros_like(v_y), v_y, v_z]).squeeze()

    def step(self, simulation):
        # Nothing needs to change here :)
        pass

    @property
    def v_hub_mean(self) -> float:
        return self.surrounding_wind.v_hub_mean


class TurbWind(Wind):

    def __init__(self, surrounding_wind: Wind, TI = 0.1) -> None:
        
        self.surrounding_wind = surrounding_wind
        self.TI = TI
        u_mean = self.surrounding_wind.v_hub_mean

        # Define discretization of the Mann box
        self.n1=4096
        self.n2=32
        self.n3=32

        # Define the size of the box
        self.Lx = 6142.5
        Ly = 180
        Lz = 180

        # Calculate grid spacing
        self.dy=Ly/(self.n2-1)
        self.dx=self.Lx/(self.n1-1)
        self.dz=Lz/(self.n3-1)

        fname = f"mann_box_{TI}_{u_mean}.nc"   # this is the FOLDER name

        if not os.path.exists(fname):
            print(f"Generating Mann box with TI={TI} and u_mean={u_mean} m/s")
            mann_box = MannTurbulenceField.generate(
                Nxyz=(self.n1, self.n2, self.n3),
                dxyz=(self.dx, self.dy, self.dz),
                L=33.6, Gamma=3.9
            )
            mann_box.scale_TI(TI=self.TI, U=self.surrounding_wind.v_hub_mean)
            mann_box.to_netcdf(filename = fname)

        mann_box = MannTurbulenceField.from_netcdf(fname)  # this one takes the folder path directly
        print("Mann box loaded from file")

        # Transform the Mann box to a `DataArray` (from the package `xarray`)
        self.da_mann_box = mann_box.to_xarray()

        # u=>z, v=>-y, w=>x in rotor coordinates
        # switch x and z
        self.da_mann_box = self.da_mann_box.rename({"x": "z", "z": "x"})
        # switch u and w
        # self.da_mann_box = self.da_mann_box.rename({"u": "w", "w": "u"})
        # flip v coordinates
        self.da_mann_box = self.da_mann_box.assign_coords(y=-self.da_mann_box["y"])  # flip y to match rotor coordinates
        # print(self.da_mann_box)
        self.da_mann_box = xr.concat(
                                    [self.da_mann_box.sel(uvw="w"),
                                    -self.da_mann_box.sel(uvw="v"),
                                    self.da_mann_box.sel(uvw="u")],
                                    dim=xr.DataArray(["x", "y", "z"], dims="uvw")) 


    def simulation_init(self, simulation):
        # Here you can load your turbulence box and set up any necessary variables for the turbulence.
        # NOTE: ["x"][1] gives the grid spacing in the x direction (dx). Same for y and z. 
        dx = float(self.da_mann_box["x"].values[1])  # spacing between x points
        dy = float(self.da_mann_box["y"].values[1] - self.da_mann_box["y"].values[0])  # spacing between y points (may be negative)
        dz = float(self.da_mann_box["z"].values[1])  # spacing between z points

        nx = self.da_mann_box["x"].size
        ny = self.da_mann_box["y"].size
        nz = self.da_mann_box["z"].size
        

        self.x_turb = np.arange(nx) * dx + (simulation.structure.hub_height - (nx - 1) * dx / 2)
        self.y_turb = np.arange(ny) * abs(dy) - (ny - 1) * abs(dy) / 2
        self.z_turb  = np.arange(nz) * dz -self.Lx #position box initially upstream of rotor by shift of one box length (Lx) to allow it to advect through the rotor plane during the simulation

        self.da_mann_box = self.da_mann_box.assign_coords(x=self.x_turb, y=self.y_turb, z=self.z_turb)

        
    def __call__(self, xyz):

        xyz = np.atleast_2d(xyz)
        
        # Wrap coordinates in DataArrays with a shared dimension 'points'
        # This forces xarray to interpolate rowwise (point-by-point) instead of a 3D mesh
        points = np.arange(len(xyz))
        x_da = xr.DataArray(xyz[:, 0], dims='points', coords={'points': points})
        y_da = xr.DataArray(xyz[:, 1], dims='points', coords={'points': points})
        z_da = xr.DataArray(xyz[:, 2], dims='points', coords={'points': points})

        # Interpolate pointwise: result shape is (3, n_points) instead of (3, nx, ny, nz)
        uvw_interp = self.da_mann_box.interp(x=x_da, y=y_da, z=z_da, method='linear')

        # print(f"Interpolating turbulence {uvw_interp}")

        # uvw_interp has dims (uvw, points) → transpose to (points, uvw)
        turb_var = uvw_interp.values.T  # shape: (n_points, 3)

        # print(f"Interpolated turbulence at points {xyz} is {turb_var}")

        # Add surrounding wind
        base = np.atleast_2d(self.surrounding_wind(xyz))
        # print(f"Surrounding wind at points {xyz} is {base}")

        result = (base + turb_var).squeeze()

        # print(f"Wind at points {xyz} is {result}")

        return result
        
    def step(self, simulation) -> None:

        # advect the box at the mean wind speed and update the z coordinates of the box
        # Pseudocode: box_z_pos += self.surrounding_wind.v_hub_mean * simulation.dt
        # Shift all z coordinates forward by umean * dt
        self.z_turb += self.surrounding_wind.v_hub_mean * simulation.dt

        # Update the z coordinates of the box
        self.da_mann_box = self.da_mann_box.assign_coords(z=self.z_turb)


    @property
    def v_hub_mean(self) -> float:
        return self.surrounding_wind.v_hub_mean

# class MannTurbulenceBox:
#     def __init__(self, umean, hub_height) -> None:
#         from scipy.interpolate import RegularGridInterpolator

#         FILENAME_U = "Turbulence_generator/sim1.bin"  # z1
#         FILENAME_V = "Turbulence_generator/sim2.bin"  # -y1
#         FILENAME_W = "Turbulence_generator/sim3.bin"  # x1

#         n1, n2, n3 = [4096, 32, 32]
#         Ly, Lz = [180, 180]

#         self.umean = umean

#         # Grid spacing (isotropic)
#         deltay = Ly / (n2 - 1)
#         deltax = deltay
#         deltaz = Lz / (n3 - 1)

#         # Spatial grids matching MATLAB: interp2(y_turb, x_turb, u_plane, pos_y, pos_x)
#         # x_turb: height axis centered around tower_height (rotor x-coord)
#         # y_turb: lateral axis centered around 0
#         x_turb = np.arange(n3) * deltax + (hub_height - (n3 - 1) * deltax / 2)
#         y_turb = np.arange(n2) * deltay - ((n2 - 1) * deltay) / 2

#         # Time axis (Taylor's frozen turbulence)
#         self.Lx = n1 * deltax
#         t_grid = np.arange(n1) * deltax  # x = umean * t → grid in advection distance

#         self.interpolators = []
#         for filename in [FILENAME_U, FILENAME_V, FILENAME_W]:
#             data = np.fromfile(filename, np.dtype('<f'), -1)
#             assert len(data) == n1 * n2 * n3, f"File {filename} has wrong size"
#             # Reshape: (n1=time, n2=lateral y, n3=height x)
#             box = data.reshape(n1, n2, n3)
#             # Grid: (t_grid, y_turb, x_turb) → query with (t, pos_y, pos_x)
#             self.interpolators.append(RegularGridInterpolator(
#                 (t_grid, y_turb, x_turb),
#                 box,
#                 method='linear',
#                 bounds_error=False,
#                 fill_value=0.0
#             ))

#         self.current_time = 0.0

#     def step(self, dt):
#         self.current_time += dt

#     def __call__(self, xyz):
#         xyz = np.atleast_2d(xyz)
#         # Taylor's frozen turbulence: advect box past rotor
#         # Equivalent to MATLAB: interp2(y_turb, x_turb, u_plane, pos_y(i), pos_x(i))
#         t_coord = (self.umean * self.current_time) % self.Lx  # periodic in time
#         t_query = np.full(len(xyz), t_coord)

#         pos_x = xyz[:, 0]  # height (x in rotor coords)
#         pos_y = xyz[:, 1]  # lateral (y in rotor coords)

#         query = np.c_[t_query, pos_y, pos_x]  # (t, pos_y, pos_x) matches interp2(y_turb, x_turb, ...)

#         u_turb = self.interpolators[0](query)  # streamwise (z in rotor)
#         v_turb = self.interpolators[1](query)  # lateral    (y in rotor)
#         w_turb = self.interpolators[2](query)  # vertical   (x in rotor)

#         return np.c_[w_turb, v_turb, u_turb]



# class TurbWind(Wind):
#     def __init__(self, turbulence_box: MannTurbulenceBox, surrounding_wind: Wind) -> None:
#         self.turbulence_box = turbulence_box
#         self.surrounding_wind = surrounding_wind

#     def __call__(self, xyz):
#         base = np.atleast_2d(self.surrounding_wind(xyz))
#         turb = np.atleast_2d(self.turbulence_box(xyz))
#         return (base + turb).squeeze()
    
#     def step(self, simulation):
#         self.turbulence_box.step(simulation.dt)