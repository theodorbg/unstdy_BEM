import matplotlib.pyplot as plt
import numpy as np

from recorder import (
    blade_position_1_recorder,
    blade_velocity_5_recorder,
    wind_5_recorder,
    aero_recorder        
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
    # structural parameters
    omega_init = 0.62  
    yaw = 0
    tilt = 0 

    # Wind parameters
    shear_exp = 0.2
    V_hub = 10

    # Tower parameters
    tower_effects = True
    

    # Aero parameters
    use_dyn_wake=True
    use_dyn_stall=True

    # Simulation parameters
    N = 10
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
        surrounding_wind = ShearWind(hub_height, V_hub, shear_exp)
    else:
        surrounding_wind = ConstantWind(V_hub)
    if tower_effects:
        wind_profile = WindWithTower(y_tower=0, z_tower=0, xa=tower_radius, surrounding_wind=surrounding_wind)
    else:
        wind_profile = surrounding_wind
    
    # AERO INITIALISATION
    aero = Aero(V_hub, use_dyn_wake=use_dyn_wake, use_dyn_stall=use_dyn_stall)

    # Define recorders
    aero_recorder = aero_recorder(name="aero", blade_idx=0, element_idx=10)
    # debug_aero_recorder = debug_aero_recorder(name="debug_aero", blade_idx=0, element_idx=10)
    recorders = [aero_recorder] 
    
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

    # Get data (saving above not needed for this) for plotting
    data = simulation.get_recorders()
    azimuth = data["time"]["values"] * omega_init / (2 * np.pi) * 360
     # Extract data from aero recorder
    w_y = data["aero"]["values"][:, 0]
    w_z = data["aero"]["values"][:, 1]
    p_y = data["aero"]["values"][:, 2]
    p_z = data["aero"]["values"][:, 3]
    
    
    # Plot induced velocity
    plot_2_values(azimuth, w_y, w_z, "w_y", "w_z", "m/s", "w_induced_velocity", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
    # Plot aerodynamic load
    # plot_2_values(azimuth, p_y, p_z, "p_y", "p_z", "Nm/m", "p_spanwise_loads", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
    # Plot relative velocity
    # plot_2_values(azimuth, vrel_y, vrel_z, "vrel_y", "vrel_z", "m/s", "v_rel_relative_velocity", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
    # # plot quasi-steady induced velocity
    # plot_2_values(azimuth, w_qs_y, w_qs_z, "w_qs_y", "w_qs_z", "m/s", "w_qs_quasi_steady_induced_velocity", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
    # # plot v0
    # plot_2_values(azimuth, v0_y, v0_z, "v0_y", "v0_z", "m/s", "v0_undisturbed_velocity", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
   