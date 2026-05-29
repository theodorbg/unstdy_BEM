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
    tip_deflection_recorder_5DOF,
    deflection_recorder_5DOF,
    root_bending_moment_recorder_5DOF
)
from simulation import Simulation
from structure import RigidStructure, FlexibleStructure5DOF
from wind import ConstantWind, ShearWind, WindWithTower, TurbWind, ConfiguredWind
from aero import Aero
from plots import *
from controller import Controller
from table_printer import *
from dtu10mw_data import df_elastic_pitch, df_stiff_pitch, df_power_turb, df_power_cfd, df_power_bem, df_ashes_shear, df_ashes_turb

do = {
    "1": True,
    "rigid_structure": True,
    "compare_flex_rigid": True,
}
