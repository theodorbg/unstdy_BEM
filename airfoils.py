import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator


class Airfoils:
    """
    Airfoil data management using RegularGridInterpolator for efficient 2D interpolation.
    
    Interpolates aerodynamic coefficients based on angle of attack (alpha) and 
    relative thickness (tc).
    
    Attributes:
        tc_grid (np.ndarray): Array of relative thickness values in percent [24.1, 30.1, ...].
        alpha_grid (np.ndarray): Array of angle of attack values in degrees.
        cl_stat_interp (RegularGridInterpolator): Interpolator for steady Cl.
        cd_stat_interp (RegularGridInterpolator): Interpolator for steady Cd.
        f_stat_interp (RegularGridInterpolator): Interpolator for steady separation point.
        cl_inv_interp (RegularGridInterpolator): Interpolator for inviscid Cl.
        cl_fs_interp (RegularGridInterpolator): Interpolator for fully separated Cl.
    
    Example:
        airfoils = Airfoils(airfoil_dir='data/')
        alpha = np.array([5.0, 10.0])
        tc = np.array([30.0, 36.0])
        cl, cd = airfoils.get_cl_cd(alpha, tc)
    """
    
    TC_GRID = np.array([24.1, 30.1, 36.0, 48.0, 60.0, 100.0])
    FILES = [
        'FFA-W3-241_ds.csv',
        'FFA-W3-301_ds.csv',
        'FFA-W3-360_ds.csv',
        'FFA-W3-480_ds.csv',
        'FFA-W3-600_ds.csv',
        'cylinder_ds.csv'
    ]
    
    def __init__(self, airfoil_dir: str = 'data/') -> None:
        """
        Initialize airfoil interpolators from CSV files.
        
        Parameters
        ----------
        airfoil_dir : str, optional
            Directory containing airfoil CSV files, by default 'data/'
        """
        # Load all dataframes
        dfs = [pd.read_csv(f"{airfoil_dir}{file}") for file in self.FILES]
        
        # All AoA are the same, extract from the first file
        self.alpha_grid = dfs[0]["alpha"].values.astype(float)
        self.tc_grid = self.TC_GRID
        
        # Build tables: shape (n_alpha, n_tc)
        cl_stat_table = np.column_stack([df["cl_stdy"].values.astype(float) for df in dfs])
        cd_stat_table = np.column_stack([df["cd_stdy"].values.astype(float) for df in dfs])
        cm_stdy_table = np.column_stack([df["cm_stdy"].values.astype(float) for df in dfs])
        f_stat_table  = np.column_stack([df["cl_sep"].values.astype(float) for df in dfs])
        cl_inv_table  = np.column_stack([df["cl_lin"].values.astype(float) for df in dfs])
        cl_fs_table   = np.column_stack([df["cl_stall"].values.astype(float) for df in dfs])
        
        # Create interpolators
        self.cl_stat_interp = RegularGridInterpolator(
            (self.alpha_grid, self.tc_grid), cl_stat_table,
            bounds_error=False, fill_value=np.nan
        )
        self.cd_stat_interp = RegularGridInterpolator(
            (self.alpha_grid, self.tc_grid), cd_stat_table,
            bounds_error=False, fill_value=np.nan
        )
        self.f_stat_interp = RegularGridInterpolator(
            (self.alpha_grid, self.tc_grid), f_stat_table,
            bounds_error=False, fill_value=np.nan
        )
        self.cl_inv_interp = RegularGridInterpolator(
            (self.alpha_grid, self.tc_grid), cl_inv_table,
            bounds_error=False, fill_value=np.nan
        )
        self.cl_fs_interp = RegularGridInterpolator(
            (self.alpha_grid, self.tc_grid), cl_fs_table,
            bounds_error=False, fill_value=np.nan
        )

airfoils = Airfoils()
    
    