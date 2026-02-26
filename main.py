import matplotlib.pyplot as plt
import numpy as np

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
from wind import ConstantWind, ShearWind, WindWithTower
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

    # Wind parameters
    shear_exp = 0
    V_hub = 8

    # Tower parameters
    tower_effects = True
    

    # Aero parameters
    use_dyn_wake=True
    use_dyn_stall=True

    # Simulation parameters
    N = 15
    T = N * 2 * np.pi / omega_init
    dt = T / 200

    # STRUCTURE INITIALISATION
    structure = RigidStructure(omega_init, yaw=yaw, tilt=tilt)
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
        surrounding_wind = ShearWind(hub_height, V_hub, shear_exp)
    else:
        print(f"Using constant wind with V_hub={V_hub} m/s")
        surrounding_wind = ConstantWind(V_hub)
    if tower_effects:
        print(f"Including tower effects with tower radius {tower_radius} m")
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=surrounding_wind)
    else:
        print(f"Not including tower effects")
        wind_profile = surrounding_wind
    
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall)

    #%% RECORDERS
    # wind_recorder = wind_5_recorder("wind", blade_idx=0, element_idx=10)
    recorders = []
    # record spanwise loads for each blade element on blade 0
    for span_pos in range(len(structure.r)):
        p5_recorder = p_5_recorder(name=f"aero_{span_pos}", blade_idx=0, element_idx=span_pos)
        recorders.append(p5_recorder)
    
    # record thrust, torque, and power for each blade
    for blade_idx in range(structure.n_blades):
        recorders.append(mech_out_recorder(name=f"mech_out_blade_{blade_idx}", blade_idx=blade_idx))
    
    recorders.append(w_5_recorder(name="w_5", blade_idx=0, element_idx=10))
    
    # Set up simulation, run, and save wind recorder data
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

    #%% OUTPUT
    # Get data (saving above not needed for this) for plotting
    data = simulation.get_recorders()
    azimuth = data["time"] * omega_init / (2 * np.pi) * 360
    
    wy_5 = data["w_5"]["w_y"]
    wz_5 = data["w_5"]["w_z"]
    py_5_10 = data["aero_10"]["p_y"]
    pz_5_10 = data["aero_10"]["p_z"]

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
    # blade_data["thrust"] has shape (n_blades, n_steps)
    # blade_data["thrust"][0] is thrust for blade 0, etc.

    total_thrust = blade_data["thrust"].sum(axis=0)
    total_torque = blade_data["torque"].sum(axis=0)
    total_power  = blade_data["power"].sum(axis=0)

    # plot the thrust for each blade
    # plot_3_values(azimuth,
    #               blade_data["thrust"][0], blade_data["thrust"][0], blade_data["thrust"][0],
    #               "thrust blade 0", "thrust blade 1", "thrust blade 2",
    #               "Thrust [N]", "thrust_blades",
    #               shear_exp,
    #               use_dyn_wake,
    #               use_dyn_stall,
    #               tower_effects,
    #               )
    
    # # plot the torque for each blade
    # plot_3_values(azimuth,
    #               blade_data["torque"][0], blade_data["torque"][1], blade_data["torque"][2],
    #               "torque blade 0", "torque blade 1", "torque blade 2",
    #               "Torque [Nm]", "torque_blades",
    #               shear_exp,
    #               use_dyn_wake,
    #               use_dyn_stall,
    #               tower_effects,
    #               )
    
    # # plot the power for each blade
    # plot_3_values(azimuth,
    #               blade_data["power"][0], blade_data["power"][1], blade_data["power"][2],
    #               "power blade 0", "power blade 1", "power blade 2",
    #               "Power [W]", "power_blades",
    #               shear_exp,
    #               use_dyn_wake,
    #               use_dyn_stall,
    #               tower_effects,
    #               )
    
    # plot total thrust, torque, and power
    plot_1_value(azimuth, total_thrust,
                 "total thrust",
                 "Thrust [N]",
                 "total_thrust",
                 shear_exp,
                 use_dyn_wake,
                 use_dyn_stall,
                 tower_effects)
    
    plot_1_value(azimuth, total_torque, "total torque", "Torque [Nm]", "total_torque", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
    plot_1_value(azimuth, total_power, "total power", "Power [W]", "total_power", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
   
    # plot the spanwise load for element 10
    plot_2_values_blade_span(structure.r, py_avg, pz_avg, "p_y_avg", "p_z_avg", "N/m", "Blade_0_spanwise_loads", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
    # plot the induced wind for element 10
    # plot_2_values(azimuth, wy_5, wz_5, "w_y", "w_z", "m/s", "w_element_10", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)

    # plot_2_values(azimuth, w_y, w_z, "w_y", "w_z", "m/s",
    #               "w_induced_velocity", shear_exp, use_dyn_wake,
    #               use_dyn_stall, tower_effects)
    # # Plot aerodynamic load
    # plot_2_values(azimuth, p_y, p_z, "p_y", "p_z", "Nm/m", "p_spanwise_loads", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
    # Plot relative velocity
    # plot_2_values(azimuth, vrel_y, vrel_z, "vrel_y", "vrel_z", "m/s", "v_rel_relative_velocity", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
    # # plot quasi-steady induced velocity
    # plot_2_values(azimuth, w_qs_y, w_qs_z, "w_qs_y", "w_qs_z", "m/s", "w_qs_quasi_steady_induced_velocity", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
    # # plot v0
    # plot_2_values(azimuth, v0_y, v0_z, "v0_y", "v0_z", "m/s", "v0_undisturbed_velocity", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
   
# %%
