from unittest import signals

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
from structure import RigidStructure
from wind import ConstantWind, ShearWind, WindWithTower, TurbWind, ConfiguredWind
from aero import Aero
from plots import *
from controller import Controller
from table_printer import *
from dtu10mw_data import df_elastic_pitch, df_stiff_pitch, df_power_turb, df_power_cfd, df_power_bem

do = {
    "2_1_main": False,
    "2_1_loop": False,
    "2_1_plots": False,
    "2_1_plots_compare_10mw": False,
    "2_2_turb_loop": True,
}

if do["2_1_main"]:
    
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 1.005
    yaw = 0
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt, pitch_init = [0, 0, 0])
        
    # Wind parameters
    shear_exp = 0
    V_hub = 11.4
    TI = 0

    # Tower parameters
    tower_effects = True

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
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall, use_wake_effects=use_wake_effects)

    # CONTROLLER INITIALISATION
    use_controller=True
    controller = Controller.create(use_controller=use_controller) 

    
    #%% RECORDERS    
    recorders = []
    recorders.append(cp_rotor_recorder(name="cp_rotor"))
    recorders.append(mech_rotor_recorder(name="mech_out_rotor"))
    recorders.append(generator_out_recorder(name="generator_out"))
    recorders.append(omega_recorder(name="omega"))
    recorders.append(pitch_recorder(name="pitch", blade_idx=0))
    
    
    

    #%% Set up simulation, run, and save wind recorder data1
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

    simulation = Simulation(structure, aero, wind=wind_profile, controller=controller, recorders=recorders)
    simulation.run(dt, T)
    print("\nSimulation complete. Saving data...\n")
    simulation.save_recorders("sim_data", overwrite=True)

    #%% EXTRACT DATA FROM RECORDERS
    # Get data (saving above not needed for this) for plotting
    data = simulation.get_recorders()
    azimuth = data["time"] * omega_init / (2 * np.pi) * 360
    t = data["time"]

    cp_rotor = data["cp_rotor"]["cp_rotor"]
    mech_out_rotor = data["mech_out_rotor"]["power"]
    power_gen = data["generator_out"]["power_gen"]
    omega = data["omega"]["omega"]
    pitch = data["pitch"]["pitch"]

    # save the average value for the last rotation of each parameter
    last_rotation_mask = azimuth >= (360 * (N-1))
    cp_rotor_last_rotation = cp_rotor[last_rotation_mask]
    mech_out_rotor_last_rotation = mech_out_rotor[last_rotation_mask]
    power_gen_last_rotation = power_gen[last_rotation_mask]
    omega_last_rotation = omega[last_rotation_mask]
    pitch_last_rotation = pitch[last_rotation_mask]
    print(f"Average rotor Cp in last rotation: {np.mean(cp_rotor_last_rotation):.4f}")
    print(f"Average mechanical power in last rotation: {np.mean(mech_out_rotor_last_rotation):.2f} W")
    print(f"Average generator power in last rotation: {np.mean(power_gen_last_rotation):.2f} W")
    print(f"Average shaft speed in last rotation: {np.mean(omega_last_rotation):.2f} rad/s")
    print(f"Average pitch in last rotation: {np.mean(pitch_last_rotation):.2f} degrees")
    
    

    #%% PLOTS
    # plot_flexible(t,
    #               [[cp_rotor],
    #                [mech_out_rotor, power_gen],
    #                [omega],
    #                [pitch]
    #                ],
    #                [[r"$C_p$"],
    #                 ["rotor power", "generator power"],
    #                 [r"$\omega$"],
    #                 [r"$\theta_p$"]
    #                 ],
    #                 "Time (s)",
    #                ["Rotor $C_p$ [-]",
    #                 "Mechanical Power (W)",
    #                 "Shaft Speed (rad/s)",
    #                 "Pitch Angle (degrees)"]
    #                 ,save_name=f"cp_{V_hub}_",
    #                 shear_exp=shear_exp
    # )
    
if do["2_1_loop"]:
    V_hub_vals = np.linspace(4,25,100)
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.15
    yaw = 0
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt, pitch_init = [0, 0, 0])
        
    # Wind parameters
    shear_exp = 0.2
    TI = 0

    # Tower parameters
    tower_effects = True

    # Aero parameters
    use_dyn_wake=True
    use_dyn_stall=True
    use_wake_effects = "geometrical"

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 500
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")
        # CONTROLLER INITIALISATION
    use_controller=True
    controller = Controller.create(use_controller=use_controller) 
    # df_results = pd.DataFrame(columns=["V_hub", "cp_rotor", "mech_out_rotor", "power_gen", "omega", "pitch"])
    results_rows = []


    print(V_hub_vals)
    for V_hub in V_hub_vals:

        # WIND INITIALISATION
        wind_profile = ConfiguredWind(
                hub_height=structure.hub_height,
                v_hub=V_hub,
                shear_exp=shear_exp,
                tower_radius=structure.tower_radius if tower_effects else None,
                TI=TI,
            )
            
        # AERO INITIALISATION
        aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall, use_wake_effects=use_wake_effects)
        #%% RECORDERS    
        recorders = []
        recorders.append(cp_rotor_recorder(name=f"cp_rotor_{V_hub}"))
        recorders.append(mech_rotor_recorder(name=f"mech_out_rotor_{V_hub}"))
        recorders.append(generator_out_recorder(name=f"generator_out_{V_hub}"))
        recorders.append(omega_recorder(name=f"omega_{V_hub}"))
        recorders.append(pitch_recorder(name=f"pitch_{V_hub}", blade_idx=0))
        #%% Set up simulation, run, and save wind recorder data1
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

        simulation = Simulation(structure, aero, wind=wind_profile, controller=controller, recorders=recorders)
        simulation.run(dt, T)
        print("\nSimulation complete. Saving data...\n")
        simulation.save_recorders("sim_data", overwrite=True)

        #%% EXTRACT DATA FROM RECORDERS
        # Get data (saving above not needed for this) for plotting
        data = simulation.get_recorders()
        azimuth = data["time"] * omega_init / (2 * np.pi) * 360
        t = data["time"]

        cp_rotor = data[f"cp_rotor_{V_hub}"]["cp_rotor"]
        mech_out_rotor = data[f"mech_out_rotor_{V_hub}"]["power"]
        power_gen = data[f"generator_out_{V_hub}"]["power_gen"]
        omega = data[f"omega_{V_hub}"]["omega"]
        pitch = data[f"pitch_{V_hub}"]["pitch"]

        # save the average value for the last rotation of each parameter
        last_rotation_mask = azimuth >= (360 * (N-1))
        results_rows.append({
            "V_hub": V_hub,
            "cp_rotor": np.mean(cp_rotor[last_rotation_mask]),
            "mech_out_rotor": np.mean(mech_out_rotor[last_rotation_mask]),
            "power_gen": np.mean(power_gen[last_rotation_mask]),
            "omega": np.mean(omega[last_rotation_mask]),
            "pitch": np.mean(pitch[last_rotation_mask])
        })
    
    # print df_results in latex table format
    df_results = pd.DataFrame(results_rows)

    # save results to csv
    df_results.to_csv("cp_2_1_results.csv", index=False)

    # print df_results in latex table format
    print_latex_table(df_results)

if do["2_1_plots"]:
    df_results = pd.read_csv("cp_2_1_results.csv")
    V_hub = df_results["V_hub"].to_numpy()
    cp_rotor = df_results["cp_rotor"].to_numpy()
    mech_out_rotor = df_results["mech_out_rotor"].to_numpy()/1e6
    power_gen = df_results["power_gen"].to_numpy()/1e6
    omega = df_results["omega"].to_numpy()
    pitch = df_results["pitch"].to_numpy()
    shear_exp = 0.2
    max_cp = 0.466
    rated_power = 10.64
    omega_rated = 9.6*np.pi/30
    
    v_ref = [(4, "cut-in"), (11.4, "rated"), (25, "cut-out")]

    plot_flexible(
        V_hub,
        [[cp_rotor], [mech_out_rotor, power_gen], [omega], [pitch]],
        [[r"$C_p$"], ["rotor power", "generator power"], [r"$\omega$"], [r"$\theta_p$"]],
        "V hub (m/s)",
        ["Rotor $C_p$ [-]", "Mechanical Power (MW)", "Shaft Speed (rad/s)", "Pitch Angle (degrees)"],
        save_name="cp_power_omega_pitch_vs_V_hub",
        hlines=[
            [(max_cp, r"$C_{p,\max}$")],
            [(rated_power, "rated power", {"color": "r", "linestyle": ":"})],
            [(omega_rated, r"$\omega_{rated}$", {"color": "b"})],
            [],
        ],
        vlines=[v_ref, v_ref, v_ref, v_ref],
        shear_exp=shear_exp,
    )

    # plot_flexible(
    #     x_val = V_hub,
    #     y_values=[
    #         [cp_rotor],
    #         [mech_out_rotor, power_gen],
    #      [omega],
    #      [pitch]
    #      ],
    #     labels=[
    #     [r"$C_p$"],
    #     ["rotor power", "generator power"],
    #     [r"$\omega$"],
    #     [r"$\theta_p$"]
    #     ],
    #     x_label=
    #     "V hub (m/s)",
    #     y_units=
    #     ["Rotor $C_p$ [-]",
    #      "Mechanical Power (W)",
    #      "Shaft Speed (rad/s)",
    #      "Pitch Angle (degrees)"]
    #     ,save_name=f"cp_power_omega_pitch_vs_V_hub",
    #     hlines=[
    #         [(max_cp, r"$C_{p,\max}$")],
    #         [(rated_power, "rated power", {"color": "r", "linestyle": ":"})],
    #         [(omega_rated, r"$\omega_{rated}$", {"color": "b"})],
    #         []
    #         ],
    #     vlines=[
    #         [(3, "cut-in"), (15, "rated"), (25, "cut-out")],  # subplot 1
    #         [(3, "cut-in"), (15, "rated"), (25, "cut-out")],  # subplot 2
    #         [(3, "cut-in"), (15, "rated"), (25, "cut-out")],  # subplot 3
    #         [(3, "cut-in"), (15, "rated"), (25, "cut-out")]   # subplot 4
    #         ],
    #     shear_exp=shear_exp
    # )

if do["2_1_plots_compare_10mw"]:
    df_results = pd.read_csv("cp_2_1_results.csv")
    V_hub = df_results["V_hub"].to_numpy()
    cp_rotor = df_results["cp_rotor"].to_numpy()
    mech_out_rotor = df_results["mech_out_rotor"].to_numpy()/1e6
    power_gen = df_results["power_gen"].to_numpy()/1e6
    omega = df_results["omega"].to_numpy()
    pitch = df_results["pitch"].to_numpy()
    shear_exp = 0.2
    max_cp = 0.466
    rated_power = 10.64
    omega_rated = 9.6*np.pi/30
    
    #10 mw data
    ws_10 = df_power_bem["Windspeed [m/s]"].to_numpy()
    pitch_10 = df_stiff_pitch["Pitch [deg.]"].to_numpy()
    rpm_10 = df_stiff_pitch["RPM"].to_numpy()
    omega_10 = rpm_10 * np.pi / 30
    
    ws_turb = df_power_turb["Windspeed [m/s]"].to_numpy()
    power_turb = df_power_turb["Mech. Power [kW]"].to_numpy()
    cp_turb = df_power_turb["CP [-]"].to_numpy()
    
    v_ref = [(4, "cut-in"), (11.4, "rated"), (25, "cut-out")]

    plot_flexible(
        V_hub,
        [[cp_rotor], [mech_out_rotor, power_gen], [omega], [pitch]],
        [[r"$C_p$"], ["rotor power", "generator power"], [r"$\omega$"], [r"$\theta_p$"]],
        "V hub (m/s)",
        ["Rotor $C_p$ [-]", "Mechanical Power (MW)", "Shaft Speed (rad/s)", "Pitch Angle (degrees)"],
        save_name="cp_power_omega_pitch_vs_V_hub",
        hlines=[
            [(max_cp, r"$C_{p,\max}$")],
            [(rated_power, "rated power", {"color": "r", "linestyle": ":"})],
            [(omega_rated, r"$\omega_{rated}$", {"color": "b"})],
            [],
        ],
        vlines=[v_ref, v_ref, v_ref, v_ref],
        shear_exp=shear_exp,
    )

if do["2_2_turb_loop"]:
    V_hub_vals = np.linspace(1,25,100)
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.15
    yaw = 0
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt, pitch_init = [0, 0, 0])
        
    # Wind parameters
    shear_exp = 0.2
    TI = 0.1

    # Tower parameters
    tower_effects = True

    # Aero parameters
    use_dyn_wake=True
    use_dyn_stall=True
    use_wake_effects = "geometrical"

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 500
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")
        # CONTROLLER INITIALISATION
    use_controller=True
    controller = Controller.create(use_controller=use_controller) 
    # df_results = pd.DataFrame(columns=["V_hub", "cp_rotor", "mech_out_rotor", "power_gen", "omega", "pitch"])
    results_rows = []


    print(V_hub_vals)
    for V_hub in V_hub_vals:

        # WIND INITIALISATION
        wind_profile = ConfiguredWind(
                hub_height=structure.hub_height,
                v_hub=V_hub,
                shear_exp=shear_exp,
                tower_radius=structure.tower_radius if tower_effects else None,
                TI=TI,
            )
            
        # AERO INITIALISATION
        aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall, use_wake_effects=use_wake_effects)
        #%% RECORDERS    
        recorders = []
        recorders.append(cp_rotor_recorder(name=f"cp_rotor_{V_hub}"))
        recorders.append(mech_rotor_recorder(name=f"mech_out_rotor_{V_hub}"))
        recorders.append(generator_out_recorder(name=f"generator_out_{V_hub}"))
        recorders.append(omega_recorder(name=f"omega_{V_hub}"))
        recorders.append(pitch_recorder(name=f"pitch_{V_hub}", blade_idx=0))
        #%% Set up simulation, run, and save wind recorder data1
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

        simulation = Simulation(structure, aero, wind=wind_profile, controller=controller, recorders=recorders)
        simulation.run(dt, T)
        print("\nSimulation complete. Saving data...\n")
        simulation.save_recorders("sim_data", overwrite=True)

        #%% EXTRACT DATA FROM RECORDERS
        # Get data (saving above not needed for this) for plotting
        data = simulation.get_recorders()
        azimuth = data["time"] * omega_init / (2 * np.pi) * 360
        t = data["time"]

        cp_rotor = data[f"cp_rotor_{V_hub}"]["cp_rotor"]
        mech_out_rotor = data[f"mech_out_rotor_{V_hub}"]["power"]
        power_gen = data[f"generator_out_{V_hub}"]["power_gen"]
        omega = data[f"omega_{V_hub}"]["omega"]
        pitch = data[f"pitch_{V_hub}"]["pitch"]

        # save the average value for the last rotation of each parameter
        last_rotation_mask = azimuth >= (360 * (N-1))
        results_rows.append({
            "V_hub": V_hub,
            "cp_rotor": np.mean(cp_rotor[last_rotation_mask]),
            "mech_out_rotor": np.mean(mech_out_rotor[last_rotation_mask]),
            "power_gen": np.mean(power_gen[last_rotation_mask]),
            "omega": np.mean(omega[last_rotation_mask]),
            "pitch": np.mean(pitch[last_rotation_mask])
        })
    
    # print df_results in latex table format
    df_results = pd.DataFrame(results_rows)

    # save results to csv
    df_results.to_csv("cp_2_2_turb_results.csv", index=False)

