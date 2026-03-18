"""
Recorder class for storing time-series data during simulation.
"""

from collections.abc import Callable

import numpy as np


class Recorder:
    """
    Records simulation data in a pre-allocated numpy array.

    The recorder allocates memory based on dt and T.
    """

    def __init__(self, func: Callable, name: str, func_returns: tuple[str, ...] | str):
        """
        Create a recorder instance.

        Example
        ----------
        Wanted: Position of blade element at index 10 in coordinate system 1.
        First: Write a function that receives `simulation` and returns the position:
        >>> def get_blade_pos_in_1(simulation):
        >>>     return simulation.structure.blade_x1(blade_idx=0)[10]

        Then: Create the recorder
        >>> pos_recorder = Recorder(get_blade_pos_in_1, "position_recorder", ("x", "y", "z"))

        Where "position_recorder" becomes the name of the recorder (when you use `simulation.get_recorders()`) and
        `("x", "y", "z")` are the coordinates that the `get_blade_pos_in_1()` returns.

        This example is already implemented as the `BladePosition1Recorder`.

        Parameters
        ----------
        func : Callable
            A function that receives only `simulation` as input and returns a 1D list or 1D numpy array of values.
        name : str
            The name for the recorded data. Important when using `simulation.get_recorders()`.
        func_returns : tuple[str, ...] | str
            Specify what the `func` returns, i.e., if it returns a xyz position, `func_returns = ("x", "y", "z")`.
        """
        self.func = func
        self.name = name
        self.func_returns = func_returns if isinstance(func_returns, tuple) else (func_returns,)
        self._data = np.empty(0)
        self._steps_udpated = False

    def update_n_steps(self, n_steps: int):
        self._data = np.zeros((n_steps, len(self.func_returns)))
        self._steps_udpated = True

    def __call__(self, simulation):
        if not self._steps_udpated:
            raise RuntimeError(f"Need to use `update_n_steps` before using the recorder '{self.name}'.")
        self._data[simulation.step_idx] = self.func(simulation)

    @property
    def data(self) -> np.ndarray:
        return self._data


def time_recorder():
    def time(simulation):
        return round(simulation.time, 5)

    return Recorder(time, "time", ("time",))


def pitch_recorder(name: str, blade_idx: int):
    """Recorder for the pitch angle, which is the same for all blades."""
    def rec(simulation):
        return simulation.structure.pitch[blade_idx] # Assuming all blades have the same pitch angle, we can just return the pitch of the first blade.
    return Recorder(rec, name, "pitch")

def omega_recorder(name: str):
    """Recorder for the rotational speed of the rotor."""
    def rec(simulation):
        return simulation.structure.omega_shaft
    return Recorder(rec, name, "omega")


def blade_position_1_recorder(name: str, blade_idx: int, element_idx: int):
    def blade_pos(simulation):
        return simulation.structure.blade_x1(blade_idx)[element_idx]

    return Recorder(blade_pos, name, ("x", "y", "z"))


def blade_velocity_5_recorder(name: str, blade_idx: int, element_idx: int | None = None):
    def blade_rel_vel(simulation):
        vel5 = simulation.structure.blade_u5(blade_idx)[element_idx]

        blade_pos1 = simulation.structure.blade_x1(blade_idx)[element_idx]
        wind1 = simulation.wind(blade_pos1)
        wind5 = simulation.structure.x15(wind1, blade_idx)
        return vel5 + wind5

    return Recorder(blade_rel_vel, name, ("u", "v", "w"))


def wind_5_recorder(name: str, blade_idx: int, element_idx: int):
    def wind5(simulation):
        blade_pos1 = simulation.structure.blade_x1(blade_idx)[element_idx]
        wind1 = simulation.wind(blade_pos1)
        return simulation.structure.x15(wind1, blade_idx)

    return Recorder(wind5, name, ("u", "v", "w"))


def w_5_recorder(name: str, blade_idx: int, element_idx: int):
    def w5(simulation):
        w_y        = simulation.aero.rotor.blades[blade_idx].w[0, element_idx]
        w_z        = simulation.aero.rotor.blades[blade_idx].w[1, element_idx]
        # vrel_y     = simulation.aero.rotor.blades[blade_idx].vrel[0, element_idx]
        # vrel_z     = simulation.aero.rotor.blades[blade_idx].vrel[1, element_idx]
        # v0_y       = simulation.aero.rotor.blades[blade_idx].v0[0, element_idx]
        # v0_z       = simulation.aero.rotor.blades[blade_idx].v0[1, element_idx]
        w_y_qs     = simulation.aero.rotor.blades[blade_idx].w_qs[0, element_idx]
        w_z_qs     = simulation.aero.rotor.blades[blade_idx].w_qs[1, element_idx]
        # w_y_int    = simulation.aero.rotor.blades[blade_idx].w_int[0, element_idx]
        # w_z_int    = simulation.aero.rotor.blades[blade_idx].w_int[1, element_idx]
        return w_y, w_z, w_y_qs, w_z_qs #, vrel_y, vrel_z, v0_y, v0_z, w_y_qs, w_z_qs, w_y_int, w_z_int

    return Recorder(w5, name, ("w_y", "w_z", "w_y_qs", "w_z_qs")) # "vrel_y", "vrel_z", "v0_y", "v0_z", "w_qs_y", "w_qs_z", "w_int_y", "w_int_z"))


def p_5_recorder(name: str, blade_idx: int, element_idx: int):
    def aero5(simulation):
        """Record aerodynamic variables for a blade element.
        Parameters
        ----------
        simulation : Simulation
            The simulation object containing the current state of the simulation.
        blade_idx : int
            The index of the blade for which to record the data.
        element_idx : int
            The index of the blade element for which to record the data.
        Returns
        -------
        tuple  
            A tuple of the aerodynamic variables for the blade element.
            The tuple contains (w, p, vrel, v0, w_qs, w_int).

        w : np.ndarray
            The induced velocity at the blade element.
        p : np.ndarray
            The aerodynamic load at the blade element.
        vrel : np.ndarray
            The relative velocity at the blade element.
        v0 : np.ndarray
            The free-stream velocity at the blade element.
        w_qs : np.ndarray
            The quasi-steady induced velocity at the blade element.
        w_int : np.ndarray
            The intermediate induced velocity used in the dynamic wake model at the blade element.



        """
        
        p_y = simulation.aero.rotor.blades[blade_idx].p[0, element_idx]
        p_z = simulation.aero.rotor.blades[blade_idx].p[1, element_idx]        

        return p_y, p_z

    return Recorder(aero5, name, ("p_y", "p_z"))


def mech_out_bladewise_recorder(name: str, blade_idx: int):
    def mech_out(simulation):
        """Record aerodynamic variables for a blade element.
        Parameters
        ----------
        simulation : Simulation
            The simulation object containing the current state of the simulation.
        blade_idx : int
            The index of the blade for which to record the data.
        element_idx : int
            The index of the blade element for which to record the data.
        Returns
        -------
        tuple  
            A tuple of the aerodynamic variables for the blade element.
            The tuple contains (w, p, vrel, v0, w_qs, w_int).

        w : np.ndarray
            The induced velocity at the blade element.
        p : np.ndarray
            The aerodynamic load at the blade element.
        vrel : np.ndarray
            The relative velocity at the blade element.
        v0 : np.ndarray
            The free-stream velocity at the blade element.
        w_qs : np.ndarray
            The quasi-steady induced velocity at the blade element.
        w_int : np.ndarray
            The intermediate induced velocity used in the dynamic wake model at the blade element.



        """

        thrust = simulation.aero.rotor.blades[blade_idx]._thrust
        torque = simulation.aero.rotor.blades[blade_idx]._torque
        power = simulation.aero.rotor.blades[blade_idx]._power

        return thrust, torque, power

    return Recorder(mech_out, name, ("thrust", "torque", "power"))


def mech_out_rotor_recorder(name: str):
    def mech_out(simulation):
        """Record aerodynamic variables for a blade element.
        Parameters

        """

        thrust = simulation.aero.rotor._thrust
        torque = simulation.aero.rotor._torque
        power = simulation.aero.rotor._power

        return thrust, torque, power

    return Recorder(mech_out, name, ("thrust", "torque", "power"))

def generator_out_recorder(name: str):
    def gen_out(simulation):
        """Record generator output."""
        torque_gen = simulation.controller.torque_gen
        power_gen = torque_gen * simulation.structure.omega_shaft

        return torque_gen, power_gen

    return Recorder(gen_out, name, ("torque_gen", "power_gen"))


def controller_recorder(name: str):
    def integral_term(simulation):
        integral_term = simulation.controller.pitch_i
        prev_integral_term = simulation.controller.pitch_i_prev
        gk = simulation.controller.gk


        return integral_term, prev_integral_term, gk
    
    return Recorder(integral_term, name, ("pitch_i", "prev_pitch_i", "gk"))


def power_blade_recorder(blade_idx: int):
    def get_power(simulation):
        return simulation.aero.rotor.blades[blade_idx].power
    
    return Recorder(get_power, "power", ("power",))

def power_rotor_recorder():
    def get_power(simulation):
        return sum(blade.power for blade in simulation.aero.rotor.blades)
    
    return Recorder(get_power, "power", ("power",))

def torque_blade_recorder(blade_idx: int):
    def get_torque(simulation):
        return simulation.aero.rotor.blades[blade_idx].torque
    
    return Recorder(get_torque, "torque", ("torque",))

def torque_rotor_recorder():
    def get_torque(simulation):
        return sum(blade.torque for blade in simulation.aero.rotor.blades)
    
    return Recorder(get_torque, "torque", ("torque",))

def thrust_blade_recorder(blade_idx: int):
    def get_thrust(simulation):
        return simulation.aero.rotor.blades[blade_idx].thrust
    
    return Recorder(get_thrust, "thrust", ("thrust",))

def mech_blade_recorder(blade_idx: int):
    def get_mech(simulation):
        thrust = simulation.aero.rotor.blades[blade_idx].thrust
        torque = simulation.aero.rotor.blades[blade_idx].torque
        power = simulation.aero.rotor.blades[blade_idx].power

        return thrust, torque, power

    return Recorder(get_mech, f"mech_blade_{blade_idx}", ("thrust", "torque", "power"))

def mech_rotor_recorder():
    def get_mech(simulation):
        """ Sum the mechanical output of all blades to get the total mechanical output of the rotor."""
        
        thrust = sum(blade.thrust for blade in simulation.aero.rotor.blades)
        torque = sum(blade.torque for blade in simulation.aero.rotor.blades)
        power = sum(blade.power for blade in simulation.aero.rotor.blades)
      

        return thrust, torque, power

    return Recorder(get_mech, "mech_rotor", ("thrust", "torque", "power"))

def p_recorder(blade_idx: int=0, n_elements=18):
    def get_p(simulation):
        """Record the aerodynamic load p for all blade elements of a blade."""
        p_y = simulation.aero.rotor.blades[blade_idx].p[0, :n_elements]
        p_z = simulation.aero.rotor.blades[blade_idx].p[1, :n_elements]

        return np.concatenate((p_y, p_z))

    return Recorder(get_p, f"p_blade_{blade_idx}", tuple(f"p_{i}" for i in range(2*n_elements)))