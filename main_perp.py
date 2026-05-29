import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

from recorder import (
    mech_blade_recorder, mech_rotor_recorder, omega_recorder, pitch_recorder,
    cp_rotor_recorder, blade_position_1_recorder, blade_velocity_5_recorder,
    time_recorder, wind_5_recorder, w_5_recorder, generator_out_recorder,
    controller_recorder, py_recorder, pz_recorder,
    tip_deflection_recorder_5DOF, deflection_recorder_5DOF, root_bending_moment_recorder_5DOF,
    deflection_recorder_11DOF, tip_deflection_recorder_11DOF, root_bending_moment_recorder_11DOF,
    tower_displacement_recorder, modal_amplitudes_recorder_5DOF, modal_amplitudes_recorder_11DOF
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
FONT_SIZE, TITLE_SIZE, LABEL_SIZE = 9, 10, 9
TICK_SIZE, LEGEND_SIZE, LINE_WIDTH = 8, 7, 1.2

plt.rcParams.update({
    "font.size": FONT_SIZE, "axes.titlesize": TITLE_SIZE, "axes.labelsize": LABEL_SIZE,
    "xtick.labelsize": TICK_SIZE, "ytick.labelsize": TICK_SIZE,
    "legend.fontsize": LEGEND_SIZE, "lines.linewidth": LINE_WIDTH,
})

do = {
    "rigid_structure": True,
    "5_dof":           True,
    "11_dof":          True,
    "compare_structures": True,
}

# ── Shared simulation parameters ─────────────────────────────────────
omega_init_RPM = 5.0
omega_init     = omega_init_RPM * 2 * np.pi / 60
print(f"Initial rotational speed: {omega_init:.2f} rad/s ({omega_init_RPM} RPM)")

v_hub          = [7, 18]
turb_intensity = [0, 0.1]
T              = 60.0
BLADE_POSITION = 15  # radial station index

# ── Color/style encoding ─────────────────────────────────────────────
COLORS_V  = {7: "tab:blue", 18: "tab:orange"}
LS_TI     = {0: "-", 0.1: "--"}
MARKERS   = {"RigidStructure": "o", "FlexibleStructure5DOF": "s", "FlexibleStructure11DOF": "^"}

def make_extra_recorders_5dof():
    return [
        deflection_recorder_5DOF("deflection_recorder_5DOF", element_idx=BLADE_POSITION),
        tip_deflection_recorder_5DOF("tip_deflection_recorder_5DOF"),
        root_bending_moment_recorder_5DOF("root_bending_moment_recorder_5DOF"),
        tower_displacement_recorder("tower_displacement_recorder"),
    ]

def make_extra_recorders_11dof():
    return [
        deflection_recorder_11DOF("deflection_recorder_11DOF", element_idx=BLADE_POSITION, blade_idx=0),
        tip_deflection_recorder_11DOF("tip_deflection_recorder_11DOF"),
        root_bending_moment_recorder_11DOF("root_bending_moment_recorder_11DOF"),
        tower_displacement_recorder("tower_displacement_recorder"),
    ]

def test_structure(structure, V_hub, TI, additional_recorders=None):
    wind_profile = ConfiguredWind(
        hub_height=structure.hub_height, v_hub=V_hub, shear_exp=0.2,
        TI=TI, tower_radius=None
    )
    aero = Aero(V_hub=V_hub, use_dyn_wake=True, use_dyn_stall=True, use_wake_effects="empirical")
    controller = Controller.create(use_controller=True)
    recorders = [
        mech_rotor_recorder(name="mech_rotor_recorder"),
        mech_blade_recorder(name="mech_blade_recorder", blade_idx=0),
        generator_out_recorder(name="generator_out_recorder"),
        omega_recorder(name="omega_recorder"),
        pitch_recorder(name="pitch_recorder", blade_idx=0),
    ]
    if additional_recorders:
        recorders.extend(additional_recorders)
    simulation = Simulation(structure=structure, aero=aero, wind=wind_profile,
                            controller=controller, recorders=recorders)
    simulation.run(dt=0.05, T=T)
    simulation.save_recorders(
        f"sim_data/{structure.__class__.__name__}_V_hub_{V_hub}_TI_{TI}", overwrite=True)
    return simulation.get_recorders()

def load_recorders(folder: str) -> dict:
    recorders = {}
    for f in os.listdir(folder):
        if f.endswith(".csv"):
            recorders[f.replace(".csv", "")] = pd.read_csv(os.path.join(folder, f))
    return recorders

def load_all(structure_name: str) -> dict:
    """Load all (v, ti) cases for a structure. Returns dict keyed by (v, ti)."""
    result = {}
    for v in v_hub:
        for ti in turb_intensity:
            folder = f"sim_data/{structure_name}_V_hub_{v}_TI_{ti}"
            if os.path.isdir(folder):
                result[(v, ti)] = load_recorders(folder)
    return result

# ── Run simulations ───────────────────────────────────────────────────
if do["rigid_structure"]:
    section_divider("INITIALIZING RIGID STRUCTURE SCRIPT")
    recorders_rigid = {}
    for v in v_hub:
        for ti in turb_intensity:
            print(f"  Rigid V={v} TI={ti}")
            structure_rigid = RigidStructure(omega_init=omega_init)
            recorders_rigid[(v, ti)] = test_structure(structure_rigid, v, ti)
    section_divider("FINISHED RIGID STRUCTURE SCRIPT")

if do["5_dof"]:
    section_divider("INITIALIZING 5-DOF STRUCTURE SCRIPT")
    recorders_5dof = {}
    for v in v_hub:
        for ti in turb_intensity:
            print(f"  5DOF V={v} TI={ti}")
            recorders_5dof[(v, ti)] = test_structure(
                FlexibleStructure5DOF(omega_init=omega_init, use_gravity=True),
                v, ti, additional_recorders=make_extra_recorders_5dof()
            )
    section_divider("FINISHED 5-DOF STRUCTURE SCRIPT")

if do["11_dof"]:
    section_divider("INITIALIZING 11-DOF STRUCTURE SCRIPT")
    recorders_11dof = {}
    for v in v_hub:
        for ti in turb_intensity:
            print(f"  11DOF V={v} TI={ti}")
            recorders_11dof[(v, ti)] = test_structure(
                FlexibleStructure11DOF(omega_init=omega_init, use_gravity=True),
                v, ti, additional_recorders=make_extra_recorders_11dof()
            )
    section_divider("FINISHED 11-DOF STRUCTURE SCRIPT")

# ── Compare ───────────────────────────────────────────────────────────
if do["compare_structures"]:
    section_divider("COMPARING STRUCTURES")

    recorders_rigid = load_all("RigidStructure")
    recorders_5dof  = load_all("FlexibleStructure5DOF")
    recorders_11dof = load_all("FlexibleStructure11DOF")

    # Build series list — one entry per (structure, v, ti) combination
    def build_series(rec_dict, struct_name):
        series = []
        for (v, ti), rec in rec_dict.items():
            series.append({
                "recorders":  rec,
                "label":      f"{struct_name} V={v} TI={ti}",
                "color":      COLORS_V[v],
                "ls":         LS_TI[ti],
                "struct":     struct_name,
                "v":          v,
                "ti":         ti,
            })
        return series

    series_rigid = build_series(recorders_rigid, "Rigid")
    series_5dof  = build_series(recorders_5dof,  "5DOF")
    series_11dof = build_series(recorders_11dof, "11DOF")
    series_all   = series_rigid + series_5dof + series_11dof
    series_flex  = series_5dof + series_11dof

    # ── Figure 1: Power / Omega / Pitch ──────────────────────────────
    fig1, axes1 = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    fig1.suptitle("Dynamics comparison")

    for s in series_all:
        t   = s["recorders"]["mech_rotor_recorder"]["time"]
        rec = s["recorders"]
        axes1[0].plot(t, rec["mech_rotor_recorder"]["power"] / 1e6,
                      color=s["color"], ls=s["ls"], label=s["label"])
        axes1[0].plot(t, rec["generator_out_recorder"]["power_gen"] / 1e6,
                      color=s["color"], ls=s["ls"], alpha=0.4)
        axes1[1].plot(t, rec["omega_recorder"]["omega"],
                      color=s["color"], ls=s["ls"], label=s["label"])
        axes1[2].plot(t, rec["pitch_recorder"]["pitch"],
                      color=s["color"], ls=s["ls"], label=s["label"])

    axes1[0].set_ylabel("Power [MW]")
    axes1[0].legend(ncol=2)
    axes1[1].set_ylabel("$\\omega$ [rad/s]")
    axes1[1].legend(ncol=2)
    axes1[2].set_ylabel("Pitch [deg]")
    axes1[2].set_xlabel("Time [s]")
    axes1[2].legend(ncol=2)
    fig1.tight_layout()
    plt.savefig("compare_power_omega_pitch.png", dpi=150, bbox_inches="tight")

    # ── Figure 2: Flapwise (left) / Edgewise (right) ─────────────────
    fig2, axes2 = plt.subplots(3, 2, figsize=(14, 10), sharex=True)
    fig2.suptitle("Deflections & Loads comparison")

    REC_MAP = {
        "5DOF":  {"tip": "tip_deflection_recorder_5DOF",
                  "def": "deflection_recorder_5DOF",
                  "bm":  "root_bending_moment_recorder_5DOF"},
        "11DOF": {"tip": "tip_deflection_recorder_11DOF",
                  "def": "deflection_recorder_11DOF",
                  "bm":  "root_bending_moment_recorder_11DOF"},
    }

    for s in series_flex:
        rec  = s["recorders"]
        t    = rec["mech_rotor_recorder"]["time"]
        rm   = REC_MAP[s["struct"]]

        axes2[0, 0].plot(t, rec[rm["tip"]]["tip_flap"], color=s["color"], ls=s["ls"], label=s["label"])
        axes2[0, 1].plot(t, rec[rm["tip"]]["tip_edge"], color=s["color"], ls=s["ls"], label=s["label"])
        axes2[1, 0].plot(t, rec[rm["def"]]["flap"],     color=s["color"], ls=s["ls"], label=s["label"])
        axes2[1, 1].plot(t, rec[rm["def"]]["edge"],     color=s["color"], ls=s["ls"], label=s["label"])
        axes2[2, 0].plot(t, rec[rm["bm"]]["M_flap"] / 1e6, color=s["color"], ls=s["ls"], label=s["label"])
        axes2[2, 1].plot(t, rec[rm["bm"]]["M_edge"] / 1e6, color=s["color"], ls=s["ls"], label=s["label"])

    axes2[0, 0].set_ylabel("Tip deflection [m]");  axes2[0, 0].set_title("Flapwise")
    axes2[0, 1].set_title("Edgewise")
    axes2[1, 0].set_ylabel(f"Deflection idx={BLADE_POSITION} [m]")
    axes2[2, 0].set_ylabel("Root BM [MNm]");       axes2[2, 0].set_xlabel("Time [s]")
    axes2[2, 1].set_xlabel("Time [s]")
    for ax in axes2.flat:
        ax.legend(ncol=2)

    fig2.tight_layout()
    plt.savefig("compare_deflections.png", dpi=150, bbox_inches="tight")

    plt.show()
    section_divider("FINISHED COMPARING STRUCTURES")