import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def plot_1_value(azimuth, value, label, y_unit, save_name, shear_exp, dyn_wake=True, dyn_stall=True, tower_effects=True, show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"

    plt.figure(figsize=(16,9))
    plt.scatter(azimuth, value, label=label)
    plt.xlabel("Azimuth [deg]")
    plt.ylabel(f"{y_unit}")
    plt.legend()
    # save figure to plots folder with name save_name
    if not dyn_wake:
        save_name += '_no_dyn_wake'
    if not dyn_stall:
        save_name += '_no_dyn_stall'
    plt.savefig(save_path / f"{save_name}.png")
    if show_plot:
        plt.show()

def plot_2_values(azimuth, value_1, value_2, label_1, label_2, y_unit, save_name, shear_exp, dyn_wake=True, dyn_stall=True, tower_effects=True, show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"
    # make the size fit a 16:9 aspect ratio
    plt.figure(figsize=(16,9))
    plt.plot(azimuth, value_1, label=label_1)
    plt.plot(azimuth, value_2, label=label_2)
    plt.xlabel("Azimuth [deg]")
    plt.ylabel(f"{y_unit}")
    plt.legend()
    # save figure to plots folder with name save_name
    if not dyn_wake:
        save_name += '_no_dyn_wake'
    if not dyn_stall:
        save_name += '_no_dyn_stall'
    plt.savefig(save_path / f"{save_name}.png")
    if show_plot:
        plt.show()

