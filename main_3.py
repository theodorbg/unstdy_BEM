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
    flap1_recorder,
    edge1_recorder,
    flap2_recorder
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
    "flexible_structure": True,
    "rigid_structure": True,
    }


def test_structural_dynamics(use_structural_dynamics: bool):
        # SET UP SIMULATION
        # structural parameters
        omega_init = 1.005
        yaw = 0
        tilt = 0 
        
        
        if use_structural_dynamics:
            structure = FlexibleStructure_5dof(omega_init, yaw=yaw, tilt=tilt, pitch_init = [0, 0, 0])
        else:
            structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt)
            
        
        # Wind parameters
        shear_exp = 0
        V_hub = 11.4
        TI = 0

        # Tower parameters
        tower_effects = False

        # Aero parameters
        use_dyn_wake=True
        use_dyn_stall=True
        use_wake_effects = "geometrical"

        # Simulation parameters
        N = 8
        # T = N * 2 * np.pi / omega_init
        T = 300
        print(f"\nTotal simulation time: {T:.2f} seconds")
        dt = 0.1
        print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

        # WIND INITIALISATION
        wind_profile = ConfiguredWind(
                hub_height=structure.hub_height,
                v_hub=V_hub,
                shear_exp=shear_exp,
                tower_radius=structure.tower_radius if tower_effects else None,
                TI=TI,
            )
            
        # AERO INITIALISATION
        aero = Aero(
            V_hub,
            use_dyn_wake=use_dyn_wake,
            use_dyn_stall=use_dyn_stall,
            use_wake_effects=use_wake_effects,
            use_structural_dynamics=use_structural_dynamics
            )

        # CONTROLLER INITIALISATION
        use_controller=True
        controller = Controller.create(use_controller=use_controller) 

        # RECORDERS    
        recorders = []
        recorders.append(mech_rotor_recorder(name="mech_rotor_recorder"))
        recorders.append(omega_recorder(name="omega"))
        recorders.append(pitch_recorder(name="pitch", blade_idx=0))
        recorders.append(generator_out_recorder(name="generator_out"))
        if use_structural_dynamics:
            recorders.append(flap1_recorder(name="flap1"))
            recorders.append(edge1_recorder(name="edge1"))
            recorders.append(flap2_recorder(name="flap2"))


        # Set up simulation, run, and save wind recorder data1
        print(f"\nRunning simulation with parameters:\n")
        print(f"omega init = {omega_init:.2f} rad/s ")
        print(f"yaw = {yaw} degrees,")  
        print(f"tilt = {tilt} degrees")
        print(f"shear_exp = {shear_exp}")
        print(f"V_hub={V_hub} m/s")
        print(f"use_dyn_wake = {use_dyn_wake}")
        print(f"use_dyn_stall = {use_dyn_stall}")
        print(f"use_wake_effects = {use_wake_effects}")
        print(f"tower_effects = {tower_effects}")
        print(f"controller = {use_controller}")

        simulation = Simulation(
            structure=structure,
            aero=aero,
            wind=wind_profile,
            controller=controller,
            recorders=recorders)
        
        simulation.run(dt, T)
        print("\nSimulation complete. Saving data...\n")
        simulation.save_recorders("sim_data", overwrite=True)

        # EXTRACT DATA FROM RECORDERS
        # Get data (saving above not needed for this) for plotting
        data = simulation.get_recorders()
        azimuth = data["time"] * omega_init / (2 * np.pi) * 360
        t = data["time"]
        
        power_mech = data["mech_rotor_recorder"]["power"]
        omega = data["omega"]["omega"]
        pitch = data["pitch"]["pitch"]
        power_gen = data["generator_out"]["power_gen"]
        if use_structural_dynamics:
            flap1_y = data["flap1"]["y"]
            flap1_z = data["flap1"]["z"]

            edge1_y = data["edge1"]["y"]
            edge1_z = data["edge1"]["z"]

            flap2_y = data["flap2"]["y"]
            flap2_z = data["flap2"]["z"]

        
        plot_flexible(
        x_val=t,
        y_values=[
            [power_mech/1e6, power_gen/1e6],
            [omega],
            [pitch]
        ],
        labels=[
            [r"$P_{mech}$", r"$P_{EL}$"],
            ["Rotor Speed"],
            ["Pitch Angle"]
        ],
        x_label="Time [s]",
        y_units=[
            "Power [MW]",
            r"$\omega$ [rad/s]",
            r"$\theta$ [deg]"
        ],
        save_name="controller_test",
        structural_dynamics=use_structural_dynamics)
        
        if use_structural_dynamics:

            plot_flexible(
            x_val=t,
            y_values=[
                [flap1_y],
                [flap1_z],
                [edge1_y],
                [edge1_z],
                [flap2_y],
                [flap2_z],
            ],
            labels=[
                ["flap1 y"],
                ["flap1 z"],
                ["edge1 y"],
                ["edge1 z"],
                ["flap2 y"],
                ["flap2 z"]
            ],
            x_label="Time [s]",
            y_units=[
                "flapwise 1 y deflection [m]",
                "flapwise 2 z deflection [m]",
                "edgewise 1 y deflection [m]",
                "edgewise 2 z deflection [m]",
                "flapwise 1 y deflection [m]",
                "flapwise 2 z deflection [m]"
            ],
            save_name="tip_deflections"
            )

    
if do["flexible_structure"]:
    test_structural_dynamics(use_structural_dynamics=True)
    
if do["rigid_structure"]:
    test_structural_dynamics(use_structural_dynamics=False)



