from unittest import signals

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from recorder import (
    omega_recorder,
    pitch_recorder,
    blade_position_1_recorder,
    blade_velocity_5_recorder,
    time_recorder,
    wind_5_recorder,
    p_5_recorder,
    w_5_recorder,
    mech_out_bladewise_recorder,
    mech_out_rotor_recorder,
    generator_out_recorder,
    controller_recorder
)
from simulation import Simulation
from structure import RigidStructure
from wind import ConstantWind, ShearWind, WindWithTower, TurbWind
from aero import Aero
from plots import *
from controller import Controller

do = {
    "test": False,
    "ass_1_1": False,
    "ass_1_2": False,
    "ass_1_3_wake": False,
    "ass_1_3_no_wake": False,
    "plot_ass_1_3": False,
    "ass_1_4_no_tower": False,
    "ass_1_4_w_tower": False,
    "ass_1_4_no_turb_w_tower": False,
    "ass_1_4_plot_comparison": False,
    "ass_1_4_plot": False,
    "controller_test": False,
    "sec_yaw_20deg_geo": False,
    "sec_yaw_20deg_empirical": False,
    "sec_yaw_0deg": False,
    "sec_yaw_plot": True
}

if do["test"]:
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.72  
    yaw = 0
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt)

    # Wind parameters
    shear_exp = 0
    V_hub = 8
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
    TI = 0

    # Tower parameters
    tower_effects = True

    # Aero parameters
    use_dyn_wake=True
    use_dyn_stall=True

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 250
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    def pitch_schedule(t):
        if t < 100:
            return [0.0, 0.0, 0.0]
        elif t < 150:
            return [2.0, 2.0, 2.0]
        else:
            return [0.0, 0.0, 0.0]

    structure.pitch_schedule = pitch_schedule
    if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall)

    
    #%% RECORDERS
    
    r_65 = structure.r[8]
    print("index 9 corresponds to radius ", r_65)
    recorders = []
    # record spanwise loads for each blade element on blade 0
    for span_pos in range(len(structure.r)):
        p5_recorder = p_5_recorder(name=f"aero_{span_pos}", blade_idx=0, element_idx=span_pos)
        # wind5_recorder = wind_5_recorder(name=f"wind_5_{span_pos}", blade_idx=0, element_idx=span_pos)
        recorders.append(p5_recorder)
        # recorders.append(wind5_recorder)
    
    # record thrust, torque, and power for each blade
    for blade_idx in range(structure.n_blades):
        recorders.append(mech_out_recorder(name=f"mech_out_blade_{blade_idx}", blade_idx=blade_idx))
        recorders.append(w_5_recorder(name=f"w_5_blade_{blade_idx}", blade_idx=blade_idx, element_idx=8)) # induced wind 
    
    recorders.append(wind_5_recorder(name=f"wind_5", blade_idx=0, element_idx=8)) # wind velocity
    recorders.append(w_5_recorder(name=f"w_5", blade_idx=0, element_idx=8)) # induced wind
    
    #%% Set up simulation, run, and save wind recorder data
    print(f"\nRunning simulation with parameters:\n")
    print(f"omega = {omega_init:.2f} rad/s ")
    print(f"yaw = {yaw} degrees,")
    print(f"tilt = {tilt} degrees")
    print(f"shear_exp = {shear_exp}")
    print(f"V_hub={V_hub} m/s")
    print(f"use_dyn_wake = {use_dyn_wake}")
    print(f"use_dyn_stall = {use_dyn_stall}")
    print(f"tower_effects = {tower_effects}")

    simulation = Simulation(structure, aero, wind=wind_profile, recorders=recorders)
    simulation.run(dt, T)
    print("\nSimulation complete. Saving data...\n")
    simulation.save_recorders("sim_data", overwrite=True)

    #%% EXTRACT DATA FROM RECORDERS
    # Get data (saving above not needed for this) for plotting
    data = simulation.get_recorders()
    azimuth = data["time"] * omega_init / (2 * np.pi) * 360
    t = data["time"]
    
    # FREE WIND
    u = data["wind_5"]["u"]
    v = data["wind_5"]["v"]
    w = data["wind_5"]["w"]

    # plot_1_value_time_2subplots(t, u, w,
    #                             "V_u", "V_w",
    #                             "m/s", "m/s",
    #                             "Wind_velocity_components_at_r_65m",
    #                             shear_exp,
    #                             turb=TI)

    

    
    # induced wind
    wy_5 = data["w_5"]["w_y"]
    wz_5 = data["w_5"]["w_z"]

    

    # aerodynamic loads
    py_5_8 = data["aero_8"]["p_y"]
    pz_5_8 = data["aero_8"]["p_z"]

    # wind velocity
    v_u = data["wind_5"]["u"]
    v_v = data["wind_5"]["v"]
    v_w = data["wind_5"]["w"]

    
    print(f"mean of v_w: {np.mean(v_w)}")
    # get the average py over one revolution for element 10 for the last revolution
    revolution_time = 2 * np.pi / omega_init
    total_time = data["time"][-1]
    last_revolution_time = total_time - revolution_time
    last_revolution_indices = np.where((data["time"] >= last_revolution_time) & (data["time"] <= total_time))[0]

    load_data = {
        qty: np.array([data[f"aero_{i}"][qty] for i in range(len(structure.r))])
        for qty in ["p_y", "p_z"]
    }

    # store the average py and pz for all blade elements over the last revolution in an array
    py_avg = np.array([np.mean(load_data["p_y"][i][last_revolution_indices]) for i in range(len(structure.r))])
    pz_avg = np.array([np.mean(load_data["p_z"][i][last_revolution_indices]) for i in range(len(structure.r))])

    blade_data = {
        qty: np.array([data[f"mech_out_blade_{i}"][qty] for i in range(structure.n_blades)])
        for qty in ["thrust", "torque", "power"]
    }

    induced_velocities = {
        qty: np.array([data[f"w_5_blade_{i}"][qty] for i in range(structure.n_blades)])
        for qty in ["w_y", "w_z"]
    }

    # wind_speeds = {
    #     qty: np.array([data[f"wind_5_blade_{i}"][qty] for i in range(structure.n_blades)])
    #     for qty in ["u", "v", "w"]
    # }

    # timeseries uvw
    


    # blade_data["thrust"] has shape (n_blades, n_steps)
    # blade_data["thrust"][0] is thrust for blade 0, etc.

    total_thrust = blade_data["thrust"].sum(axis=0)
    total_torque = blade_data["torque"].sum(axis=0)
    total_power  = blade_data["power"].sum(axis=0)



    # normalize data to compare across dimensions
    total_thrust_normalized = total_thrust / np.max(np.abs(total_thrust))
    print(f" max total thrust: {np.max(np.abs(total_thrust))}")
    total_torque_normalized = total_torque / np.max(np.abs(total_torque))
    total_power_normalized = total_power / 10e6

    # compute average total power with the last revolution
    avg_power = np.mean(total_power[last_revolution_indices])
    print(f"Average power for each blade over the last revolution: {avg_power:.3e} W")
    avg_thrust = np.mean(total_thrust[last_revolution_indices])
    print(f"Average thrust for each blade over the last revolution: {avg_thrust:.3e} N")

    py_avg_normalized = py_avg / np.max(np.abs(py_avg))
    pz_avg_normalized = pz_avg / np.max(np.abs(pz_avg))


    # load data from steady bem code located in data folder (csv file)
    df_stdy_bem = pd.read_csv("data/BEM_46310.csv")
    stdy_py = df_stdy_bem["p_t_torque"].values
    stdy_pz = df_stdy_bem["p_n_thrust"].values

    print("\n")

    #%% PLOTTING
    

    # plot total thrust and power and bladewise thrust and power
    plot_flexible(azimuth,
                    y_values=[
                    [total_thrust/1e3,
                     blade_data["thrust"][0]/1e3,
                     blade_data["thrust"][1]/1e3,
                     blade_data["thrust"][2]/1e3],
                    [total_power/1e6,
                      blade_data["power"][0]/1e6,
                      blade_data["power"][1]/1e6,
                      blade_data["power"][2]/1e6],
                    ],
                  labels=[
                    ["Total Thrust", "Blade 0", "Blade 1", "Blade 2"],
                    ["Total Power",  "Blade 0", "Blade 1", "Blade 2"],
                    ],
                  x_label="Azimuth Position [deg]",
                  y_units=["Thrust [kN]", "Power [MW]"],
                  save_name="total_bladewise_thrust_power",
                  shear_exp=shear_exp,
                  xlims=[1000,3000])

    # plot py and pz avg over blade span position
    plot_flexible(structure.r, 
                  y_values=[[py_avg, pz_avg]],
                  labels=[["Tangential", "Normal"]],
                  x_label="Blade Span Position (r) [m]",
                  y_units=["[N/m]"],
                  save_name="spanwise_load_distributions",
                  shear_exp=shear_exp,
                  fig_size=16)
    # Plot uvw vs time at r=65m
    # plot_flexible(t,
    #                 [v_u, v_v, v_w],
    #                 ["u", "v", "w"],
    #                 "Time [s]", ["m/s", "m/s", "m/s"],
    #                 "Wind_velocity_components_at_r_65m_time_series",
    #                 3,1,
    #                 shear_exp,
    #                 turb=TI)

if do["ass_1_1"]:
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.72  
    yaw = 0
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt)

    # Wind parameters
    shear_exp = 0
    V_hub = 8
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
    TI = 0

    # Tower parameters
    tower_effects = True

    # Aero parameters
    use_dyn_wake=True
    use_dyn_stall=True

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 250
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    def pitch_schedule(t):
        if t < 100:
            return [0.0, 0.0, 0.0]
        elif t < 150:
            return [2.0, 2.0, 2.0]
        else:
            return [0.0, 0.0, 0.0]

    structure.pitch_schedule = pitch_schedule
    if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall)

    
    #%% RECORDERS
    
    r_65 = structure.r[8]
    print("index 9 corresponds to radius ", r_65)
    recorders = []
    # record spanwise loads for each blade element on blade 0
    for span_pos in range(len(structure.r)):
        p5_recorder = p_5_recorder(name=f"aero_{span_pos}", blade_idx=0, element_idx=span_pos)
        # wind5_recorder = wind_5_recorder(name=f"wind_5_{span_pos}", blade_idx=0, element_idx=span_pos)
        recorders.append(p5_recorder)
        # recorders.append(wind5_recorder)
    
    # record thrust, torque, and power for each blade
    for blade_idx in range(structure.n_blades):
        recorders.append(mech_out_recorder(name=f"mech_out_blade_{blade_idx}", blade_idx=blade_idx))
        recorders.append(w_5_recorder(name=f"w_5_blade_{blade_idx}", blade_idx=blade_idx, element_idx=8)) # induced wind 
    
    recorders.append(wind_5_recorder(name=f"wind_5", blade_idx=0, element_idx=8)) # wind velocity
    recorders.append(w_5_recorder(name=f"w_5", blade_idx=0, element_idx=8)) # induced wind
    
    #%% Set up simulation, run, and save wind recorder data
    print(f"\nRunning simulation with parameters:\n")
    print(f"omega = {omega_init:.2f} rad/s ")
    print(f"yaw = {yaw} degrees,")
    print(f"tilt = {tilt} degrees")
    print(f"shear_exp = {shear_exp}")
    print(f"V_hub={V_hub} m/s")
    print(f"use_dyn_wake = {use_dyn_wake}")
    print(f"use_dyn_stall = {use_dyn_stall}")
    print(f"tower_effects = {tower_effects}")

    simulation = Simulation(structure, aero, wind=wind_profile, recorders=recorders)
    simulation.run(dt, T)
    print("\nSimulation complete. Saving data...\n")
    simulation.save_recorders("sim_data", overwrite=True)

    #%% EXTRACT DATA FROM RECORDERS
    # Get data (saving above not needed for this) for plotting
    data = simulation.get_recorders()
    azimuth = data["time"] * omega_init / (2 * np.pi) * 360
    t = data["time"]
    
    # FREE WIND
    u = data["wind_5"]["u"]
    v = data["wind_5"]["v"]
    w = data["wind_5"]["w"]

    # plot_1_value_time_2subplots(t, u, w,
    #                             "V_u", "V_w",
    #                             "m/s", "m/s",
    #                             "Wind_velocity_components_at_r_65m",
    #                             shear_exp,
    #                             turb=TI)

    

    
    # induced wind
    wy_5 = data["w_5"]["w_y"]
    wz_5 = data["w_5"]["w_z"]

    

    # aerodynamic loads
    py_5_8 = data["aero_8"]["p_y"]
    pz_5_8 = data["aero_8"]["p_z"]

    # wind velocity
    v_u = data["wind_5"]["u"]
    v_v = data["wind_5"]["v"]
    v_w = data["wind_5"]["w"]

    
    print(f"mean of v_w: {np.mean(v_w)}")
    # get the average py over one revolution for element 10 for the last revolution
    revolution_time = 2 * np.pi / omega_init
    total_time = data["time"][-1]
    last_revolution_time = total_time - revolution_time
    last_revolution_indices = np.where((data["time"] >= last_revolution_time) & (data["time"] <= total_time))[0]

    load_data = {
        qty: np.array([data[f"aero_{i}"][qty] for i in range(len(structure.r))])
        for qty in ["p_y", "p_z"]
    }

    # store the average py and pz for all blade elements over the last revolution in an array
    py_avg = np.array([np.mean(load_data["p_y"][i][last_revolution_indices]) for i in range(len(structure.r))])
    pz_avg = np.array([np.mean(load_data["p_z"][i][last_revolution_indices]) for i in range(len(structure.r))])

    blade_data = {
        qty: np.array([data[f"mech_out_blade_{i}"][qty] for i in range(structure.n_blades)])
        for qty in ["thrust", "torque", "power"]
    }

    induced_velocities = {
        qty: np.array([data[f"w_5_blade_{i}"][qty] for i in range(structure.n_blades)])
        for qty in ["w_y", "w_z"]
    }

    # wind_speeds = {
    #     qty: np.array([data[f"wind_5_blade_{i}"][qty] for i in range(structure.n_blades)])
    #     for qty in ["u", "v", "w"]
    # }

    # timeseries uvw
    


    # blade_data["thrust"] has shape (n_blades, n_steps)
    # blade_data["thrust"][0] is thrust for blade 0, etc.

    total_thrust = blade_data["thrust"].sum(axis=0)
    total_torque = blade_data["torque"].sum(axis=0)
    total_power  = blade_data["power"].sum(axis=0)



    # normalize data to compare across dimensions
    total_thrust_normalized = total_thrust / np.max(np.abs(total_thrust))
    print(f" max total thrust: {np.max(np.abs(total_thrust))}")
    total_torque_normalized = total_torque / np.max(np.abs(total_torque))
    total_power_normalized = total_power / 10e6

    # compute average total power with the last revolution
    avg_power = np.mean(total_power[last_revolution_indices])
    print(f"Average power for each blade over the last revolution: {avg_power:.3e} W")
    avg_thrust = np.mean(total_thrust[last_revolution_indices])
    print(f"Average thrust for each blade over the last revolution: {avg_thrust:.3e} N")

    py_avg_normalized = py_avg / np.max(np.abs(py_avg))
    pz_avg_normalized = pz_avg / np.max(np.abs(pz_avg))


    # load data from steady bem code located in data folder (csv file)
    df_stdy_bem = pd.read_csv("data/BEM_46310.csv")
    stdy_py = df_stdy_bem["p_t_torque"].values
    stdy_pz = df_stdy_bem["p_n_thrust"].values

    print("\n")

    #%% PLOTTING
    from ashes_data import ashes_normal, ashes_tangential, r_ashes

    hub_radius = 2.8

    ashes_normal_interp = np.interp(structure.r-hub_radius, r_ashes, ashes_normal)
    ashes_tangential_interp = np.interp(structure.r-hub_radius, r_ashes, ashes_tangential)

    # interpolate steady BEM onto structure.r
    stdy_r  = df_stdy_bem["span_position_r"].values  # <-- load the radial positions from the CSV
    stdy_py_interp = np.interp(structure.r, stdy_r, stdy_py)
    stdy_pz_interp = np.interp(structure.r, stdy_r, stdy_pz)



    plot_flexible(structure.r,
                  y_values=[[py_avg, stdy_py_interp, ashes_tangential_interp], 
                            [pz_avg, stdy_pz_interp, ashes_normal_interp]],
                  labels=[["Unsteady", "Steady", "ASHES"],
                          ["Unsteady", "Steady", "ASHES"]],
                  x_label="Blade Span Position (r) [m]",
                  y_units=["Tangential [N/m]", "Normal [N/m]"],
                  save_name="spanwise_load_comparison_with_ashes",
                    shear_exp=shear_exp)

    # plot total thrust and power and bladewise thrust and power
    plot_flexible(azimuth,
                    y_values=[
                    [total_thrust/1e3,
                     blade_data["thrust"][0]/1e3,
                     blade_data["thrust"][1]/1e3,
                     blade_data["thrust"][2]/1e3],
                    [total_power/1e6,
                      blade_data["power"][0]/1e6,
                      blade_data["power"][1]/1e6,
                      blade_data["power"][2]/1e6],
                    ],
                  labels=[
                    ["Total Thrust", "Blade 0", "Blade 1", "Blade 2"],
                    ["Total Power",  "Blade 0", "Blade 1", "Blade 2"],
                    ],
                  x_label="Azimuth Position [deg]",
                  y_units=["Thrust [kN]", "Power [MW]"],
                  save_name="total_bladewise_thrust_power",
                  shear_exp=shear_exp,
                  xlims=[1000,3000])

    # plot py and pz avg over blade span position
    plot_flexible(structure.r, 
                  y_values=[[py_avg, pz_avg]],
                  labels=[["Tangential", "Normal"]],
                  x_label="Blade Span Position (r) [m]",
                  y_units=["[N/m]"],
                  save_name="spanwise_load_distributions",
                  shear_exp=shear_exp,
                  fig_size=16)
    # Plot uvw vs time at r=65m
    # plot_flexible(t,
    #                 [v_u, v_v, v_w],
    #                 ["u", "v", "w"],
    #                 "Time [s]", ["m/s", "m/s", "m/s"],
    #                 "Wind_velocity_components_at_r_65m_time_series",
    #                 3,1,
    #                 shear_exp,
    #                 turb=TI)
    

if do["ass_1_2"]:
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.72  
    yaw = 0
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt)

    # Wind parameters
    shear_exp = 0.2
    V_hub = 8
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
    TI = 0

    # Tower parameters
    tower_effects = True

    # Aero parameters
    use_dyn_wake=True
    use_dyn_stall=True

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 130
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    def pitch_schedule(t):
        if t < 100:
            return [0.0, 0.0, 0.0]
        elif t < 150:
            return [2.0, 2.0, 2.0]
        else:
            return [0.0, 0.0, 0.0]

    structure.pitch_schedule = pitch_schedule
    if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall)

    
    #%% RECORDERS
    
    r_65 = structure.r[8]
    print("index 9 corresponds to radius ", r_65)
    recorders = []
    # record spanwise loads for each blade element on blade 0
    for span_pos in range(len(structure.r)):
        p5_recorder = p_5_recorder(name=f"aero_{span_pos}", blade_idx=0, element_idx=span_pos)
        # wind5_recorder = wind_5_recorder(name=f"wind_5_{span_pos}", blade_idx=0, element_idx=span_pos)
        recorders.append(p5_recorder)
        # recorders.append(wind5_recorder)
    
    # record thrust, torque, and power for each blade
    for blade_idx in range(structure.n_blades):
        recorders.append(mech_out_recorder(name=f"mech_out_blade_{blade_idx}", blade_idx=blade_idx))
        recorders.append(w_5_recorder(name=f"w_5_blade_{blade_idx}", blade_idx=blade_idx, element_idx=8)) # induced wind 
    
    recorders.append(wind_5_recorder(name=f"wind_5", blade_idx=0, element_idx=8)) # wind velocity
    recorders.append(w_5_recorder(name=f"w_5", blade_idx=0, element_idx=8)) # induced wind
    
    #%% Set up simulation, run, and save wind recorder data
    print(f"\nRunning simulation with parameters:\n")
    print(f"omega = {omega_init:.2f} rad/s ")
    print(f"yaw = {yaw} degrees,")
    print(f"tilt = {tilt} degrees")
    print(f"shear_exp = {shear_exp}")
    print(f"V_hub={V_hub} m/s")
    print(f"use_dyn_wake = {use_dyn_wake}")
    print(f"use_dyn_stall = {use_dyn_stall}")
    print(f"tower_effects = {tower_effects}")

    simulation = Simulation(structure, aero, wind=wind_profile, recorders=recorders)
    simulation.run(dt, T)
    print("\nSimulation complete. Saving data...\n")
    simulation.save_recorders("sim_data", overwrite=True)

    #%% EXTRACT DATA FROM RECORDERS
    # Get data (saving above not needed for this) for plotting
    data = simulation.get_recorders()
    azimuth = data["time"] * omega_init / (2 * np.pi) * 360
    t = data["time"]
    
    # FREE WIND
    u = data["wind_5"]["u"]
    v = data["wind_5"]["v"]
    w = data["wind_5"]["w"]

    # plot_1_value_time_2subplots(t, u, w,
    #                             "V_u", "V_w",
    #                             "m/s", "m/s",
    #                             "Wind_velocity_components_at_r_65m",
    #                             shear_exp,
    #                             turb=TI)

    

    
    # induced wind
    wy_5 = data["w_5"]["w_y"]
    wz_5 = data["w_5"]["w_z"]

    

    # aerodynamic loads
    py_5_8 = data["aero_8"]["p_y"]
    pz_5_8 = data["aero_8"]["p_z"]

    # wind velocity
    v_u = data["wind_5"]["u"]
    v_v = data["wind_5"]["v"]
    v_w = data["wind_5"]["w"]

    
    print(f"mean of v_w: {np.mean(v_w)}")
    # get the average py over one revolution for element 10 for the last revolution
    revolution_time = 2 * np.pi / omega_init
    total_time = data["time"][-1]
    last_revolution_time = total_time - revolution_time
    last_revolution_indices = np.where((data["time"] >= last_revolution_time) & (data["time"] <= total_time))[0]

    load_data = {
        qty: np.array([data[f"aero_{i}"][qty] for i in range(len(structure.r))])
        for qty in ["p_y", "p_z"]
    }

    # store the average py and pz for all blade elements over the last revolution in an array
    py_avg = np.array([np.mean(load_data["p_y"][i][last_revolution_indices]) for i in range(len(structure.r))])
    pz_avg = np.array([np.mean(load_data["p_z"][i][last_revolution_indices]) for i in range(len(structure.r))])

    blade_data = {
        qty: np.array([data[f"mech_out_blade_{i}"][qty] for i in range(structure.n_blades)])
        for qty in ["thrust", "torque", "power"]
    }

    induced_velocities = {
        qty: np.array([data[f"w_5_blade_{i}"][qty] for i in range(structure.n_blades)])
        for qty in ["w_y", "w_z"]
    }

    # wind_speeds = {
    #     qty: np.array([data[f"wind_5_blade_{i}"][qty] for i in range(structure.n_blades)])
    #     for qty in ["u", "v", "w"]
    # }

    # timeseries uvw
    


    # blade_data["thrust"] has shape (n_blades, n_steps)
    # blade_data["thrust"][0] is thrust for blade 0, etc.

    total_thrust = blade_data["thrust"].sum(axis=0)
    total_torque = blade_data["torque"].sum(axis=0)
    total_power  = blade_data["power"].sum(axis=0)



    # normalize data to compare across dimensions
    total_thrust_normalized = total_thrust / np.max(np.abs(total_thrust))
    print(f" max total thrust: {np.max(np.abs(total_thrust))}")
    total_torque_normalized = total_torque / np.max(np.abs(total_torque))
    total_power_normalized = total_power / 10e6

    # compute average total power with the last revolution
    avg_power = np.mean(total_power[last_revolution_indices])
    print(f"Average power for each blade over the last revolution: {avg_power:.3e} W")
    avg_thrust = np.mean(total_thrust[last_revolution_indices])
    print(f"Average thrust for each blade over the last revolution: {avg_thrust:.3e} N")

    py_avg_normalized = py_avg / np.max(np.abs(py_avg))
    pz_avg_normalized = pz_avg / np.max(np.abs(pz_avg))


    # load data from steady bem code located in data folder (csv file)
    df_stdy_bem = pd.read_csv("data/BEM_46310.csv")
    stdy_py = df_stdy_bem["p_t_torque"].values
    stdy_pz = df_stdy_bem["p_n_thrust"].values

    print("\n")

    #%% PLOTTING

    # plot total thrust and power and bladewise thrust and power
    plot_flexible(azimuth,
                    y_values=[
                    [total_thrust/1e3,
                     blade_data["thrust"][0]/1e3,
                     blade_data["thrust"][1]/1e3,
                     blade_data["thrust"][2]/1e3],
                    [total_power/1e6,
                     blade_data["power"][0]/1e6,
                     blade_data["power"][1]/1e6,
                     blade_data["power"][2]/1e6],
                    ],
                  labels=[
                      ["Total Thrust", "Blade 0", "Blade 1", "Blade 2"],
                      ["Total Power",  "Blade 0", "Blade 1", "Blade 2"],
                    ],
                  x_label="Azimuth Position [deg]",
                  y_units=["Thrust [kN]", "Power [MW]"],
                  save_name="total_bladewise_thrust_power",
                  shear_exp=shear_exp,
                  xlims=[1000,3000],
                  ylims=[[150,900], [0, 4.5]])

if do["ass_1_3_wake"]:
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.72  
    yaw = 0
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt)

    # Wind parameters
    shear_exp = 0
    V_hub = 8
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
    TI = 0

    # Tower parameters
    tower_effects = False

    # Aero parameters
    use_dyn_wake=True
    use_dyn_stall=True

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 250
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    def pitch_schedule(t):
        if t < 100:
            return [0.0, 0.0, 0.0]
        elif t < 150:
            return [2.0, 2.0, 2.0]
        else:
            return [0.0, 0.0, 0.0]

    structure.pitch_schedule = pitch_schedule
    if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall)

    
    #%% RECORDERS
    
    r_65 = structure.r[8]
    print("index 9 corresponds to radius ", r_65)
    recorders = []
    # record spanwise loads for each blade element on blade 0
    for span_pos in range(len(structure.r)):
        p5_recorder = p_5_recorder(name=f"aero_{span_pos}_{use_dyn_wake}", blade_idx=0, element_idx=span_pos)
        # wind5_recorder = wind_5_recorder(name=f"wind_5_{span_pos}", blade_idx=0, element_idx=span_pos)
        recorders.append(p5_recorder)
        # recorders.append(wind5_recorder)
    
    # record thrust, torque, and power for each blade
    for blade_idx in range(structure.n_blades):
        recorders.append(mech_out_recorder(name=f"mech_out_blade_{blade_idx}_{use_dyn_wake}", blade_idx=blade_idx))
        recorders.append(w_5_recorder(name=f"w_5_blade_{blade_idx}_{use_dyn_wake}", blade_idx=blade_idx, element_idx=8)) # induced wind 
    
    recorders.append(wind_5_recorder(name=f"wind_5_{use_dyn_wake}", blade_idx=0, element_idx=8)) # wind velocity
    recorders.append(w_5_recorder(name=f"w_5_{use_dyn_wake}", blade_idx=0, element_idx=8)) # induced wind
    
    #%% Set up simulation, run, and save wind recorder data
    print(f"\nRunning simulation with parameters:\n")
    print(f"omega = {omega_init:.2f} rad/s ")
    print(f"yaw = {yaw} degrees,")
    print(f"tilt = {tilt} degrees")
    print(f"shear_exp = {shear_exp}")
    print(f"V_hub={V_hub} m/s")
    print(f"use_dyn_wake = {use_dyn_wake}")
    print(f"use_dyn_stall = {use_dyn_stall}")
    print(f"tower_effects = {tower_effects}")

    simulation = Simulation(structure, aero, wind=wind_profile, recorders=recorders)
    simulation.run(dt, T)
    print("\nSimulation complete. Saving data...\n")
    simulation.save_recorders("sim_data", overwrite=True)

    #%% EXTRACT DATA FROM RECORDERS
    # Get data (saving above not needed for this) for plotting
    data = simulation.get_recorders()
    azimuth = data["time"] * omega_init / (2 * np.pi) * 360
    t = data["time"]

    # induced wind
    wy_5 = data[f"w_5_{use_dyn_wake}"]["w_y"]
    wz_5 = data[f"w_5_{use_dyn_wake}"]["w_z"]

    

    # aerodynamic loads
    py_5_8 = data[f"aero_8_{use_dyn_wake}"]["p_y"]
    pz_5_8 = data[f"aero_8_{use_dyn_wake}"]["p_z"]

    # wind velocity
    v_u = data[f"wind_5_{use_dyn_wake}"]["u"]
    v_v = data[f"wind_5_{use_dyn_wake}"]["v"]
    v_w = data[f"wind_5_{use_dyn_wake}"]["w"]

    
    print(f"mean of v_w: {np.mean(v_w)}")
    # get the average py over one revolution for element 10 for the last revolution
    revolution_time = 2 * np.pi / omega_init
    total_time = data["time"][-1]
    last_revolution_time = total_time - revolution_time
    last_revolution_indices = np.where((data["time"] >= last_revolution_time) & (data["time"] <= total_time))[0]

    load_data = {
        qty: np.array([data[f"aero_{i}_{use_dyn_wake}"][qty] for i in range(len(structure.r))])
        for qty in ["p_y", "p_z"]
    }

    # store the average py and pz for all blade elements over the last revolution in an array
    py_avg = np.array([np.mean(load_data["p_y"][i][last_revolution_indices]) for i in range(len(structure.r))])
    pz_avg = np.array([np.mean(load_data["p_z"][i][last_revolution_indices]) for i in range(len(structure.r))])

    blade_data = {
        qty: np.array([data[f"mech_out_blade_{i}_{use_dyn_wake}"][qty] for i in range(structure.n_blades)])
        for qty in ["thrust", "torque", "power"]
    }

    induced_velocities = {
        qty: np.array([data[f"w_5_blade_{i}_{use_dyn_wake}"][qty] for i in range(structure.n_blades)])
        for qty in ["w_y", "w_z"]
    }

    total_thrust = blade_data["thrust"].sum(axis=0)
    total_torque = blade_data["torque"].sum(axis=0)
    total_power  = blade_data["power"].sum(axis=0)

    # normalize data to compare across dimensions
    total_thrust_normalized = total_thrust / np.max(np.abs(total_thrust))
    print(f" max total thrust: {np.max(np.abs(total_thrust))}")
    total_torque_normalized = total_torque / np.max(np.abs(total_torque))
    total_power_normalized = total_power / 10e6

    # compute average total power with the last revolution
    avg_power = np.mean(total_power[last_revolution_indices])
    print(f"Average power for each blade over the last revolution: {avg_power:.3e} W")
    avg_thrust = np.mean(total_thrust[last_revolution_indices])
    print(f"Average thrust for each blade over the last revolution: {avg_thrust:.3e} N")

    py_avg_normalized = py_avg / np.max(np.abs(py_avg))
    pz_avg_normalized = pz_avg / np.max(np.abs(pz_avg))


    # load data from steady bem code located in data folder (csv file)
    df_stdy_bem = pd.read_csv("data/BEM_46310.csv")
    stdy_py = df_stdy_bem["p_t_torque"].values
    stdy_pz = df_stdy_bem["p_n_thrust"].values

    print("\n")

    #%% PLOTTING

    # plot total thrust and power and bladewise thrust and power
    plot_flexible(t,
                    y_values=[
                        [wy_5],
                        [wz_5],
                        [blade_data["power"][0]/1e6],
                        [total_power/1e6],
                        [blade_data["thrust"][0]/1e3],
                        [total_thrust/1e3]],
                    labels=[
                        ["Induced Velocity w_y at r=65m"],
                        ["Induced Velocity w_z at r=65m"],
                        ["Blade 0 Power"],
                        ["Total Power"],
                        ["Blade 0 Thrust"],
                        ["Total Thrust"]],
                    x_label="Time [s]",
                    y_units=["[m/s]", "[m/s]",  "Power [MW]",  "Power [MW]", "Thrust [kN]", "Thrust [kN]"],
                    save_name="induced_power_thrust_total_bladewise",
                    shear_exp=shear_exp,
                    xlims=[50, 250],
                    ylims=[
                            [-0.27, -0.33],
                            [-2.3, -3.1],
                            [1.0, 1.6],
                            [2.8, 4.8],
                            [220, 320],
                            [600, 1000]
                        ])

    #%% SAVE PLOT DATA TO CSV
    df_plot = pd.DataFrame({
        "time":         t,
        "azimuth":      azimuth,
        "wy_5":         wy_5,
        "wz_5":         wz_5,
        "power_blade0": blade_data["power"][0],
        "power_blade1": blade_data["power"][1],
        "power_blade2": blade_data["power"][2],
        "power_total":  total_power,
        "thrust_blade0":blade_data["thrust"][0],
        "thrust_blade1":blade_data["thrust"][1],
        "thrust_blade2":blade_data["thrust"][2],
        "thrust_total": total_thrust,
        "torque_blade0":blade_data["torque"][0],
        "torque_blade1":blade_data["torque"][1],
        "torque_blade2":blade_data["torque"][2],
        "torque_total": total_torque,
        "v_u":          v_u,
        "v_v":          v_v,
        "v_w":          v_w,
    })
    csv_path = Path("sim_data") / f"plot_data_dyn_wake_{use_dyn_wake}_shear_{shear_exp}.csv"
    csv_path.parent.mkdir(exist_ok=True)
    df_plot.to_csv(csv_path, index=False)
    print(f"Plot data saved to {csv_path}")

    # save spanwise data separately (different length than time series)
    df_span = pd.DataFrame({
        "r":     structure.r,
        "py_avg": py_avg,
        "pz_avg": pz_avg,
    })
    span_csv_path = Path("sim_data") / f"spanwise_data_dyn_wake_{use_dyn_wake}_shear_{shear_exp}.csv"
    df_span.to_csv(span_csv_path, index=False)
    print(f"Spanwise data saved to {span_csv_path}")

    #[-0.27, -0.33],
                        #  [-2.3, -3.1],
                        #  [1.0, 1.6],
                        #  [2.8, 4.8],
                        #  [0.22, 0.32],
                        #  [0.6, 1.0],

    # plot py and pz avg over blade span position
    # # Plot uvw vs time at r=65m
    # plot_flexible(t,
    #                 [v_u, v_v, v_w],
    #                 ["u", "v", "w"],
    #                 "Time [s]", ["m/s", "m/s", "m/s"],
    #                 "Wind_velocity_components_at_r_65m_time_series",
    #                 3,1,
    #                 shear_exp,
    #                 turb=TI)
    
if do["ass_1_3_no_wake"]:
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.72  
    yaw = 0
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt)

    # Wind parameters
    shear_exp = 0
    V_hub = 8
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
    TI = 0

    # Tower parameters
    tower_effects = False

    # Aero parameters
    use_dyn_wake=False
    use_dyn_stall=True

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 250
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    def pitch_schedule(t):
        if t < 100:
            return [0.0, 0.0, 0.0]
        elif t < 150:
            return [2.0, 2.0, 2.0]
        else:
            return [0.0, 0.0, 0.0]

    structure.pitch_schedule = pitch_schedule
    if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall)

    
    #%% RECORDERS
    
    r_65 = structure.r[8]
    print("index 9 corresponds to radius ", r_65)
    recorders = []
    # record spanwise loads for each blade element on blade 0
    for span_pos in range(len(structure.r)):
        p5_recorder = p_5_recorder(name=f"aero_{span_pos}_{use_dyn_wake}", blade_idx=0, element_idx=span_pos)
        # wind5_recorder = wind_5_recorder(name=f"wind_5_{span_pos}", blade_idx=0, element_idx=span_pos)
        recorders.append(p5_recorder)
        # recorders.append(wind5_recorder)
    
    # record thrust, torque, and power for each blade
    for blade_idx in range(structure.n_blades):
        recorders.append(mech_out_recorder(name=f"mech_out_blade_{blade_idx}_{use_dyn_wake}", blade_idx=blade_idx))
        recorders.append(w_5_recorder(name=f"w_5_blade_{blade_idx}_{use_dyn_wake}", blade_idx=blade_idx, element_idx=8)) # induced wind 
    
    recorders.append(wind_5_recorder(name=f"wind_5_{use_dyn_wake}", blade_idx=0, element_idx=8)) # wind velocity
    recorders.append(w_5_recorder(name=f"w_5_{use_dyn_wake}", blade_idx=0, element_idx=8)) # induced wind
    
    #%% Set up simulation, run, and save wind recorder data
    print(f"\nRunning simulation with parameters:\n")
    print(f"omega = {omega_init:.2f} rad/s ")
    print(f"yaw = {yaw} degrees,")
    print(f"tilt = {tilt} degrees")
    print(f"shear_exp = {shear_exp}")
    print(f"V_hub={V_hub} m/s")
    print(f"use_dyn_wake = {use_dyn_wake}")
    print(f"use_dyn_stall = {use_dyn_stall}")
    print(f"tower_effects = {tower_effects}")

    simulation = Simulation(structure, aero, wind=wind_profile, recorders=recorders)
    simulation.run(dt, T)
    print("\nSimulation complete. Saving data...\n")
    simulation.save_recorders("sim_data", overwrite=True)

    #%% EXTRACT DATA FROM RECORDERS
    # Get data (saving above not needed for this) for plotting
    data = simulation.get_recorders()
    azimuth = data["time"] * omega_init / (2 * np.pi) * 360
    t = data["time"]

    # induced wind
    wy_5 = data[f"w_5_{use_dyn_wake}"]["w_y"]
    wz_5 = data[f"w_5_{use_dyn_wake}"]["w_z"]
    wy_qs_5 = data[f"w_5_{use_dyn_wake}"]["w_y_qs"]
    wz_qs_5 = data[f"w_5_{use_dyn_wake}"]["w_z_qs"]

    

    # aerodynamic loads
    py_5_8 = data[f"aero_8_{use_dyn_wake}"]["p_y"]
    pz_5_8 = data[f"aero_8_{use_dyn_wake}"]["p_z"]

    # wind velocity
    v_u = data[f"wind_5_{use_dyn_wake}"]["u"]
    v_v = data[f"wind_5_{use_dyn_wake}"]["v"]
    v_w = data[f"wind_5_{use_dyn_wake}"]["w"]

    
    print(f"mean of v_w: {np.mean(v_w)}")
    # get the average py over one revolution for element 10 for the last revolution
    revolution_time = 2 * np.pi / omega_init
    total_time = data["time"][-1]
    last_revolution_time = total_time - revolution_time
    last_revolution_indices = np.where((data["time"] >= last_revolution_time) & (data["time"] <= total_time))[0]

    load_data = {
        qty: np.array([data[f"aero_{i}_{use_dyn_wake}"][qty] for i in range(len(structure.r))])
        for qty in ["p_y", "p_z"]
    }

    # store the average py and pz for all blade elements over the last revolution in an array
    py_avg = np.array([np.mean(load_data["p_y"][i][last_revolution_indices]) for i in range(len(structure.r))])
    pz_avg = np.array([np.mean(load_data["p_z"][i][last_revolution_indices]) for i in range(len(structure.r))])

    blade_data = {
        qty: np.array([data[f"mech_out_blade_{i}_{use_dyn_wake}"][qty] for i in range(structure.n_blades)])
        for qty in ["thrust", "torque", "power"]
    }

    induced_velocities = {
        qty: np.array([data[f"w_5_blade_{i}_{use_dyn_wake}"][qty] for i in range(structure.n_blades)])
        for qty in ["w_y", "w_z", "w_y_qs", "w_z_qs"]
    }

    total_thrust = blade_data["thrust"].sum(axis=0)
    total_torque = blade_data["torque"].sum(axis=0)
    total_power  = blade_data["power"].sum(axis=0)

    # normalize data to compare across dimensions
    total_thrust_normalized = total_thrust / np.max(np.abs(total_thrust))
    print(f" max total thrust: {np.max(np.abs(total_thrust))}")
    total_torque_normalized = total_torque / np.max(np.abs(total_torque))
    total_power_normalized = total_power / 10e6

    # compute average total power with the last revolution
    avg_power = np.mean(total_power[last_revolution_indices])
    print(f"Average power for each blade over the last revolution: {avg_power:.3e} W")
    avg_thrust = np.mean(total_thrust[last_revolution_indices])
    print(f"Average thrust for each blade over the last revolution: {avg_thrust:.3e} N")

    py_avg_normalized = py_avg / np.max(np.abs(py_avg))
    pz_avg_normalized = pz_avg / np.max(np.abs(pz_avg))


    # load data from steady bem code located in data folder (csv file)
    df_stdy_bem = pd.read_csv("data/BEM_46310.csv")
    stdy_py = df_stdy_bem["p_t_torque"].values
    stdy_pz = df_stdy_bem["p_n_thrust"].values

    print("\n")

    #%% PLOTTING

    # plot total thrust and power and bladewise thrust and power
    plot_flexible(t,
                    y_values=[
                        [wy_qs_5],
                        [wz_qs_5],
                        [blade_data["power"][0]/1e6],
                        [total_power/1e6],
                        [blade_data["thrust"][0]/1e3],
                        [total_thrust/1e3]],
                    labels=[
                        ["Induced Velocity w_y at r=65m"],
                        ["Induced Velocity w_z at r=65m"],
                        ["Blade 0 Power"],
                        ["Total Power"],
                        ["Blade 0 Thrust"],
                        ["Total Thrust"]],
                    x_label="Time [s]",
                    y_units=["[m/s]", "[m/s]",  "Power [MW]",  "Power [MW]", "Thrust [kN]", "Thrust [kN]"],
                    save_name="induced_power_thrust_total_bladewise",
                    shear_exp=shear_exp,
                    xlims=[50, 250],
                    )

                        #%% SAVE PLOT DATA TO CSV
    df_plot = pd.DataFrame({
        "time":         t,
        "azimuth":      azimuth,
        "wy_5":         wy_qs_5,
        "wz_5":         wz_qs_5,
        "power_blade0": blade_data["power"][0],
        "power_blade1": blade_data["power"][1],
        "power_blade2": blade_data["power"][2],
        "power_total":  total_power,
        "thrust_blade0":blade_data["thrust"][0],
        "thrust_blade1":blade_data["thrust"][1],
        "thrust_blade2":blade_data["thrust"][2],
        "thrust_total": total_thrust,
        "torque_blade0":blade_data["torque"][0],
        "torque_blade1":blade_data["torque"][1],
        "torque_blade2":blade_data["torque"][2],
        "torque_total": total_torque,
        "v_u":          v_u,
        "v_v":          v_v,
        "v_w":          v_w,
    })
    csv_path = Path("sim_data") / f"plot_data_dyn_wake_{use_dyn_wake}_shear_{shear_exp}.csv"
    csv_path.parent.mkdir(exist_ok=True)
    df_plot.to_csv(csv_path, index=False)
    print(f"Plot data saved to {csv_path}")

    # save spanwise data separately (different length than time series)
    df_span = pd.DataFrame({
        "r":     structure.r,
        "py_avg": py_avg,
        "pz_avg": pz_avg,
    })
    span_csv_path = Path("sim_data") / f"spanwise_data_dyn_wake_{use_dyn_wake}_shear_{shear_exp}.csv"
    df_span.to_csv(span_csv_path, index=False)
    print(f"Spanwise data saved to {span_csv_path}")


    
    #[-0.27, -0.33],
                        #  [-2.3, -3.1],
                        #  [1.0, 1.6],
                        #  [2.8, 4.8],
                        #  [0.22, 0.32],
                        #  [0.6, 1.0],

    # plot py and pz avg over blade span position
    # # Plot uvw vs time at r=65m
    # plot_flexible(t,
    #                 [v_u, v_v, v_w],
    #                 ["u", "v", "w"],
    #                 "Time [s]", ["m/s", "m/s", "m/s"],
    #                 "Wind_velocity_components_at_r_65m_time_series",
    #                 3,1,
    #                 shear_exp,
    #                 turb=TI)

if do["plot_ass_1_3"]:
    # load the data from the two simulations

    df_wake = pd.read_csv("sim_data/plot_data_dyn_wake_True_shear_0.csv")
    df_no_wake = pd.read_csv("sim_data/plot_data_dyn_wake_False_shear_0.csv")
    df_spanwise_wake = pd.read_csv("sim_data/spanwise_data_dyn_wake_True_shear_0.csv")
    df_spanwise_no_wake = pd.read_csv("sim_data/spanwise_data_dyn_wake_False_shear_0.csv")

    
    shear_exp = 0
    plot_flexible(df_wake["time"],
                    y_values=[
                        [df_wake["wy_5"], df_no_wake["wy_5"]],
                        [df_wake["wz_5"], df_no_wake["wz_5"]],
                        [df_wake["power_blade0"]/1e6, df_no_wake["power_blade0"]/1e6],
                        [df_wake["power_total"]/1e6, df_no_wake["power_total"]/1e6],
                        [df_wake["thrust_blade0"]/1e3, df_no_wake["thrust_blade0"]/1e3],
                        [df_wake["thrust_total"]/1e3, df_no_wake["thrust_total"]/1e3]],
                    labels=[
                        ["wake", "no wake"],
                        ["wake", "no wake"],
                        ["wake", "no wake"],
                        ["wake", "no wake"],
                        ["wake", "no wake"],
                        ["wake", "no wake"]],
                    x_label="Time [s]",
                    y_units=["W y at r=65m[m/s]",
                             "W z at r=65m[m/s]",
                             "Power blade 0 [MW]",
                             "Total Power [MW]",
                             "Thrust blade 0 [kN]",
                             "Total Thrust [kN]"],
                    save_name="induced_power_thrust_total_bladewise_wake_comparison",
                    shear_exp=shear_exp,
                    xlims=[50, 250],
                    ylims=[
                            [-0.27, -0.33],
                            [-2.3, -3.1],
                            [1.0, 1.6],
                            [2.8, 4.8],
                            [220, 320],
                            [600, 1000]
                        ])

if do["ass_1_4_no_tower"]:
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.72
    yaw = 0
    tilt = 0

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt)

    # Wind parameters
    shear_exp = 0
    V_hub = 8
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
    TI = 0.1

    # Tower parameters
    tower_effects = False

    # Aero parameters
    use_dyn_wake = True
    use_dyn_stall = True

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 130
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    def pitch_schedule(t):
        if t < 100:
            return [0.0, 0.0, 0.0]
        elif t < 150:
            return [2.0, 2.0, 2.0]
        else:
            return [0.0, 0.0, 0.0]

    # UNCOMMENT / COMMENT TO ENABLE OR DISABLE PITCH SCHEDULE
    # structure.pitch_schedule = pitch_schedule
    if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall)

    
    #%% RECORDERS
    
    r_65 = structure.r[8]
    print("index 8 corresponds to radius ", r_65)
    recorders = []

    # record SPANWISE loads for each blade element on blade 0
    for span_pos in range(len(structure.r)):
        p5_recorder = p_5_recorder(name=f"aero_{span_pos}_{use_dyn_wake}", blade_idx=0, element_idx=span_pos)
        # wind5_recorder = wind_5_recorder(name=f"wind_5_{span_pos}", blade_idx=0, element_idx=span_pos)
        recorders.append(p5_recorder)
        # recorders.append(wind5_recorder)
    
    # record BLADEWISE thrust, torque, and power for each blade
    for blade_idx in range(structure.n_blades):
        recorders.append(mech_out_recorder(name=f"mech_out_blade_{blade_idx}_{use_dyn_wake}", blade_idx=blade_idx))
        recorders.append(w_5_recorder(name=f"w_5_blade_{blade_idx}_{use_dyn_wake}", blade_idx=blade_idx, element_idx=8)) # induced wind 
    
    recorders.append(wind_5_recorder(name=f"wind_5_{use_dyn_wake}", blade_idx=0, element_idx=8)) # wind velocity
    recorders.append(w_5_recorder(name=f"w_5_{use_dyn_wake}", blade_idx=0, element_idx=8)) # induced wind
    
    #%% Set up simulation, run, and save wind recorder data
    print(f"\nRunning simulation with parameters:\n")
    print(f"omega = {omega_init:.2f} rad/s ")
    print(f"yaw = {yaw} degrees,")
    print(f"tilt = {tilt} degrees")
    print(f"shear_exp = {shear_exp}")
    print(f"V_hub={V_hub} m/s")
    print(f"use_dyn_wake = {use_dyn_wake}")
    print(f"use_dyn_stall = {use_dyn_stall}")
    print(f"tower_effects = {tower_effects}")

    simulation = Simulation(structure, aero, wind=wind_profile, recorders=recorders)
    simulation.run(dt, T)
    print("\nSimulation complete. Saving data...\n")
    simulation.save_recorders("sim_data", overwrite=True)

    #%% EXTRACT DATA FROM RECORDERS
    # Get data (saving above not needed for this) for plotting
    data = simulation.get_recorders()
    azimuth = data["time"] * omega_init / (2 * np.pi) * 360
    t = data["time"]

    # induced wind
    wy_5 = data[f"w_5_{use_dyn_wake}"]["w_y"]
    wz_5 = data[f"w_5_{use_dyn_wake}"]["w_z"]
    wy_qs_5 = data[f"w_5_{use_dyn_wake}"]["w_y_qs"]
    wz_qs_5 = data[f"w_5_{use_dyn_wake}"]["w_z_qs"]

    

    # aerodynamic loads
    py_5_8 = data[f"aero_8_{use_dyn_wake}"]["p_y"]
    pz_5_8 = data[f"aero_8_{use_dyn_wake}"]["p_z"]

    # wind velocity
    v_u = data[f"wind_5_{use_dyn_wake}"]["u"]
    v_v = data[f"wind_5_{use_dyn_wake}"]["v"]
    v_w = data[f"wind_5_{use_dyn_wake}"]["w"]

    
    print(f"mean of v_w: {np.mean(v_w)}")
    # get the average py over one revolution for element 10 for the last revolution
    revolution_time = 2 * np.pi / omega_init
    total_time = data["time"][-1]
    last_revolution_time = total_time - revolution_time
    last_revolution_indices = np.where((data["time"] >= last_revolution_time) & (data["time"] <= total_time))[0]

    load_data = {
        qty: np.array([data[f"aero_{i}_{use_dyn_wake}"][qty] for i in range(len(structure.r))])
        for qty in ["p_y", "p_z"]
    }

    # store the average py and pz for all blade elements over the last revolution in an array
    py_avg = np.array([np.mean(load_data["p_y"][i][last_revolution_indices]) for i in range(len(structure.r))])
    pz_avg = np.array([np.mean(load_data["p_z"][i][last_revolution_indices]) for i in range(len(structure.r))])

    blade_data = {
        qty: np.array([data[f"mech_out_blade_{i}_{use_dyn_wake}"][qty] for i in range(structure.n_blades)])
        for qty in ["thrust", "torque", "power"]
    }

    induced_velocities = {
        qty: np.array([data[f"w_5_blade_{i}_{use_dyn_wake}"][qty] for i in range(structure.n_blades)])
        for qty in ["w_y", "w_z", "w_y_qs", "w_z_qs"]
    }

    total_thrust = blade_data["thrust"].sum(axis=0)
    total_torque = blade_data["torque"].sum(axis=0)
    total_power  = blade_data["power"].sum(axis=0)

    # normalize data to compare across dimensions
    total_thrust_normalized = total_thrust / np.max(np.abs(total_thrust))
    print(f" max total thrust: {np.max(np.abs(total_thrust))}")
    total_torque_normalized = total_torque / np.max(np.abs(total_torque))
    total_power_normalized = total_power / 10e6

    # compute average total power with the last revolution
    avg_power = np.mean(total_power[last_revolution_indices])
    print(f"Average power for each blade over the last revolution: {avg_power:.3e} W")
    avg_thrust = np.mean(total_thrust[last_revolution_indices])
    print(f"Average thrust for each blade over the last revolution: {avg_thrust:.3e} N")

    py_avg_normalized = py_avg / np.max(np.abs(py_avg))
    pz_avg_normalized = pz_avg / np.max(np.abs(pz_avg))


    # load data from steady bem code located in data folder (csv file)
    df_stdy_bem = pd.read_csv("data/BEM_46310.csv")
    stdy_py = df_stdy_bem["p_t_torque"].values
    stdy_pz = df_stdy_bem["p_n_thrust"].values

    print("\n")

    #%% PLOTTING

    # plot pz and total thrust in two subplots
    plot_flexible(
        x_val=t,
        y_values=[
            [pz_5_8/1e3],
            [total_thrust/1e3]],
        labels=[
            ["Normal load p_z @ r=65m"],
            ["Total Thrust"]],
        x_label="Time [s]",
        y_units=["[kN/m]", "[kN]"],
        save_name="pz_thrust",
        shear_exp=shear_exp,
        xlims=[50, 130],
        ylims=[[3,6.5],[700, 1000]],
        turb=True)

    plot_psd_flexible(
        signals= [
            [pz_5_8],
            [total_thrust]],
        labels=[
            ["Normal load p_z @ r=65m"],
            ["Total Thrust"]],
        fs=1/dt,
        y_units=["PSD (N/m)^2/Hz", "PSD (N)^2/Hz"],
        vlines=[{"x": 1, "color": "red", "linestyle": "--"},
                {"x": 2, "color": "red", "linestyle": "--"},
                {"x": 3, "color": "red", "linestyle": "--"},
                {"x": 6, "color": "red", "linestyle": "--"},
                {"x": 9, "color": "red", "linestyle": "--"}],
        save_name="pz_thrust_psd",
        shear_exp=shear_exp,
        omega=omega_init,
        nperseg=1024,
        xlims=[0, 10],
        ylims=[[10, 10**6], [10**3, 10**11]],
        turb=True
    )

    #%% SAVE PLOT DATA TO CSV
    df_plot = pd.DataFrame({
        "time":          t,
        "azimuth":       azimuth,
        "wy_5":          wy_5,
        "wz_5":          wz_5,
        "wy_qs_5":       wy_qs_5,
        "wz_qs_5":       wz_qs_5,
        "pz_5_8":        pz_5_8,
        "py_5_8":        py_5_8,
        "power_blade0":  blade_data["power"][0],
        "power_blade1":  blade_data["power"][1],
        "power_blade2":  blade_data["power"][2],
        "power_total":   total_power,
        "thrust_blade0": blade_data["thrust"][0],
        "thrust_blade1": blade_data["thrust"][1],
        "thrust_blade2": blade_data["thrust"][2],
        "thrust_total":  total_thrust,
        "torque_blade0": blade_data["torque"][0],
        "torque_blade1": blade_data["torque"][1],
        "torque_blade2": blade_data["torque"][2],
        "torque_total":  total_torque,
        "v_u":           v_u,
        "v_v":           v_v,
        "v_w":           v_w,
    })
    csv_path = Path("sim_data") / f"plot_data_TI_{TI}_tower_{tower_effects}_shear_{shear_exp}.csv"
    csv_path.parent.mkdir(exist_ok=True)
    df_plot.to_csv(csv_path, index=False)
    print(f"Plot data saved to {csv_path}")

    # save spanwise data separately (different length)
    df_span = pd.DataFrame({
        "r":      structure.r,
        "py_avg": py_avg,
        "pz_avg": pz_avg,
    })
    span_csv_path = Path("sim_data") / f"spanwise_data_TI_{TI}_tower_{tower_effects}_shear_{shear_exp}.csv"
    df_span.to_csv(span_csv_path, index=False)
    print(f"Spanwise data saved to {span_csv_path}")

if do["ass_1_4_w_tower"]:
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.72
    yaw = 0
    tilt = 0

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt)

    # Wind parameters
    shear_exp = 0
    V_hub = 8
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
    TI = 0.1

    # Tower parameters
    tower_effects = True

    # Aero parameters
    use_dyn_wake = True
    use_dyn_stall = True

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 130
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    def pitch_schedule(t):
        if t < 100:
            return [0.0, 0.0, 0.0]
        elif t < 150:
            return [2.0, 2.0, 2.0]
        else:
            return [0.0, 0.0, 0.0]

    # UNCOMMENT / COMMENT TO ENABLE OR DISABLE PITCH SCHEDULE
    # structure.pitch_schedule = pitch_schedule
    if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall)

    
    #%% RECORDERS
    
    r_65 = structure.r[8]
    print("index 8 corresponds to radius ", r_65)
    recorders = []

    # record SPANWISE loads for each blade element on blade 0
    for span_pos in range(len(structure.r)):
        p5_recorder = p_5_recorder(name=f"aero_{span_pos}_{use_dyn_wake}", blade_idx=0, element_idx=span_pos)
        # wind5_recorder = wind_5_recorder(name=f"wind_5_{span_pos}", blade_idx=0, element_idx=span_pos)
        recorders.append(p5_recorder)
        # recorders.append(wind5_recorder)
    
    # record BLADEWISE thrust, torque, and power for each blade
    for blade_idx in range(structure.n_blades):
        recorders.append(mech_out_recorder(name=f"mech_out_blade_{blade_idx}_{use_dyn_wake}", blade_idx=blade_idx))
        recorders.append(w_5_recorder(name=f"w_5_blade_{blade_idx}_{use_dyn_wake}", blade_idx=blade_idx, element_idx=8)) # induced wind 
    
    recorders.append(wind_5_recorder(name=f"wind_5_{use_dyn_wake}", blade_idx=0, element_idx=8)) # wind velocity
    recorders.append(w_5_recorder(name=f"w_5_{use_dyn_wake}", blade_idx=0, element_idx=8)) # induced wind
    
    #%% Set up simulation, run, and save wind recorder data
    print(f"\nRunning simulation with parameters:\n")
    print(f"omega = {omega_init:.2f} rad/s ")
    print(f"yaw = {yaw} degrees,")
    print(f"tilt = {tilt} degrees")
    print(f"shear_exp = {shear_exp}")
    print(f"V_hub={V_hub} m/s")
    print(f"use_dyn_wake = {use_dyn_wake}")
    print(f"use_dyn_stall = {use_dyn_stall}")
    print(f"tower_effects = {tower_effects}")

    simulation = Simulation(structure, aero, wind=wind_profile, recorders=recorders)
    simulation.run(dt, T)
    print("\nSimulation complete. Saving data...\n")
    simulation.save_recorders("sim_data", overwrite=True)

    #%% EXTRACT DATA FROM RECORDERS
    # Get data (saving above not needed for this) for plotting
    data = simulation.get_recorders()
    azimuth = data["time"] * omega_init / (2 * np.pi) * 360
    t = data["time"]

    # induced wind
    wy_5 = data[f"w_5_{use_dyn_wake}"]["w_y"]
    wz_5 = data[f"w_5_{use_dyn_wake}"]["w_z"]
    wy_qs_5 = data[f"w_5_{use_dyn_wake}"]["w_y_qs"]
    wz_qs_5 = data[f"w_5_{use_dyn_wake}"]["w_z_qs"]

    

    # aerodynamic loads
    py_5_8 = data[f"aero_8_{use_dyn_wake}"]["p_y"]
    pz_5_8 = data[f"aero_8_{use_dyn_wake}"]["p_z"]

    # wind velocity
    v_u = data[f"wind_5_{use_dyn_wake}"]["u"]
    v_v = data[f"wind_5_{use_dyn_wake}"]["v"]
    v_w = data[f"wind_5_{use_dyn_wake}"]["w"]

    
    print(f"mean of v_w: {np.mean(v_w)}")
    # get the average py over one revolution for element 10 for the last revolution
    revolution_time = 2 * np.pi / omega_init
    total_time = data["time"][-1]
    last_revolution_time = total_time - revolution_time
    last_revolution_indices = np.where((data["time"] >= last_revolution_time) & (data["time"] <= total_time))[0]

    load_data = {
        qty: np.array([data[f"aero_{i}_{use_dyn_wake}"][qty] for i in range(len(structure.r))])
        for qty in ["p_y", "p_z"]
    }

    # store the average py and pz for all blade elements over the last revolution in an array
    py_avg = np.array([np.mean(load_data["p_y"][i][last_revolution_indices]) for i in range(len(structure.r))])
    pz_avg = np.array([np.mean(load_data["p_z"][i][last_revolution_indices]) for i in range(len(structure.r))])

    blade_data = {
        qty: np.array([data[f"mech_out_blade_{i}_{use_dyn_wake}"][qty] for i in range(structure.n_blades)])
        for qty in ["thrust", "torque", "power"]
    }

    induced_velocities = {
        qty: np.array([data[f"w_5_blade_{i}_{use_dyn_wake}"][qty] for i in range(structure.n_blades)])
        for qty in ["w_y", "w_z", "w_y_qs", "w_z_qs"]
    }

    total_thrust = blade_data["thrust"].sum(axis=0)
    total_torque = blade_data["torque"].sum(axis=0)
    total_power  = blade_data["power"].sum(axis=0)

    # normalize data to compare across dimensions
    total_thrust_normalized = total_thrust / np.max(np.abs(total_thrust))
    print(f" max total thrust: {np.max(np.abs(total_thrust))}")
    total_torque_normalized = total_torque / np.max(np.abs(total_torque))
    total_power_normalized = total_power / 10e6

    # compute average total power with the last revolution
    avg_power = np.mean(total_power[last_revolution_indices])
    print(f"Average power for each blade over the last revolution: {avg_power:.3e} W")
    avg_thrust = np.mean(total_thrust[last_revolution_indices])
    print(f"Average thrust for each blade over the last revolution: {avg_thrust:.3e} N")

    py_avg_normalized = py_avg / np.max(np.abs(py_avg))
    pz_avg_normalized = pz_avg / np.max(np.abs(pz_avg))


    # load data from steady bem code located in data folder (csv file)
    df_stdy_bem = pd.read_csv("data/BEM_46310.csv")
    stdy_py = df_stdy_bem["p_t_torque"].values
    stdy_pz = df_stdy_bem["p_n_thrust"].values

    print("\n")

    #%% PLOTTING

    # plot pz and total thrust in two subplots
    plot_flexible(
        x_val=t,
        y_values=[
            [pz_5_8/1e3],
            [total_thrust/1e3]],
        labels=[
            ["Normal load p_z @ r=65m"],
            ["Total Thrust"]],
        x_label="Time [s]",
        y_units=["[kN/m]", "[kN]"],
        save_name="pz_thrust",
        shear_exp=shear_exp,
        xlims=[50, 130],
        ylims=[[3,6.5],[700, 1000]],
        turb=True)

    plot_psd_flexible(
        signals= [
            [pz_5_8],
            [total_thrust]],
        labels=[
            ["Normal load p_z @ r=65m"],
            ["Total Thrust"]],
        fs=1/dt,
        y_units=["PSD (N/m)^2/Hz", "PSD (N)^2/Hz"],
        vlines=[{"x": 1, "color": "red", "linestyle": "--"},
                {"x": 2, "color": "red", "linestyle": "--"},
                {"x": 3, "color": "red", "linestyle": "--"},
                {"x": 6, "color": "red", "linestyle": "--"},
                {"x": 9, "color": "red", "linestyle": "--"}],
        save_name="pz_thrust_psd",
        shear_exp=shear_exp,
        omega=omega_init,
        nperseg=1024,
        xlims=[0, 10],
        ylims=[[10, 10**6], [10**3, 10**11]],
        turb=True
    )

    #%% SAVE PLOT DATA TO CSV
    df_plot = pd.DataFrame({
        "time":          t,
        "azimuth":       azimuth,
        "wy_5":          wy_5,
        "wz_5":          wz_5,
        "wy_qs_5":       wy_qs_5,
        "wz_qs_5":       wz_qs_5,
        "pz_5_8":        pz_5_8,
        "py_5_8":        py_5_8,
        "power_blade0":  blade_data["power"][0],
        "power_blade1":  blade_data["power"][1],
        "power_blade2":  blade_data["power"][2],
        "power_total":   total_power,
        "thrust_blade0": blade_data["thrust"][0],
        "thrust_blade1": blade_data["thrust"][1],
        "thrust_blade2": blade_data["thrust"][2],
        "thrust_total":  total_thrust,
        "torque_blade0": blade_data["torque"][0],
        "torque_blade1": blade_data["torque"][1],
        "torque_blade2": blade_data["torque"][2],
        "torque_total":  total_torque,
        "v_u":           v_u,
        "v_v":           v_v,
        "v_w":           v_w,
    })
    csv_path = Path("sim_data") / f"plot_data_TI_{TI}_tower_{tower_effects}_shear_{shear_exp}.csv"
    csv_path.parent.mkdir(exist_ok=True)
    df_plot.to_csv(csv_path, index=False)
    print(f"Plot data saved to {csv_path}")

    # save spanwise data separately (different length)
    df_span = pd.DataFrame({
        "r":      structure.r,
        "py_avg": py_avg,
        "pz_avg": pz_avg,
    })
    span_csv_path = Path("sim_data") / f"spanwise_data_TI_{TI}_tower_{tower_effects}_shear_{shear_exp}.csv"
    df_span.to_csv(span_csv_path, index=False)
    print(f"Spanwise data saved to {span_csv_path}")

if do["ass_1_4_no_turb_w_tower"]:
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.72
    yaw = 0
    tilt = 0

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt)

    # Wind parameters
    shear_exp = 0
    V_hub = 8
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
    TI = 0

    # Tower parameters
    tower_effects = True

    # Aero parameters
    use_dyn_wake = True
    use_dyn_stall = True

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 130
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    def pitch_schedule(t):
        if t < 100:
            return [0.0, 0.0, 0.0]
        elif t < 150:
            return [2.0, 2.0, 2.0]
        else:
            return [0.0, 0.0, 0.0]

    # UNCOMMENT / COMMENT TO ENABLE OR DISABLE PITCH SCHEDULE
    # structure.pitch_schedule = pitch_schedule
    if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall)

    
    #%% RECORDERS
    
    r_65 = structure.r[8]
    print("index 8 corresponds to radius ", r_65)
    recorders = []

    # record SPANWISE loads for each blade element on blade 0
    for span_pos in range(len(structure.r)):
        p5_recorder = p_5_recorder(name=f"aero_{span_pos}_{use_dyn_wake}", blade_idx=0, element_idx=span_pos)
        # wind5_recorder = wind_5_recorder(name=f"wind_5_{span_pos}", blade_idx=0, element_idx=span_pos)
        recorders.append(p5_recorder)
        # recorders.append(wind5_recorder)
    
    # record BLADEWISE thrust, torque, and power for each blade
    for blade_idx in range(structure.n_blades):
        recorders.append(mech_out_recorder(name=f"mech_out_blade_{blade_idx}_{use_dyn_wake}", blade_idx=blade_idx))
        recorders.append(w_5_recorder(name=f"w_5_blade_{blade_idx}_{use_dyn_wake}", blade_idx=blade_idx, element_idx=8)) # induced wind 
    
    recorders.append(wind_5_recorder(name=f"wind_5_{use_dyn_wake}", blade_idx=0, element_idx=8)) # wind velocity
    recorders.append(w_5_recorder(name=f"w_5_{use_dyn_wake}", blade_idx=0, element_idx=8)) # induced wind
    
    #%% Set up simulation, run, and save wind recorder data
    print(f"\nRunning simulation with parameters:\n")
    print(f"omega = {omega_init:.2f} rad/s ")
    print(f"yaw = {yaw} degrees,")
    print(f"tilt = {tilt} degrees")
    print(f"shear_exp = {shear_exp}")
    print(f"V_hub={V_hub} m/s")
    print(f"use_dyn_wake = {use_dyn_wake}")
    print(f"use_dyn_stall = {use_dyn_stall}")
    print(f"tower_effects = {tower_effects}")

    simulation = Simulation(structure, aero, wind=wind_profile, recorders=recorders)
    simulation.run(dt, T)
    print("\nSimulation complete. Saving data...\n")
    simulation.save_recorders("sim_data", overwrite=True)

    #%% EXTRACT DATA FROM RECORDERS
    # Get data (saving above not needed for this) for plotting
    data = simulation.get_recorders()
    azimuth = data["time"] * omega_init / (2 * np.pi) * 360
    t = data["time"]

    # induced wind
    wy_5 = data[f"w_5_{use_dyn_wake}"]["w_y"]
    wz_5 = data[f"w_5_{use_dyn_wake}"]["w_z"]
    wy_qs_5 = data[f"w_5_{use_dyn_wake}"]["w_y_qs"]
    wz_qs_5 = data[f"w_5_{use_dyn_wake}"]["w_z_qs"]

    

    # aerodynamic loads
    py_5_8 = data[f"aero_8_{use_dyn_wake}"]["p_y"]
    pz_5_8 = data[f"aero_8_{use_dyn_wake}"]["p_z"]

    # wind velocity
    v_u = data[f"wind_5_{use_dyn_wake}"]["u"]
    v_v = data[f"wind_5_{use_dyn_wake}"]["v"]
    v_w = data[f"wind_5_{use_dyn_wake}"]["w"]

    
    print(f"mean of v_w: {np.mean(v_w)}")
    # get the average py over one revolution for element 10 for the last revolution
    revolution_time = 2 * np.pi / omega_init
    total_time = data["time"][-1]
    last_revolution_time = total_time - revolution_time
    last_revolution_indices = np.where((data["time"] >= last_revolution_time) & (data["time"] <= total_time))[0]

    load_data = {
        qty: np.array([data[f"aero_{i}_{use_dyn_wake}"][qty] for i in range(len(structure.r))])
        for qty in ["p_y", "p_z"]
    }

    # store the average py and pz for all blade elements over the last revolution in an array
    py_avg = np.array([np.mean(load_data["p_y"][i][last_revolution_indices]) for i in range(len(structure.r))])
    pz_avg = np.array([np.mean(load_data["p_z"][i][last_revolution_indices]) for i in range(len(structure.r))])

    blade_data = {
        qty: np.array([data[f"mech_out_blade_{i}_{use_dyn_wake}"][qty] for i in range(structure.n_blades)])
        for qty in ["thrust", "torque", "power"]
    }

    induced_velocities = {
        qty: np.array([data[f"w_5_blade_{i}_{use_dyn_wake}"][qty] for i in range(structure.n_blades)])
        for qty in ["w_y", "w_z", "w_y_qs", "w_z_qs"]
    }

    total_thrust = blade_data["thrust"].sum(axis=0)
    total_torque = blade_data["torque"].sum(axis=0)
    total_power  = blade_data["power"].sum(axis=0)

    # normalize data to compare across dimensions
    total_thrust_normalized = total_thrust / np.max(np.abs(total_thrust))
    print(f" max total thrust: {np.max(np.abs(total_thrust))}")
    total_torque_normalized = total_torque / np.max(np.abs(total_torque))
    total_power_normalized = total_power / 10e6

    # compute average total power with the last revolution
    avg_power = np.mean(total_power[last_revolution_indices])
    print(f"Average power for each blade over the last revolution: {avg_power:.3e} W")
    avg_thrust = np.mean(total_thrust[last_revolution_indices])
    print(f"Average thrust for each blade over the last revolution: {avg_thrust:.3e} N")

    py_avg_normalized = py_avg / np.max(np.abs(py_avg))
    pz_avg_normalized = pz_avg / np.max(np.abs(pz_avg))


    # load data from steady bem code located in data folder (csv file)
    df_stdy_bem = pd.read_csv("data/BEM_46310.csv")
    stdy_py = df_stdy_bem["p_t_torque"].values
    stdy_pz = df_stdy_bem["p_n_thrust"].values

    print("\n")

    #%% PLOTTING

    # plot pz and total thrust in two subplots
    plot_flexible(
        x_val=t,
        y_values=[
            [pz_5_8/1e3],
            [total_thrust/1e3]],
        labels=[
            ["Normal load p_z @ r=65m"],
            ["Total Thrust"]],
        x_label="Time [s]",
        y_units=["[kN/m]", "[kN]"],
        save_name="pz_thrust",
        shear_exp=shear_exp,
        xlims=[50, 130],
        ylims=[[3,6.5],[700, 1000]],
        turb=TI)

    plot_psd_flexible(
        signals= [
            [pz_5_8],
            [total_thrust]],
        labels=[
            ["Normal load p_z @ r=65m"],
            ["Total Thrust"]],
        fs=1/dt,
        y_units=["PSD (N/m)^2/Hz", "PSD (N)^2/Hz"],
        vlines=[{"x": 1, "color": "red", "linestyle": "--"},
                {"x": 2, "color": "red", "linestyle": "--"},
                {"x": 3, "color": "red", "linestyle": "--"},
                {"x": 6, "color": "red", "linestyle": "--"},
                {"x": 9, "color": "red", "linestyle": "--"}],
        save_name="pz_thrust_psd",
        shear_exp=shear_exp,
        omega=omega_init,
        nperseg=1024,
        xlims=[10**(-1), 10],
        ylims=[[10**(-2), 10**7], [10**(1), 10**11]],
        turb=TI
    )

    #%% SAVE PLOT DATA TO CSV
    df_plot = pd.DataFrame({
        "time":          t,
        "azimuth":       azimuth,
        "wy_5":          wy_5,
        "wz_5":          wz_5,
        "wy_qs_5":       wy_qs_5,
        "wz_qs_5":       wz_qs_5,
        "pz_5_8":        pz_5_8,
        "py_5_8":        py_5_8,
        "power_blade0":  blade_data["power"][0],
        "power_blade1":  blade_data["power"][1],
        "power_blade2":  blade_data["power"][2],
        "power_total":   total_power,
        "thrust_blade0": blade_data["thrust"][0],
        "thrust_blade1": blade_data["thrust"][1],
        "thrust_blade2": blade_data["thrust"][2],
        "thrust_total":  total_thrust,
        "torque_blade0": blade_data["torque"][0],
        "torque_blade1": blade_data["torque"][1],
        "torque_blade2": blade_data["torque"][2],
        "torque_total":  total_torque,
        "v_u":           v_u,
        "v_v":           v_v,
        "v_w":           v_w,
    })
    csv_path = Path("sim_data") / f"plot_data_TI_{TI}_tower_{tower_effects}_shear_{shear_exp}.csv"
    csv_path.parent.mkdir(exist_ok=True)
    df_plot.to_csv(csv_path, index=False)
    print(f"Plot data saved to {csv_path}")

    # save spanwise data separately (different length)
    df_span = pd.DataFrame({
        "r":      structure.r,
        "py_avg": py_avg,
        "pz_avg": pz_avg,
    })
    span_csv_path = Path("sim_data") / f"spanwise_data_TI_{TI}_tower_{tower_effects}_shear_{shear_exp}.csv"
    df_span.to_csv(span_csv_path, index=False)
    print(f"Spanwise data saved to {span_csv_path}")

if do["ass_1_4_plot"]:

    # --- parameters (must match what was used in ass_1_4) ---
    omega_init    = 0.72
    shear_exp     = 0
    TI            = 0.1
    tower_effects = False
    dt            = 0.1
    use_dyn_wake  = True
    use_dyn_stall = True

    structure = RigidStructure(omega_init)  # needed for structure.r, n_blades

    # --- load recorders directly from CSV files ---
    sim_path = Path("sim_data")

    # time (from any file, all share same time axis)
    t       = pd.read_csv(sim_path / f"wind_5_{use_dyn_wake}.csv")["time"].values
    azimuth = t * omega_init / (2 * np.pi) * 360

    # induced wind at r=65m, blade 0
    df_w5       = pd.read_csv(sim_path / f"w_5_{use_dyn_wake}.csv")
    wy_5        = df_w5["w_y"].values
    wz_5        = df_w5["w_z"].values
    wy_qs_5     = df_w5["w_y_qs"].values
    wz_qs_5     = df_w5["w_z_qs"].values

    # aerodynamic loads at element 8, blade 0
    df_aero8    = pd.read_csv(sim_path / f"aero_8_{use_dyn_wake}.csv")
    py_5_8      = df_aero8["p_y"].values
    pz_5_8      = df_aero8["p_z"].values

    # wind velocity at r=65m, blade 0
    df_wind5    = pd.read_csv(sim_path / f"wind_5_{use_dyn_wake}.csv")
    v_u         = df_wind5["u"].values
    v_v         = df_wind5["v"].values
    v_w         = df_wind5["w"].values
    print(f"mean of v_w: {np.mean(v_w)}")

    # bladewise thrust/torque/power
    blade_dfs = [pd.read_csv(sim_path / f"mech_out_blade_{i}_{use_dyn_wake}.csv") for i in range(structure.n_blades)]
    blade_data = {
        qty: np.array([df[qty].values for df in blade_dfs])
        for qty in ["thrust", "torque", "power"]
    }
    total_thrust = blade_data["thrust"].sum(axis=0)
    total_torque = blade_data["torque"].sum(axis=0)
    total_power  = blade_data["power"].sum(axis=0)

    # spanwise loads (averaged over last revolution)
    revolution_time      = 2 * np.pi / omega_init
    total_time           = t[-1]
    last_revolution_time = total_time - revolution_time
    last_revolution_indices = np.where(
        (t >= last_revolution_time) & (t <= total_time)
    )[0]

    aero_dfs = [pd.read_csv(sim_path / f"aero_{i}_{use_dyn_wake}.csv") for i in range(len(structure.r))]
    py_avg = np.array([np.mean(df["p_y"].values[last_revolution_indices]) for df in aero_dfs])
    pz_avg = np.array([np.mean(df["p_z"].values[last_revolution_indices]) for df in aero_dfs])

    avg_power  = np.mean(total_power[last_revolution_indices])
    avg_thrust = np.mean(total_thrust[last_revolution_indices])
    print(f"Average power  over last revolution: {avg_power:.3e} W")
    print(f"Average thrust over last revolution: {avg_thrust:.3e} N")

    #%% PLOTTING
    plot_flexible(
        x_val=t,
        y_values=[
            [pz_5_8/1e3],
            [total_thrust/1e3]],
        labels=[
            ["Normal load p_z @ r=65m"],
            ["Total Thrust"]],
        x_label="Time [s]",
        y_units=["[kN/m]", "[kN]"],
        save_name="pz_thrust",
        shear_exp=shear_exp,
        xlims=[50, 130],
        ylims=[[3.4, 6.5], [700, 950]],
        turb=True)

    plot_psd_flexible(
        signals=[
            [pz_5_8],
            [total_thrust]],
        labels=[
            ["Normal load p_z @ r=65m"],
            ["Total Thrust"]],
        fs=1/dt,
        y_units=["PSD (N/m)^2/Hz", "PSD (N)^2/Hz"],
        vlines=[
            {"x": 1, "color": "red", "linestyle": "--"},
            {"x": 2, "color": "red", "linestyle": "--"},
            {"x": 3, "color": "red", "linestyle": "--"},
            {"x": 6, "color": "red", "linestyle": "--"},
            {"x": 9, "color": "red", "linestyle": "--"},
        ],
        save_name="pz_thrust",
        shear_exp=shear_exp,
        omega=omega_init,
        nperseg=1024,
        xlims=[0, 10],
        ylims=[[10**2, None], [10**3, None]],
        turb=True)

if do["ass_1_4_plot_comparison"]:

    # --- parameters ---
    omega_init    = 0.72
    shear_exp     = 0
    TI_turb       = 0.1
    TI_no_turb    = 0
    dt            = 0.1

    # --- load both datasets ---
    sim_path = Path("sim_data")

    df_turb_no_tower    = pd.read_csv(sim_path / f"plot_data_TI_{TI_turb}_tower_{False}_shear_{shear_exp}.csv")
    df_turb_tower = pd.read_csv(sim_path / f"plot_data_TI_{TI_turb}_tower_{True}_shear_{shear_exp}.csv")
    df_span_turb_no_tower    = pd.read_csv(sim_path / f"spanwise_data_TI_{TI_turb}_tower_{False}_shear_{shear_exp}.csv")
    df_span_turb_tower = pd.read_csv(sim_path / f"spanwise_data_TI_{TI_turb}_tower_{True}_shear_{shear_exp}.csv")

    t = df_turb_no_tower["time"].values  # both simulations share same time axis

    # --- time series comparison plot ---
    plot_flexible(
        x_val=t,
        y_values=[
            [df_turb_no_tower["pz_5_8"]/1e3,        df_turb_tower["pz_5_8"]/1e3],
            [df_turb_no_tower["thrust_total"]/1e3,  df_turb_tower["thrust_total"]/1e3]
        ],
        labels=[
            ["turb no tower", "turb w. tower"],
            ["turb no tower", "turb w. tower"]
        ],
        x_label="Time [s]",
        y_units=[
            "p_z @ r=65m [kN/m]",
            "Total Thrust [kN]"
        ],
        save_name="tower_vs_no_tower_comparison",
        shear_exp=shear_exp,
        xlims=[50, 130],
        ylims=[[3.4, 6.5], [700, 950]])

    # --- PSD comparison plot ---
    plot_psd_flexible(
        signals=[

            [df_turb_no_tower["pz_5_8"],       df_turb_tower["pz_5_8"]],
            [df_turb_no_tower["thrust_total"],  df_turb_tower["thrust_total"]]
        ],
        labels=[
            ["p_z turb no tower", "p_z turb w. tower"],
            ["thrust turb no tower", "thrust turb w. tower"],
        ],
        fs=1/dt,
        y_units=["PSD p_z (N/m)^2/Hz", "PSD thrust (N)^2/Hz"],
        vlines=[
            {"x": 1, "color": "red",  "linestyle": "--"},
            {"x": 2, "color": "red",  "linestyle": "--"},
            {"x": 3, "color": "red",  "linestyle": "--"},
            {"x": 6, "color": "red",  "linestyle": "--"},
            {"x": 9, "color": "red",  "linestyle": "--"},
        ],
        save_name="tower_vs_no_tower_comparison",
        shear_exp=shear_exp,
        omega=omega_init,
        nperseg=1024,
        xlims=[0, 10],
        ylims=[[1e2, 1e7], [1e2, 1e11]]
        )

if do["controller_test"]:
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.5
    yaw = 0
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt, pitch_init = [0, 0, 0])

    # Wind parameters
    shear_exp = 0
    V_hub = 15
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
    TI = 0

    # Tower parameters
    tower_effects = False

    # Aero parameters
    use_dyn_wake=True
    use_dyn_stall=True

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 60
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    # def pitch_schedule(t):
    #     if t < 100:
    #         return [0.0, 0.0, 0.0]
    #     elif t < 150:
    #         return [2.0, 2.0, 2.0]
    #     else:
    #         return [0.0, 0.0, 0.0]

    # structure.pitch_schedule = pitch_schedule
    # if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        # print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall)

    # CONTROLLER INITIALISATION
    use_controller=True
    controller = Controller(use_controller = use_controller)

    
    #%% RECORDERS    
    recorders = []
    recorders.append(mech_out_rotor_recorder(name="mech_out_rotor"))
    recorders.append(omega_recorder(name="omega"))
    recorders.append(pitch_recorder(name="pitch", blade_idx=0))
    recorders.append(generator_out_recorder(name="generator_out"))
    recorders.append(controller_recorder(name="integral_term"))
    

    #%% Set up simulation, run, and save wind recorder data1
    print(f"\nRunning simulation with parameters:\n")
    print(f"omega init = {omega_init:.2f} rad/s ")
    print(f"yaw = {yaw} degrees,")
    print(f"tilt = {tilt} degrees")
    print(f"shear_exp = {shear_exp}")
    print(f"V_hub={V_hub} m/s")
    print(f"use_dyn_wake = {use_dyn_wake}")
    print(f"use_dyn_stall = {use_dyn_stall}")
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

    power_mech = data["mech_out_rotor"]["power"]
    omega = data["omega"]["omega"]
    pitch = data["pitch"]["pitch"]
    power_gen = data["generator_out"]["power_gen"]
    integral_term = data["integral_term"]["pitch_i"]
    prev_integral_term = data["integral_term"]["prev_pitch_i"]
    gk = data["integral_term"]["gk"]

   
    #%% PLOTTING
    plot_flexible(
        x_val=t,
        y_values=[
            [power_mech/1e6, power_gen/1e6],
            [omega],
            [pitch],
            [integral_term, prev_integral_term],
            [gk]
        ],
        labels=[
            [r"$P_{mech}$", r"$P_{EL}$"],
            ["Rotor Speed"],
            ["Pitch Angle"],
            ["Controller Integral Term", "Previous integral term"],
            ["gk factor"]
        ],
        x_label="Time [s]",
        y_units=["Power [MW]", r"$\omega$ [rad/s]", r"$\theta$ [deg]", "Integral term", "GK factor"],
        save_name="controller_test",
        shear_exp=shear_exp)
   
    # plot_flexible(
    #         x_val=t,
    #         y_values=[
    #             [power_mech/1e6],
    #             [omega]                
    #         ],
    #         labels=[
    #             [r"P_{mech}"],
    #             ["Rotor Speed"]
    #         ],
    #         x_label="Time [s]",
    #         y_units=[["Power [MW]"], [r"\omega \frac{rad}{s}"]],
    #         save_name="pitch_test",
    #         shear_exp=shear_exp)

if do["sec_yaw_20deg_geo"]:
    
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.72
    yaw = 20
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt, pitch_init = [0, 0, 0])
    # radial distance index of evaluation
    print(structure.r)
    r_eval_idx = 57
    print(f"Radial distance at index {r_eval_idx}: {structure.r[r_eval_idx]}")

    # Wind parameters
    shear_exp = 0
    V_hub = 8
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
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
    T = 200
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    # def pitch_schedule(t):
    #     if t < 100:
    #         return [0.0, 0.0, 0.0]
    #     elif t < 150:
    #         return [2.0, 2.0, 2.0]
    #     else:
    #         return [0.0, 0.0, 0.0]

    # structure.pitch_schedule = pitch_schedule
    # if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        # print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall, use_wake_effects=use_wake_effects)

    # CONTROLLER INITIALISATION
    use_controller=True
    controller = Controller(tsr = 7.8, cp_max = 0.41, use_controller = use_controller)

    
    #%% RECORDERS    
    recorders = []
    recorders.append(mech_out_rotor_recorder(name="mech_out_rotor"))
    recorders.append(omega_recorder(name="omega"))
    recorders.append(pitch_recorder(name="pitch", blade_idx=0))
    recorders.append(generator_out_recorder(name="generator_out"))
    recorders.append(controller_recorder(name="integral_term"))
    recorders.append(w_5_recorder(name=f"w_5_yaw{yaw}_{use_wake_effects}", blade_idx=0, element_idx=r_eval_idx)) # induced wind at r=65m
    

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

    power_mech = data["mech_out_rotor"]["power"]
    omega = data["omega"]["omega"]
    pitch = data["pitch"]["pitch"]
    power_gen = data["generator_out"]["power_gen"]
    integral_term = data["integral_term"]["pitch_i"]
    prev_integral_term = data["integral_term"]["prev_pitch_i"]
    gk = data["integral_term"]["gk"]
    w_5 = data[f"w_5_yaw{yaw}_{use_wake_effects}"]["w_z"] # induced wind at r=65m, blade 0, z component

if do["sec_yaw_20deg_empirical"]:
    
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.72
    yaw = 20
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt, pitch_init = [0, 0, 0])
    # radial distance index of evaluation
    print(structure.r)
    r_eval_idx = 57
    print(f"Radial distance at index {r_eval_idx}: {structure.r[r_eval_idx]}")

    # Wind parameters
    shear_exp = 0
    V_hub = 8
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
    TI = 0

    # Tower parameters
    tower_effects = False

    # Aero parameters
    use_dyn_wake=True
    use_dyn_stall=True
    use_wake_effects = "empirical"

    # Simulation parameters
    N = 8
    # T = N * 2 * np.pi / omega_init
    T = 200
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    # def pitch_schedule(t):
    #     if t < 100:
    #         return [0.0, 0.0, 0.0]
    #     elif t < 150:
    #         return [2.0, 2.0, 2.0]
    #     else:
    #         return [0.0, 0.0, 0.0]

    # structure.pitch_schedule = pitch_schedule
    # if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        # print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall, use_wake_effects=use_wake_effects)

    # CONTROLLER INITIALISATION
    use_controller=True
    controller = Controller(tsr = 7.8, cp_max = 0.41, use_controller = use_controller)

    
    #%% RECORDERS    
    recorders = []
    recorders.append(mech_out_rotor_recorder(name="mech_out_rotor"))
    recorders.append(omega_recorder(name="omega"))
    recorders.append(pitch_recorder(name="pitch", blade_idx=0))
    recorders.append(generator_out_recorder(name="generator_out"))
    recorders.append(controller_recorder(name="integral_term"))
    recorders.append(w_5_recorder(name=f"w_5_yaw{yaw}_{use_wake_effects}", blade_idx=0, element_idx=r_eval_idx)) # induced wind at r=65m
    

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

    power_mech = data["mech_out_rotor"]["power"]
    omega = data["omega"]["omega"]
    pitch = data["pitch"]["pitch"]
    power_gen = data["generator_out"]["power_gen"]
    integral_term = data["integral_term"]["pitch_i"]
    prev_integral_term = data["integral_term"]["prev_pitch_i"]
    gk = data["integral_term"]["gk"]
    w_5 = data[f"w_5_yaw{yaw}_{use_wake_effects}"]["w_z"] # induced wind at r=65m, blade 0, z component
  


if do["sec_yaw_0deg"]:
    
    #%% SET UP SIMULATION
    # structural parameters
    omega_init = 0.72
    yaw = 0
    tilt = 0 

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt, pitch_init = [0, 0, 0])
    # radial distance index of evaluation
    print(structure.r)
    r_eval_idx = 57
    print(f"Radial distance at index {r_eval_idx}: {structure.r[r_eval_idx]}")

    # Wind parameters
    shear_exp = 0
    V_hub = 8
    # turbulence_box = MannTurbulenceBox(umean=V_hub, hub_height=structure.hub_height)
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
    T = 200
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = 0.1
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    # def pitch_schedule(t):
    #     if t < 100:
    #         return [0.0, 0.0, 0.0]
    #     elif t < 150:
    #         return [2.0, 2.0, 2.0]
    #     else:
    #         return [0.0, 0.0, 0.0]

    # structure.pitch_schedule = pitch_schedule
    # if hasattr(structure, 'pitch_schedule') and structure.pitch_schedule is not None:
        # print(f"Pitch schedule  (deg)= (t<100s, p= {pitch_schedule(0)} ) , (t<150s p={pitch_schedule(100)} ), (t>150s p={pitch_schedule(150)}) ")
    hub_height = structure.hub_height
    # Define wind with tower effect
    tower_radius = np.asarray(  # columns are [x, tower radius]
        [
            [0, structure.bot_thickness],
            [structure.hub_height, structure.top_thickness],
        ]
    )

    # WIND INITIALISATION
    if shear_exp != 0:
        print(f"Using shear wind with exponent {shear_exp}")
        wind_profile = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        wind_profile = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=wind_profile)
    else:
        print(f"Not including tower effects")
        # wind_profile = surrounding_wind
    if TI > 0:
        print(f"Including turbulence box")
        wind_profile = TurbWind(wind_profile, TI)
    else:
        print(f"Not including turbulence box")
        
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall, use_wake_effects=use_wake_effects)

    # CONTROLLER INITIALISATION
    use_controller=True
    controller = Controller(tsr = 7.8, cp_max = 0.41, use_controller = use_controller)

    
    #%% RECORDERS    
    recorders = []
    recorders.append(mech_out_rotor_recorder(name="mech_out_rotor"))
    recorders.append(omega_recorder(name="omega"))
    recorders.append(pitch_recorder(name="pitch", blade_idx=0))
    recorders.append(generator_out_recorder(name="generator_out"))
    recorders.append(controller_recorder(name="integral_term"))
    recorders.append(w_5_recorder(name=f"w_5_yaw{yaw}", blade_idx=0, element_idx=r_eval_idx)) # induced wind at r=65m
    

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

    power_mech = data["mech_out_rotor"]["power"]
    omega = data["omega"]["omega"]
    pitch = data["pitch"]["pitch"]
    power_gen = data["generator_out"]["power_gen"]
    integral_term = data["integral_term"]["pitch_i"]
    prev_integral_term = data["integral_term"]["prev_pitch_i"]
    gk = data["integral_term"]["gk"]
    w_5 = data[f"w_5_yaw{yaw}"]["w_z"] # induced wind at r=65m, blade 0, z component
    df_yaw20 = pd.read_csv("sim_data/w_5_yaw20.csv")
    w_5_yaw = df_yaw20["w_z"].values

if do["sec_yaw_plot"]:
    df_yaw20_geo = pd.read_csv("sim_data/w_5_yaw20_geometrical.csv")
    df_yaw20_empirical = pd.read_csv("sim_data/w_5_yaw20_empirical.csv")
    df_yaw0 = pd.read_csv("sim_data/w_5_yaw0.csv")

    t = df_yaw20_geo["time"].values
    w_5_yaw20_geo = df_yaw20_geo["w_z"].values
    w_5_yaw20_empirical = df_yaw20_empirical["w_z"].values
    w_5_yaw0 = df_yaw0["w_z"].values

    #%% PLOTTING
    yaw = 20
    r_pos = 58
    shear_exp = 0
    plot_flexible(
        x_val=t,
        y_values=[[-w_5_yaw20_geo, -w_5_yaw20_empirical, -w_5_yaw0]],  # one subplot, three curves
        labels=[[f"w_z, yaw={yaw}deg, geometrical", f"w_z, yaw=20deg, empirical", f"w_z, yaw=0deg"]],  # one subplot, three labels
        x_label="Time [s]",
        y_units=["Induced wind w_z [m/s]"],  # exactly one entry (one subplot)
        save_name=f"sec_yaw_at_r_{r_pos}m",
        shear_exp=shear_exp
    )
 