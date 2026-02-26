from abc import ABC, abstractmethod

import numpy as np
from numpy import cos, sin, sqrt, arctan, pi, arccos, arcsin
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
        vrel_y (type): Y component of relative velocity.
        vrel_z (type): Z component of relative velocity.
        v0_y (type): Y component of free stream velocity.
        v0_z (type): Z component of free stream velocity.
        w_y (type): Y component of induced velocity.
        w_z (type): Z component of induced velocity.
        flow_angle (type): Flow angle in radians.
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
        f_g (type): glauert correciton
             
        

        RHO (type): Air density in kg/m^3
    
    """
    
    # Class attributes (shared by all instances)
    RHO = 1.225
    
    def __init__(self) -> None:
        """
        Initialize a new instance.
        
        Args:
            param1 (type1): Description.
            param2 (type2, optional): Description. Defaults to default2.
        """
        self.w_y=0
        self.w_z=0
        self.vrel_y = 0
        self.vrel_z = 0
        self.v0_y = 0
        self.v0_z = 0
        self.w_y = 0
        self.w_z = 0
        self.flow_angle = 0
        self.aoa = 0
        self.twist = 0
        self.pitch = 0
        self.cl = 0
        self.cd = 0
        self.lift = 0
        self.drag = 0
        self.chord = 0
        self.p_z = 0
        self.p_y = 0
        self.a = 0
        self.f_g = 0
        self.drag = 0
        self.drag = 0

        # self.blade_data = read_blade_data() # function to read blade data from file or other source
        # Additional initialization, e.g., validation or computed attributes
    
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

        B = simulation.structure.n_blades
        
        for blade_no in range(B):
            xyz = simulation.structure.blade_x1(blade_no)
            
            self.v0_y = simulation.wind(xyz)[:,1]
            self.v0_z = simulation.wind(xyz)[:,2]

            omega = simulation.structure.omega_shaft
            cone = simulation.structure.cone
            x = simulation.structure.r

            # calculate relative velocity components
            self.vrel_y = self.v0_y+ self.w_y - omega*x*cos(cone)
            self.vrel_z = self.v0_z + self.w_z

            # calculate norm of relative velocity
            norm_vrel = sqrt(self.vrel_y**2+self.vrel_z**2)

            # calculate flow angle
            self.phi = arctan(self.vrel_z, -self.vrel_y) # in radians

            # calculate angle of attack
            self.aoa = self.phi-self.twist+self.pitch

            # interpolate cl and cd from airfoil data
            self.cl, self.cd = airfoils.get_cl_cd(self.aoa, simulation.structure.tc)
                        
            # calculate lift and drag per unit length
            self.lift = 0.5*self.RHO*norm_vrel**2*self.chord*self.cl
            self.drag = 0.5*self.RHO*norm_vrel**2*self.chord*self.cd

            # calculate spanwise loads
            self.p_z = self.lift*cos(self.phi)+self.drag*sin(self.phi)
            self.p_y = self.lift*sin(self.phi)-self.drag*cos(self.phi)

            # estimate local induction factor
            self.a = -self.w_z / self.v0_y #ask TA

            # calculate glauert correction factor 
            if self.a<=1/3:
                self.f_g = 1
            else: self.f_g = 1/4*(5-3*self.a)
            
            # calculate Prandtl tip loss F
            R = simulation.structure.R
            r = simulation.structure.r
            self.F = 2/pi * arccos(np.exp(-B/2*(R-r)/(r*sin(np.abs(self.phi)))))

            # calculate v0+fg*Wn to insert easily into formula for Wz_qs
            mag_v0_fW = sqrt(self.v0_y**2+(self.v0_z+self.f_g*self.w_z)**2)

            # calculate quasi steady induction wind z component
            self.w_z = (-B*self.lift*cos(self.phi))/(4*pi*self.RHO*r*self.F*mag_v0_fW)

            # calculate quasi steady induction wind y component
            self.w_y = (-B*self.lift*sin(self.phi))/(4*pi*self.RHO*r*self.F*mag_v0_fW)



                                                             






        

        return result
    
    @classmethod
    def class_method(cls) -> "ClassName":
        """
        Alternative constructor or class-level operation.
        """
        # Class method logic
        return cls(...)
    
    @staticmethod
    def static_method(arg: type) -> type:
        """
        Utility function not requiring instance or class access.
        """
        # Static method logic
        return result
    
    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return f"ClassName(instance_attr1={self.instance_attr1!r})"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"ClassName with attr1={self.instance_attr1}"
