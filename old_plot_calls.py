 # plt.psd(py_5_8, =1024, Fs=1/(t[1]-t[0]))


    # plot_1_value_time_2subplots(t, blade_data["power"][0]/1e6, total_power/1e6, 
    #                             "power blade 0", "total power",
    #                             "Power [MW]", "Power [MW]", "power_blade0_and_total_power",
    #                             shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)

    # plot_1_value_time_2subplots(t, blade_data["thrust"][0]/1e6, total_thrust/1e6, 
    #                             "thrust blade 0", "total thrust",
    #                             "Thrust [MN]", "Thrust [MN]", "thrust_blade0_and_total_thrust",
    #                             shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)


    # plot_1_value_time(t, blade_data["power"][0]/1e6, 
    #                     "power blade 0",
    #                     "Power [MW]", "power_blade_0",
    #                     shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)

    # plot_2_values_blade_span(structure.r, py_avg, stdy_py, "unsteady", "steady", "N/m", "Blade_0_spanwise_loads_comparison_py_1", shear_exp)
    # plot_2_values_blade_span(structure.r, pz_avg, stdy_pz, "unsteady", "steady", "N/m", "Blade_0_spanwise_loads_comparison_pz_1", shear_exp)
    # combine them in one plot with two subplots
    # plot_2_values_blade_span_subplots(structure.r, py_avg, stdy_py, pz_avg, stdy_pz, "unsteady py", "steady py", "unsteady pz", "steady pz", "N/m", "N/m", "Blade_0_spanwise_loads_comparison_subplots_1", shear_exp)
    # # plot the thrust for each blade
    # plot_4_values(azimuth,
    #               1/1e6*blade_data["thrust"][0], 1/1e6*blade_data["thrust"][1], 1/1e6*blade_data["thrust"][2], 1/1e6*total_thrust,
    #               "thrust blade 0", "thrust blade 1", "thrust blade 2", "total thrust",
    #               "Thrust [MN]", "thrust_blades",
    #               shear_exp,
    #               )
    
    # plot_4_values_2subplots(azimuth,
    #                           1/1e6*blade_data["thrust"][0], 
    #                           1/1e6*blade_data["thrust"][1], 
    #                           1/1e6*blade_data["thrust"][2], 
    #                           1/1e6*total_thrust,
    #                           1/1e6*blade_data["power"][0], 
    #                           1/1e6*blade_data["power"][1], 
    #                           1/1e6*blade_data["power"][2], 
    #                           1/1e6*total_power,
    #                           "thrust blade 0", 
    #                           "thrust blade 1", 
    #                           "thrust blade 2", 
    #                           "total thrust",
    #                           "power blade 0",
    #                            "power blade 1", 
    #                            "power blade 2", 
    #                            "total power",
    #                            "MN", "MW",
    #                           "thrust_and_power_blades",
    #                             shear_exp)
    # # # plot the torque for each blade
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
    # plot_4_values(azimuth,
                #   1/1e6*blade_data["power"][0], 1/1e6*blade_data["power"][1], 1/1e6*blade_data["power"][2], 1/1e6*total_power,
                #   "power blade 0", "power blade 1", "power blade 2", "total power",
                #   "Power [MW]", "power_blades",
                #   shear_exp,
                #   use_dyn_wake,
                #   use_dyn_stall,
                #   tower_effects,
                #   )
    
    # plot total thrust, torque, and power
    # plot_1_value(azimuth, total_thrust_normalized,
    #              "total thrust normalized",
    #              "Thrust [N]",
    #              "total_thrust_normalized",
    #              shear_exp,
    #              use_dyn_wake,
    #              use_dyn_stall,
    #              tower_effects)
    
    # plot_1_value(azimuth, total_torque_normalized, "total torque normalized", "Torque [Nm]", "total_torque_normalized", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
    # plot_1_value(azimuth, total_power_normalized, "total power normalized", "Power [W]", "total_power_normalized", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
   
    # plot the thrust and power normalized together
    # plot_2_values(azimuth, total_thrust_normalized, total_power_normalized, "total thrust normalized", "total power normalized", "N and W", "total_thrust_and_power_normalized", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)

    # plot the spanwise load for element 10
    # plot_2_values_blade_span(structure.r, py_avg_normalized, pz_avg_normalized, "p_y_avg_normalized", "p_z_avg_normalized", "N/m", "Blade_0_spanwise_loads_normalized", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
    # plot the induced wind for element 10
    # plot_2_values_time(t, wy_5/np.max(wy_5), wz_5/np.max(wz_5), "w_y normalized", "w_z normalized", "m/s", "w_element_8", shear_exp, use_dyn_wake, use_dyn_stall, tower_effects)
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
    
    # plot_1_value(azimuth,
    #               v_w,
    #               "w",
    #               "m/s",
    #               "wind_velocity_w",
    #               shear_exp)

    # plot_6_subplots_time(t,
    #                      induced_velocities["w_y"][0],
    #                      induced_velocities["w_z"][0],
    #                      blade_data["power"][0]/1e6,
    #                      total_power/1e6,
    #                      blade_data["thrust"][0]/1e6,
    #                      total_thrust/1e6,
    #                      "w_y blade 0", "w_z blade 0",
    #                      "power blade 0", "total power",
    #                      "thrust blade 0", "total thrust",
    #                      "m/s", "m/s", "MW", "MW", "MN", "MN",
    #                      "w_power_thrust_blade0_and_total",
    #                      shear_exp,
    #                      dyn_wake=use_dyn_wake,
    #                      dyn_stall=use_dyn_stall)
    # #[-0.27, -0.33],
    #                     #  [-2.3, -3.1],
    #                     #  [1.0, 1.6],
    #                     #  [2.8, 4.8],
    #                     #  [0.22, 0.32],
    #                     #  [0.6, 1.0],

        # plot_1_value_time_2subplots(t,
    #                             induced_velocities["w_y"][0],
    #                             induced_velocities["w_z"][0],
    #                             "w_y blade 0", "w_z blade 0",
    #                             "m/s", "m/s",
    #                             "induced_velocities_blade_0",
    #                             shear_exp)

    # plot_3_subplots_time_2subplots(t,
    #                                induced_velocities["w_y"][0],
    #                                induced_velocities["w_y"][1],
                                #    induced_velocities["w_y"][2],
                                #    induced_velocities["w_z"][0],
                                #    induced_velocities["w_z"][1],
                                #    induced_velocities["w_z"][2],
                                #    "w_y blade 0", "w_y blade 1", "w_y blade 2",
                                #    "w_z blade 0", "w_z blade 1", "w_z blade 2",
                                #    "m/s", "m/s",
                                #    "induced_velocities_all_blades_y_z",
                                #    shear_exp,
                                #    )

