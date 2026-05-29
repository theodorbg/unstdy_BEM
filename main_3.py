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
    "flexible_structure": True,
    "rigid_structure": True,
    "compare_flex_rigid": True,
}

# ─── Plot style ─────────────────────────────────────────────────────

plt.rcParams.update({
    "font.size": 17,
    "axes.labelsize": 20,
    "axes.titlesize": 18,
    "legend.fontsize": 14,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
})


# ─── Shared simulation parameters ───────────────────────────────────

omega_init_RPM = 10.0
omega_init     = omega_init_RPM * 2 * np.pi / 60
print(f"Initial rotational speed: {omega_init:.2f} rad/s ({omega_init_RPM} RPM)")

V_hub = 7
shear_exp = 0.2
TI             = 0.1
# Tower parameters
tower_effects = False
# Aero parameters
use_dyn_wake=True
use_dyn_stall=True
use_wake_effects = "geometrical"




dt             = 0.01      # [s]
T              = 80.0     # [s]
print(f"\nTotal simulation time: {T:.2f} seconds")
print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

yaw            = 0   
tilt           = 0
pitch_init     = [0, 0, 0]   

# Mann turbulence box (same dimensions as Assignment 2)
Lz         = 6142.5 * 3
Nz         = 4096 * 3
dimensions = (Nz, 32, 32)
lengths    = (Lz, 185.0, 185.0)

Path("Assignment 3").mkdir(exist_ok=True)



def test_structural_dynamics(use_structural_dynamics: bool, save_tag: str):
    if use_structural_dynamics:
        structure = FlexibleStructure5DOF(omega_init, yaw=yaw, tilt=tilt, pitch_init=pitch_init)
    else:
        structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt, pitch_init=pitch_init)

    wind_profile = ConfiguredWind(
        hub_height=structure.hub_height,
        v_hub=V_hub,
        shear_exp=shear_exp,
        tower_radius=structure.tower_radius if tower_effects else None,
        TI=TI,
    )

    aero = Aero(
        V_hub,
        use_dyn_wake=use_dyn_wake,
        use_dyn_stall=use_dyn_stall,
        use_wake_effects=use_wake_effects,
        use_structural_dynamics=use_structural_dynamics,
    )

    use_controller = True
    controller = Controller.create(use_controller=use_controller)

    recorders = [
        mech_rotor_recorder(name="mech_rotor_recorder"),
        omega_recorder(name="omega"),
        pitch_recorder(name="pitch", blade_idx=0),
        generator_out_recorder(name="generator_out"),
        tip_deflection_recorder_5DOF(name="tip_defl"),
        deflection_recorder_5DOF(name="defl", element_idx=-1),
        root_bending_moment_recorder_5DOF(name="root_bend"),
    ]

    simulation = Simulation(
        structure=structure,
        aero=aero,
        wind=wind_profile,
        controller=controller,
        recorders=recorders,
    )

    simulation.run(dt, T)
    simulation.save_recorders(f"sim_data/{save_tag}", overwrite=True)
    return simulation.get_recorders()

# Run cases
flex_data = None
rigid_data = None

if do["flexible_structure"] or do["compare_flex_rigid"]:
    flex_data = test_structural_dynamics(use_structural_dynamics=True, save_tag="flexible")

if do["rigid_structure"] or do["compare_flex_rigid"]:
    rigid_data = test_structural_dynamics(use_structural_dynamics=False, save_tag="rigid")

# Compare plots
if do["compare_flex_rigid"]:
    if flex_data is None or rigid_data is None:
        raise ValueError("Need both flexible and rigid runs for compare_flex_rigid.")

    t = flex_data["time"]

    # Power / speed / pitch (flex vs rigid together)
    plot_flexible(
        x_val=t,
        y_values=[
            [
                flex_data["mech_rotor_recorder"]["power"] / 1e6,
                rigid_data["mech_rotor_recorder"]["power"] / 1e6,
                flex_data["generator_out"]["power_gen"] / 1e6,
                rigid_data["generator_out"]["power_gen"] / 1e6,
            ],
            [flex_data["omega"]["omega"], rigid_data["omega"]["omega"]],
            [flex_data["pitch"]["pitch"], rigid_data["pitch"]["pitch"]],
        ],
        labels=[
            [r"$P_{mech}$ flex", r"$P_{mech}$ rigid", r"$P_{EL}$ flex", r"$P_{EL}$ rigid"],
            [r"$\omega$ flex", r"$\omega$ rigid"],
            [r"$\theta$ flex", r"$\theta$ rigid"],
        ],
        x_label="Time [s]",
        y_units=["Power [MW]", r"$\omega$ [rad/s]", r"$\theta$ [deg]"],
        save_name="compare_flex_rigid_power_omega_pitch",
        structural_dynamics=True,
    )

    # Deflection / root moments (rigid should be ~0)
    zeros = np.zeros_like(t)
    plot_flexible(
        x_val=t,
        y_values=[
            [flex_data["tip_defl"]["tip_edge"], rigid_data["tip_defl"]["tip_edge"]],
            [flex_data["tip_defl"]["tip_flap"], rigid_data["tip_defl"]["tip_flap"]],
            [flex_data["root_bend"]["M_flap"], rigid_data["root_bend"]["M_flap"]],
            [flex_data["root_bend"]["M_edge"], rigid_data["root_bend"]["M_edge"]],
        ],
        labels=[
            ["tip edge flex", "tip edge rigid"],
            ["tip flap flex", "tip flap rigid"],
            ["M_flap flex", "M_flap rigid"],
            ["M_edge flex", "M_edge rigid"],
        ],
        x_label="Time [s]",
        y_units=[
            "edgewise tip deflection [m]",
            "flapwise tip deflection [m]",
            "root bending moment (flap) [Nm]",
            "root bending moment (edge) [Nm]",
        ],
        save_name="compare_flex_rigid_deflection_bendingmoment",
    )



