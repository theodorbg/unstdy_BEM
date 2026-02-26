import numpy as np
# import interp1d
from scipy.interpolate import interp1d


class Airfoil:
    """
    Brief description of the class purpose.
    
    Attributes:
        instance_attr (type): Description of instance attribute.
        CLASS_ATTR (type): Description of class attribute (shared across instances).
    
    Example:
        obj = ClassName(param1, param2)
        result = obj.method()
    """
    
    # Class attributes (shared by all instances)

    def __init__(self, file_path: str) -> None:
        """
        Initialize a new instance.
        
        Args:
            airfoil (csv file): Description of the airfoil data file.
            """
        data = np.loadtxt(file_path, delimiter=',', skiprows=1)  # Adjust as needed
        self.airfoil = data
        self.aoa = data[:, 0]
        self.cl_stdy = data[:, 1]
        self.cd_stdy = data[:, 2]
        self.cm_stdy = data[:, 3]
        self.cl_sep = data[:, 4]
        self.cl_lin = data[:, 5]
        self.cl_stall = data[:, 6]
        
    def cl_cd(self, alpha: float) -> tuple[float, float]:
        """Steady Cl/Cd at alpha (deg); nan/clip outside aoa range."""
        cl_interp = interp1d(self.aoa, self.cl_stdy, kind='linear', 
                             bounds_error=False, fill_value=np.nan)
        cd_interp = interp1d(self.aoa, self.cd_stdy, kind='linear', 
                             bounds_error=False, fill_value=np.nan)
        return float(cl_interp(alpha)), float(cd_interp(alpha))
    
    def cl_lin_cl_stall_fs(self, alpha: float) -> tuple[float, float, float]:
        """Cl_lin, Cl_stall and Cl_sep at alpha (deg); nan/clip outside aoa range."""
        cl_lin_interp = interp1d(self.aoa, self.cl_lin, kind='linear', 
                                 bounds_error=False, fill_value=np.nan)
        cl_stall_interp = interp1d(self.aoa, self.cl_stall, kind='linear', 
                                bounds_error=False, fill_value=np.nan)
        fs_interp = interp1d(self.aoa, self.cl_sep, kind='linear', 
                                bounds_error=False, fill_value=np.nan)
        
        return float(cl_lin_interp(alpha)), float(cl_stall_interp(alpha)), float(fs_interp(alpha))
        
class BladeAirfoils:
    " Manage all 7 airfoils; interpolate by thickness ratio. "

    THICKNESSES = np.array([24.1, 30.1, 36.0, 48.0, 60.0, 100.0])
    FILES = {
        24.1: 'FFA-W3-241_ds.csv',
        30.1: 'FFA-W3-301_ds.csv',
        36.0: 'FFA-W3-360_ds.csv',
        48.0: 'FFA-W3-480_ds.csv',
        60.0: 'FFA-W3-600_ds.csv',
        100.0: 'cylinder_ds.csv',      
    }

    
    def __init__(self, airfoil_dir: str = 'data/'):
        self.airfoils = {}
        for thick, filename in self.FILES.items():
            filepath = f"{airfoil_dir}{filename}"
            self.airfoils[thick] = Airfoil(filepath)


    def get_cl_cd(self, alpha: np.ndarray, rel_thick: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Interp Cl/Cd between nearest airfoils by rel_thick (arrays for blade sections)."""
        cl_out = np.zeros_like(alpha)
        cd_out = np.zeros_like(alpha)
        
        for i in range(len(rel_thick)):
            idx1, idx2 = self._find_nearest(rel_thick[i])  # Scalar thick_i
            cl1, cd1 = self.airfoils[self.THICKNESSES[idx1]].cl_cd(alpha[i])
            cl2, cd2 = self.airfoils[self.THICKNESSES[idx2]].cl_cd(alpha[i])
            
            denom = self.THICKNESSES[idx2] - self.THICKNESSES[idx1]
            if denom == 0:  # Same airfoil (exact match/clipped)
                cl_out[i], cd_out[i] = cl1, cd1
            else:
                frac = (rel_thick[i] - self.THICKNESSES[idx1]) / denom
                cl_out[i] = cl1 + frac * (cl2 - cl1)
                cd_out[i] = cd1 + frac * (cd2 - cd1)
        
        return cl_out, cd_out
    
    def get_cl_lin_cl_stall_fs(self, alpha: np.ndarray, rel_thick: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Interp Cl/Cd between nearest airfoils by rel_thick (arrays for blade sections)
        
        Parameters
        ----------
        alpha : np.ndarray
            Array of angle of attack values (in degrees) for each blade section.
        rel_thick : np.ndarray
            Array of relative thickness values for each blade section (e.g., 0.24, 0.30, etc.).

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray]
            A tuple containing three numpy arrays: (Cl_lin, Cl_stall, fs) for each blade section, interpolated based on the provided alpha and rel_thick values.


        """
        cl_lin_out = np.zeros_like(alpha)
        cl_stall_out = np.zeros_like(alpha)
        fs_out = np.zeros_like(alpha)

        for i in range(len(rel_thick)):
            idx1, idx2 = self._find_nearest(rel_thick[i])  # Scalar thick_i
            cl_lin1, cl_stall1, fs1 = self.airfoils[self.THICKNESSES[idx1]].cl_lin_cl_stall_fs(alpha[i])
            cl_lin2, cl_stall2, fs2 = self.airfoils[self.THICKNESSES[idx2]].cl_lin_cl_stall_fs(alpha[i])
            
            denom = self.THICKNESSES[idx2] - self.THICKNESSES[idx1]
            if denom == 0:  # Same airfoil (exact match/clipped)
                cl_lin_out[i], cl_stall_out[i], fs_out[i] = cl_lin1, cl_stall1, fs1
            else:
                frac = (rel_thick[i] - self.THICKNESSES[idx1]) / denom
                cl_lin_out[i] = cl_lin1 + frac * (cl_lin2 - cl_lin1)
                cl_stall_out[i] = cl_stall1 + frac * (cl_stall2 - cl_stall1)
                fs_out[i] = fs1 + frac * (fs2 - fs1)
        
        return cl_lin_out, cl_stall_out, fs_out
    

    def _find_nearest(self, thick: float) -> tuple[int, int]:
        """
        Find lower/upper indices for interpolation.
        E.g., thick=0.27 → (0, 1) for [24.1, 30.1].
        Exact match returns same index twice (e.g., 0.36 → (2, 2)).
        Clips: thick<0.241 → (0,0); thick>1.0 → (5,5).
        """
        # Convert decimal to percentage (e.g., 0.36 → 36.0)
        thick_percent = thick * 100.0
        thicknesses = self.THICKNESSES  # np.array([24.1, 30.1, 36.0, 48.0, 60.0, 100.0])
        
        # Check for exact match first
        exact_match = np.where(np.isclose(thicknesses, thick_percent, atol=0.01))[0]
        if len(exact_match) > 0:
            idx = exact_match[0]
            return idx, idx
        
        # Find bracket for interpolation
        idx = np.searchsorted(thicknesses, thick_percent, side='left')
        
        if idx == 0:
            return 0, 0  # Below minimum - clip to first
        elif idx >= len(thicknesses):
            return len(thicknesses) - 1, len(thicknesses) - 1  # Above maximum - clip to last
        else:
            return idx - 1, idx  # Bracket: lower, upper


airfoils = BladeAirfoils()
aoa = -70

cl_lin_out, cl_stall_out, fs_out = airfoils.get_cl_lin_cl_stall_fs(np.array([12]), np.array([24.1]))
print("cl_lin_out:", cl_lin_out)
print("cl_stall_out:", cl_stall_out)
print("fs_out:", fs_out)

#0.480: -70.000000,-0.642800,1.147900,0.234900,0.000000,-11.074992,-0.642800


#0.360 -70.000000,-0.643000,1.148000,0.235000,0.000000,-2.911204,-0.643000

# cl_expected = -0.6429
# cd_expected = 1.14795
# cl, cd = airfoils.get_cl_cd(aoa, 0.54)
# print(f"Expected vs interpolated Cl: {cl_expected} = {cl}")
# print(f"Expected vs interpolated Cd: {cd_expected} = {cd}")
