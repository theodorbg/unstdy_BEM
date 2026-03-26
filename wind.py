from abc import ABC, abstractmethod

import numpy as np
from scipy.interpolate import interp1d
import xarray as xr
import os
from hipersim import MannTurbulenceField
from scipy.interpolate import RegularGridInterpolator


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
        self.shear_exp = exponent
        self.hub_height = x_ref  # <-- required by v_hub_mean

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

        self.mann_dir = os.path.join(os.path.dirname(__file__), "sim_data", "mann_boxes")
        os.makedirs(self.mann_dir, exist_ok=True)

        # remove decimal point and trailing zeros from u_mean for filename
        u_s = f"{u_mean:.2f}".rstrip("0").rstrip(".")

        fname = f"mann_box_{TI}_{u_s}.nc"
        fpath = os.path.join(self.mann_dir, fname)
        
        if not os.path.exists(fpath):
            print(f"Generating Mann box with TI={TI} and u_mean={u_mean} m/s")
            mann_box = MannTurbulenceField.generate(
                Nxyz=(self.n1, self.n2, self.n3),
                dxyz=(self.dx, self.dy, self.dz),
                L=33.6, Gamma=3.9
            )
            mann_box.scale_TI(TI=self.TI, U=self.surrounding_wind.v_hub_mean)
            mann_box.to_netcdf(filename = fpath)

        mann_box = MannTurbulenceField.from_netcdf(fpath)  # this one takes the folder path directly
        print(f"Mann box loaded from file: {fpath}")

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
        dx = float(self.da_mann_box["x"].values[1] - self.da_mann_box["x"].values[0])  # spacing between x points
        dy = float(self.da_mann_box["y"].values[1] - self.da_mann_box["y"].values[0])  # spacing between y points (may be negative)
        dz = float(self.da_mann_box["z"].values[1] - self.da_mann_box["z"].values[0])  # spacing between z points

        nx = self.da_mann_box["x"].size
        ny = self.da_mann_box["y"].size
        nz = self.da_mann_box["z"].size
        

        self.x_turb = np.arange(nx) * dx + (simulation.structure.hub_height - (nx - 1) * dx / 2)
        self.y_turb = np.arange(ny) * abs(dy) - (ny - 1) * abs(dy) / 2
        self.z_turb  = np.arange(nz) * dz -self.Lx # position box initially upstream of rotor by shift of one box length (Lx) to allow it to advect through the rotor plane during the simulation

        self.da_mann_box = self.da_mann_box.assign_coords(x=self.x_turb, y=self.y_turb, z=self.z_turb)

        """ Make interpolator function for the Mann box"""

        # Extract coordinate arrays and velocity components arrays from the DataArray and make them numpy arrays for the interpolator
        self.x_grid = self.da_mann_box["x"].to_numpy()
        self.y_grid = self.da_mann_box["y"].to_numpy()
        self.z_grid = self.da_mann_box["z"].to_numpy()

        self.u_grid = self.da_mann_box.sel(uvw="x").transpose("x", "y", "z").to_numpy()  # shape (nx, ny, nz)
        self.v_grid = self.da_mann_box.sel(uvw="y").transpose("x", "y", "z").to_numpy()  # shape (nx, ny, nz)
        self.w_grid = self.da_mann_box.sel(uvw="z").transpose("x", "y", "z").to_numpy()  # shape (nx, ny, nz)

        uvw_grid = np.stack([self.u_grid, self.v_grid, self.w_grid], axis=-1)  # shape (nx, ny, nz, 3)

        # Create the interpolator
        self.uvw_interp = RegularGridInterpolator((self.x_grid, self.y_grid, self.z_grid), uvw_grid)

       
    def __call__(self, xyz):

        xyz = np.atleast_2d(xyz)

        # query points
        xq = xyz[:, 0]
        yq = xyz[:, 1]
        zq = xyz[:, 2]


        V_turb = self.uvw_interp(xyz)  # shape (n_points, 3)

        if np.isnan(V_turb).any():
            raise ValueError(f"NaN values found in interpolated turbulence at points {xyz}."
                             "This likely means that some of the query points are outside the bounds of the turbulence box."
                              " Check the coordinates of the query points and the bounds of the turbulence box.")
        
        
        # Add surrounding wind
        base = np.atleast_2d(self.surrounding_wind(xyz))

        return (V_turb + base).squeeze()

        # # Check if any query points are within the box bounds
        # z_min, z_max = self.z_turb[0], self.z_turb[-1]
        # x_min, x_max = self.x_turb[0], self.x_turb[-1]
        # y_min, y_max = self.y_turb[0], self.y_turb[-1]

        # in_bounds = (
        #     (xyz[:, 0] >= x_min) & (xyz[:, 0] <= x_max) &
        #     (xyz[:, 1] >= y_min) & (xyz[:, 1] <= y_max) &
        #     (xyz[:, 2] >= z_min) & (xyz[:, 2] <= z_max)
        # )

        # if not np.any(in_bounds):
        #     print(f"outside turb box bounds, returning {base}")
        #     return base.squeeze()
        
        # # Wrap coordinates in DataArrays with a shared dimension 'points'
        # # This forces xarray to interpolate rowwise (point-by-point) instead of a 3D mesh
        # points = np.arange(len(xyz))
        # x_da = xr.DataArray(xyz[:, 0], dims='points', coords={'points': points})
        # y_da = xr.DataArray(xyz[:, 1], dims='points', coords={'points': points})
        # z_da = xr.DataArray(xyz[:, 2], dims='points', coords={'points': points})

        # # Box coordinates
        # x_box = self.da_mann_box["x"]
        # y_box = self.da_mann_box["y"]
        # z_box = self.da_mann_box["z"]


        # # Check if rotor is outside box
        # if xyz[:,0].min() < float(x_box[0]):
        #     print("Rotor extends below box in x direction")
        # if xyz[:,0].max() > float(x_box[-1]):
        #     print("Rotor extends above box in x direction")
        # if xyz[:,1].min() < float(y_box[0]):
        #     print("Rotor extends below box in y direction")
        # if xyz[:,1].max() > float(y_box[-1]):
        #     print("Rotor extends above box in y direction")
        # if xyz[:,2].min() < float(z_box[0]):
        #     print("Rotor extends below box in z direction")
        # if xyz[:,2].max() > float(z_box[-1]):
        #     print("Rotor extends above box in z direction")

        # # Interpolate pointwise: result shape is (3, n_points) instead of (3, nx, ny, nz)
        # uvw_interp = self.da_mann_box.interp(x=x_da, y=y_da, z=z_da, method='linear')

        # # print(f"Interpolating turbulence {uvw_interp}")

        # # uvw_interp has dims (uvw, points) → transpose to (points, uvw)
        # turb_var = uvw_interp.values.T  # shape: (n_points, 3)

        # # Replace NaNs with 0 for out-of-bounds points (adds 0 turbulence = free wind only)
        # turb_var = np.nan_to_num(turb_var, nan=0.0)

        # # print(f"Interpolated turbulence at points {xyz} is {turb_var}")

        # result = (base + turb_var).squeeze()

        # # print(f"Wind at points {xyz} is {result}")

        # return result
        
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


class ConfiguredWind(Wind):
    """
    Builds a wind model from simple inputs:
    - shear exponent
    - hub height
    - hub wind speed
    - optional tower radius profile
    - turbulence intensity
    """
    def __init__(
        self,
        hub_height: float,
        v_hub: float,
        shear_exp: float = 0.0,
        tower_radius: np.ndarray | None = None,
        TI: float = 0.0,
        y_tower: float = 0.0,
        z_tower: float = 0.0,
    ) -> None:
        if shear_exp != 0:
            #    def __init__(self, x_ref: float, v_ref: float, exponent: float, hub_height: float) -> None:

            wind: Wind = ShearWind(hub_height, v_hub, shear_exp)
        else:
            wind = ConstantWind(v_hub)

        if tower_radius is not None:
            wind = WindWithTower(
                y_tower=y_tower,
                z_tower=z_tower,
                xa=tower_radius,
                surrounding_wind=wind,
            )

        if TI > 0:
            wind = TurbWind(wind, TI)

        self._wind = wind

    def simulation_init(self, simulation):
        if hasattr(self._wind, "simulation_init"):
            self._wind.simulation_init(simulation)

    def __call__(self, xyz):
        return self._wind(xyz)

    def step(self, simulation) -> None:
        self._wind.step(simulation)

    @property
    def v_hub_mean(self) -> float:
        return self._wind.v_hub_mean

