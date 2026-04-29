from unittest import signals

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re

from recorder import (
    mech_blade_recorder,
    mech_rotor_recorder,
    omega_recorder,
    pitch_recorder,
    cp_rotor_recorder,
    blade_position_1_recorder,
    blade_velocity_5_recorder,
    time_recorder,
    wind_5_recorder,
    w_5_recorder,
    generator_out_recorder,
    controller_recorder,
    py_recorder,
    pz_recorder,
)
from simulation import Simulation
from structure import RigidStructure, FlexibleStructure_5dof
from wind import ConstantWind, ShearWind, WindWithTower, TurbWind, ConfiguredWind
from aero import Aero
from plots import *
from controller import Controller
from table_printer import *
from dtu10mw_data import df_elastic_pitch, df_stiff_pitch, df_power_turb, df_power_cfd, df_power_bem, df_ashes_shear, df_ashes_turb

do = {
    "load_mode_shapes": True
    }

if do["load_mode_shapes"]:
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 1.005
    yaw = 0
    tilt = 0 

    FlexibleStructure = FlexibleStructure_5dof(omega_init, yaw=yaw, tilt=tilt, pitch_init = [0, 0, 0])
    # plot the modeshapes: self.u1_flap, self.u1_edge, self.u2_flap
    # confirm that they are loaded correctly in
    plot_flexible(
        x_val = FlexibleStructure.r,
        y_values=[
            [FlexibleStructure.u1_flap[0]],
            [FlexibleStructure.u1_flap[1]],
            [FlexibleStructure.u1_edge[0]],
            [FlexibleStructure.u1_edge[1]],
            [FlexibleStructure.u2_flap[0]],
            [FlexibleStructure.u2_flap[1]]],
        labels=[
            ["u1 flap y"],
            ["u1 flap z"],
            ["u1 edge y"],
            ["u1 edge z"],
            ["u2 flap y"],
            ["u2 flap z"]
        ],
        x_label="Radial position (m)",
        y_units=[
            ["u1 flap y (m)"],
            ["u1 flap z (m)"],
            ["u1 edge y (m)"],
            ["u1 edge z (m)"],
            ["u2 flap y (m)"],
            ["u2 flap z (m)"]
        ],
        save_name="modeshapes_txt.png")
    


    