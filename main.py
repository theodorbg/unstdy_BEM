import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from recorder import (
    blade_position_1_recorder,
    blade_velocity_5_recorder,
    wind_5_recorder,
    p_5_recorder,
    w_5_recorder,
    mech_out_recorder
)
from simulation import Simulation
from structure import RigidStructure
from wind import ConstantWind, ShearWind, WindWithTower, TurbWind
from aero import Aero
from plots import *

do = {
    "test": True
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
    TI = 0.2

    # Tower parameters
    tower_effects = False

    # Aero parameters
    use_dyn_wake=False
    use_dyn_stall=False

    # Simulation parameters
    N = 4
    T = N * 2 * np.pi / omega_init
    print(f"\nTotal simulation time: {T:.2f} seconds")
    dt = T/200 
    print(f"Time step: {dt:.4f} seconds, Number of steps: {int(T/dt)}")

    # PITCH SCHEDULE INITIALISATION
    def pitch_schedule(t):
        if t < 100:
            return [0.0, 0.0, 0.0]
        elif t < 150:
            return [2.0, 2.0, 2.0]
        else:
            return [0.0, 0.0, 0.0]

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
    
    recorders.append(wind_5_recorder(name="wind_5", blade_idx=0, element_idx=8)) # wind velocity
    recorders.append(w_5_recorder(name="w_5", blade_idx=0, element_idx=8)) # induced wind

    # make a recorder to record the velocity of the whole rotor plane
    
    
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

    #%% PLOTTING

    plot_flexible(t,
                    [v_u, v_v, v_w],
                    ["u", "v", "w"],
                    "Time [s]", ["m/s", "m/s", "m/s"],
                    "Wind_velocity_components_at_r_65m_time_series",
                    3,1,
                    shear_exp,
                    turb=TI)

    plot_psd_flexible(signals = [v_u, v_v, v_w],
                      labels = ["u", "v", "w"],
                      fs = 1/dt,
                      y_units = ["PSD (m/s)^2/Hz", "PSD (m/s)^2/Hz", "PSD (m/s)^2/Hz"],
                      save_name="psd_wind_velocity_components_at_r_65m",
                        subplots=3, values_per_subplot=1,
                      shear_exp=shear_exp, turb=TI,
                      omega = omega_init, dyn_wake=use_dyn_wake,
                        dyn_stall=use_dyn_stall, tower=tower_effects)


    # plot_flexible(azimuth,
    #               [u,v,w],
    #               ["V_u", "V_v", "V_w"],
    #               "Azimuth Position [degrees]",
    #               ["m/s", "m/s", "m/s"],
    #               "Wind_velocity_components_at_r_65m",
    #               3,1,
    #               shear_exp,
    #               turb=TI)
    
    
    # plot_flexible(azimuth,
    #                 [wy_5, wz_5],
    #                 ["w_y", "w_z"],
    #                 "Azimuth Position [degrees]",
    #                 ["m/s", "m/s"],
    #                 "Induced_velocity_components_at_r_65m",
    #                 2,1,
    #                 shear_exp,
    #                 turb=TI)

    # plot_flexible(t, [pz_5_8/1e3, total_thrust/1e6],
    #               ["p_z_r_65m", "total thrust"],
    #               "Time [s]", ["kN/m", "MN"],
    #               "p_z_and_total_thrust_time_series", 2,1,
    #               shear_exp,turb=TI,
    #               ylims=[[3.5, 6], [0.6, 0.85]],
    #               xlims=[50,130])
    
    # # plot the power spectrum
    # plot_psd_flexible(signals = [pz_5_8, total_thrust],
    #                   labels = ["p_z at r=65m", "total thrust"],
    #                   fs = 1/dt,
    #                   y_units = ["PSD (N/m)^2/Hz", "PSD (N)^2/Hz"],
    #                   save_name="psd_p_z_and_total_thrust",
    #                   subplots=2,
    #                   values_per_subplot=1,
    #                   shear_exp=shear_exp,
    #                   omega = omega_init,
    #                   nperseg=1024,
    #                   xlims=[0, 10],
                    #   turb=TI)
   