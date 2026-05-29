
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import os

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
    root_bending_moment_recorder_5DOF,
    deflection_recorder_11DOF,
    tip_deflection_recorder_11DOF,
    root_bending_moment_recorder_11DOF,
    tower_displacement_recorder,
    modal_amplitudes_recorder_5DOF,
    modal_amplitudes_recorder_11DOF
)
from simulation import Simulation
from structure import RigidStructure, FlexibleStructure5DOF, FlexibleStructure11DOF
from wind import ConstantWind, ShearWind, WindWithTower, TurbWind, ConfiguredWind
from aero import Aero
from plots import *
from controller import Controller
from table_printer import *
from dtu10mw_data import df_elastic_pitch, df_stiff_pitch, df_power_turb, df_power_cfd, df_power_bem, df_ashes_shear, df_ashes_turb

# ── Plot style globals ───────────────────────────────────────────────
FONT_SIZE       = 9
TITLE_SIZE      = 10
LABEL_SIZE      = 9
TICK_SIZE       = 8
LEGEND_SIZE     = 7
LINE_WIDTH      = 1.2

plt.rcParams.update({
    "font.size":        FONT_SIZE,
    "axes.titlesize":   TITLE_SIZE,
    "axes.labelsize":   LABEL_SIZE,
    "xtick.labelsize":  TICK_SIZE,
    "ytick.labelsize":  TICK_SIZE,
    "legend.fontsize":  LEGEND_SIZE,
    "lines.linewidth":  LINE_WIDTH,
})

do = {
    "rigid_structure": False,
    "5_dof": False,
    "11_dof": True,
    "compare_structures": True,
}

# ─── Shared simulation parameters ───────────────────────────────────

omega_init_RPM = 5.0
omega_init     = omega_init_RPM * 2 * np.pi / 60
print(f"Initial rotational speed: {omega_init:.2f} rad/s ({omega_init_RPM} RPM)")

v_hub = [7, 18]
turb_intensity = [0, 0.1]

BLADE_POSITION = 88 #M

def test_structure(structure,
                   V_hub,
                   TI,
                   T=400.0,
                   additional_recorders=False
                   ):
    structure = structure
    wind_profile = ConfiguredWind(
        hub_height=structure.hub_height,
        v_hub=V_hub,
        shear_exp=0.2,
        TI=TI,
        tower_radius=None # because no tower effects
    )
    aero = Aero(
        V_hub=V_hub,
        use_dyn_wake=True,
        use_dyn_stall=True,
        use_wake_effects="empirical",
        )
    controller = Controller.create(use_controller=True)
    recorders = [
        # power
        mech_rotor_recorder(name="mech_rotor_recorder"),
        mech_blade_recorder(name="mech_blade_recorder", blade_idx=0),
        # generator power
        generator_out_recorder(name="generator_out_recorder"),

        omega_recorder(name="omega_recorder"),
        pitch_recorder(name="pitch_recorder", blade_idx=0),
        ] 
    if additional_recorders:
        recorders.extend(additional_recorders)
    simulation = Simulation(
        structure=structure,
        aero=aero,
        wind=wind_profile,
        controller=controller,
        recorders=recorders
    )
    
    simulation.run(dt=0.01, T=T)
    simulation.save_recorders(f"sim_data/{structure.__class__.__name__}_V_hub_{V_hub}_TI_{TI}", overwrite=True)
    return simulation.get_recorders()
    
def load_recorders(folder: str) -> dict:
    """Load all CSVs in a folder into a dict keyed by filename (without .csv)."""
    recorders = {}
    for f in os.listdir(folder):
        if f.endswith(".csv"):
            name = f.replace(".csv", "")
            recorders[name] = pd.read_csv(os.path.join(folder, f))
    return recorders

if do["rigid_structure"]:
    section_divider("INITIALIZING RIGID STRUCTURE SCRIPT")
    structure_rigid = RigidStructure(omega_init=omega_init)
    recorders_rigid = {}
    for v in v_hub:
        for ti in turb_intensity:
            print(f"Running rigid structure case with V_hub={v} m/s and TI={ti}")
            recorders = test_structure(
                structure=structure_rigid,
                V_hub=v,
                TI=ti,
                T=400.0
            )
            recorders_rigid[(v, ti)] = recorders
    section_divider("FINISHED RIGID STRUCTURE SCRIPT")

if do["5_dof"]:
    section_divider("INITIALIZING 5-DOF STRUCTURE SCRIPT")

    recorders_5dof = [
        deflection_recorder_5DOF(name="deflection_recorder_5DOF", element_idx=BLADE_POSITION),
        tip_deflection_recorder_5DOF(name="tip_deflection_recorder_5DOF"),
        root_bending_moment_recorder_5DOF(name="root_bending_moment_recorder_5DOF"),
        tower_displacement_recorder(name="tower_displacement_recorder"),
        ]
    structure_5dof = FlexibleStructure5DOF(omega_init=omega_init, use_gravity=True)
    recorders_5dof = test_structure(
        structure=structure_5dof,
        V_hub=18.0,
        TI=turb_intensity[0],
        T=60.0,
        additional_recorders=recorders_5dof
    )
    section_divider("FINISHED 5-DOF STRUCTURE SCRIPT")
    
if do["11_dof"]:
    section_divider("INITIALIZING 11-DOF STRUCTURE SCRIPT")
    recorders_11dof = [
    deflection_recorder_11DOF(name="deflection_recorder_11DOF", element_idx=BLADE_POSITION, blade_idx=0),
    tip_deflection_recorder_11DOF(name="tip_deflection_recorder_11DOF"),
    root_bending_moment_recorder_11DOF(name="root_bending_moment_recorder_11DOF"),
    tower_displacement_recorder(name="tower_displacement_recorder"),
    ]
    structure_11dof = FlexibleStructure11DOF(omega_init=omega_init, use_gravity=True)
    recorders_11dof = test_structure(
        structure=structure_11dof,
        V_hub=25.0,
        TI=turb_intensity[0],
        T=60.0,
        additional_recorders=recorders_11dof
    )
    section_divider("FINISHED 11-DOF STRUCTURE SCRIPT")
            
if do["compare_structures"]:
    section_divider("COMPARING STRUCTURES")

    recorders_rigid = load_recorders("sim_data/RigidStructure_V_hub_7_TI_0")
    recorders_5dof  = load_recorders("sim_data/FlexibleStructure5DOF_V_hub_7_TI_0")
    recorders_11dof = load_recorders("sim_data/FlexibleStructure11DOF_V_hub_7_TI_0")

    t_r  = recorders_rigid["mech_rotor_recorder"]["time"]
    t_5  = recorders_5dof["mech_rotor_recorder"]["time"]
    t_11 = recorders_11dof["mech_rotor_recorder"]["time"]
    
    

    colors = {"rigid": "black", "5dof": "tab:blue", "11dof": "tab:green"}

    # ── Figure 1: Power / Omega / Pitch ──────────────────────────────
    fig1, axes1 = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    fig1.suptitle(f"Dynamics — $V_{{hub}}$ = {V_hub[0]} m/s, TI = {TI[0]}")

    ax = axes1[0]
    ax.plot(t_r,  recorders_rigid["mech_rotor_recorder"]["power"] / 1e6,        color=colors["rigid"],  label="Mechanical Rigid")
    ax.plot(t_5,  recorders_5dof["mech_rotor_recorder"]["power"] / 1e6,         color=colors["5dof"],   label="Mechanical 5DOF")
    ax.plot(t_11, recorders_11dof["mech_rotor_recorder"]["power"] / 1e6,        color=colors["11dof"],  label="Mechanical 11DOF")
    ax.plot(t_r,  recorders_rigid["generator_out_recorder"]["power_gen"] / 1e6, color=colors["rigid"],  ls="--", label="Generator rigid")
    ax.plot(t_5,  recorders_5dof["generator_out_recorder"]["power_gen"] / 1e6,  color=colors["5dof"],   ls="--", label="Generator 5DOF")
    ax.plot(t_11, recorders_11dof["generator_out_recorder"]["power_gen"] / 1e6, color=colors["11dof"],  ls="--", label="Generator 11DOF")
    ax.set_ylabel("Power [MW]")
    ax.legend(ncol=2)

    ax = axes1[1]
    ax.plot(t_r,  recorders_rigid["omega_recorder"]["omega"],  color=colors["rigid"],  label="Rigid")
    ax.plot(t_5,  recorders_5dof["omega_recorder"]["omega"],   color=colors["5dof"],   label="5DOF")
    ax.plot(t_11, recorders_11dof["omega_recorder"]["omega"],  color=colors["11dof"],  label="11DOF")
    ax.set_ylabel("$\\omega$ [rad/s]")
    ax.legend()

    ax = axes1[2]
    ax.plot(t_r,  recorders_rigid["pitch_recorder"]["pitch"],  color=colors["rigid"],  label="Rigid")
    ax.plot(t_5,  recorders_5dof["pitch_recorder"]["pitch"],   color=colors["5dof"],   label="5DOF")
    ax.plot(t_11, recorders_11dof["pitch_recorder"]["pitch"],  color=colors["11dof"],  label="11DOF")
    ax.set_ylabel("Pitch [deg]")
    ax.set_xlabel("Time [s]")
    ax.legend()

    fig1.tight_layout()
    plt.savefig("compare_power_omega_pitch.png", dpi=150, bbox_inches="tight")

    # ── Figure 2: Flapwise (left) / Edgewise (right) ─────────────────
    fig2, axes2 = plt.subplots(3, 2, figsize=(14, 10), sharex=True)
    fig2.suptitle(f"Deflections & Loads — $V_{{hub}}$ = {V_hub[0]} m/s, TI = {TI[0]}")

    # [0, left] Tip deflection — flapwise
    ax = axes2[0, 0]
    ax.plot(t_5,  recorders_5dof["tip_deflection_recorder_5DOF"]["tip_flap"],   color=colors["5dof"],   label="5DOF")
    ax.plot(t_11, recorders_11dof["tip_deflection_recorder_11DOF"]["tip_flap"], color=colors["11dof"],  label="11DOF")
    ax.set_ylabel("Tip deflection [m]")
    ax.set_title("Flapwise")
    ax.legend()

    # [0, right] Tip deflection — edgewise
    ax = axes2[0, 1]
    ax.plot(t_5,  recorders_5dof["tip_deflection_recorder_5DOF"]["tip_edge"],   color=colors["5dof"],   label="5DOF")
    ax.plot(t_11, recorders_11dof["tip_deflection_recorder_11DOF"]["tip_edge"], color=colors["11dof"],  label="11DOF")
    ax.set_title("Edgewise")
    ax.legend()

    # [1, left] Station deflection — flapwise
    ax = axes2[1, 0]
    ax.plot(t_5,  recorders_5dof["deflection_recorder_5DOF"]["flap"],   color=colors["5dof"],   label="5DOF")
    ax.plot(t_11, recorders_11dof["deflection_recorder_11DOF"]["flap"], color=colors["11dof"],  label="11DOF")
    ax.set_ylabel("Deflection r=15 [m]")
    ax.legend()

    # [1, right] Station deflection — edgewise
    ax = axes2[1, 1]
    ax.plot(t_5,  recorders_5dof["deflection_recorder_5DOF"]["edge"],   color=colors["5dof"],   label="5DOF")
    ax.plot(t_11, recorders_11dof["deflection_recorder_11DOF"]["edge"], color=colors["11dof"],  label="11DOF")
    ax.legend()

    # [2, left] Root BM — flapwise
    ax = axes2[2, 0]
    ax.plot(t_5,  recorders_5dof["root_bending_moment_recorder_5DOF"]["M_flap"] / 1e6,   color=colors["5dof"],   label="5DOF")
    ax.plot(t_11, recorders_11dof["root_bending_moment_recorder_11DOF"]["M_flap"] / 1e6, color=colors["11dof"],  label="11DOF")
    ax.set_ylabel("Root BM [MNm]")
    ax.set_xlabel("Time [s]")
    ax.legend()

    # [2, right] Root BM — edgewise
    ax = axes2[2, 1]
    ax.plot(t_5,  recorders_5dof["root_bending_moment_recorder_5DOF"]["M_edge"] / 1e6,   color=colors["5dof"],   label="5DOF")
    ax.plot(t_11, recorders_11dof["root_bending_moment_recorder_11DOF"]["M_edge"] / 1e6, color=colors["11dof"],  label="11DOF")
    ax.set_xlabel("Time [s]")
    ax.legend()

    fig2.tight_layout()
    plt.savefig("compare_deflections.png", dpi=150, bbox_inches="tight")

    plt.show()
    section_divider("FINISHED COMPARING STRUCTURES")