import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Global text size control
FONT_SIZE = 40
plt.rcParams.update({
    "font.size": FONT_SIZE,
    "axes.titlesize": FONT_SIZE,
    "axes.labelsize": FONT_SIZE,
    "xtick.labelsize": FONT_SIZE,
    "ytick.labelsize": FONT_SIZE,
    "legend.fontsize": 40,
    "figure.titlesize": FONT_SIZE,
})

def plot_1_value(azimuth, value, label, y_unit, save_name, shear_exp, dyn_wake=True, dyn_stall=True, tower_effects=True, turb=True, show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"

    plt.figure(figsize=(24,14))
    plt.plot(azimuth, value, label=label)
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

def plot_1_value_time(time, value, label, y_unit, save_name, shear_exp, dyn_wake=True, dyn_stall=True, tower_effects=True, turb=True, show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"

    plt.figure(figsize=(24,14))
    plt.plot(time, value, label=label)
    # create vertical lines at t=100s and t=150s
    plt.axvline(x=100, color='gray', linestyle='--', label='t=100s')
    plt.axvline(x=150, color='red', linestyle='--', label='t=150s')
    plt.xlabel("Time [s]")
    plt.ylabel(f"{y_unit}")
    plt.xlim(50, 250)
    plt.ylim(1,1.5)
    plt.legend()
    # save figure to plots folder with name save_name
    if not dyn_wake:
        save_name += '_no_dyn_wake'
    if not dyn_stall:
        save_name += '_no_dyn_stall'
    plt.savefig(save_path / f"{save_name}.png")
    if show_plot:
        plt.show()

def plot_1_value_time_2subplots(time,
                                 value_1, value_2,
                                 label_1, label_2,
                                 y_unit_1, y_unit_2,
                                 save_name, shear_exp,
                                 dyn_wake=True, dyn_stall=True, tower_effects=True, turb=True, show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(32, 18), sharex=True)

    ax1.plot(time, value_1, label=label_1)
    # ax1.axvline(x=100, color='gray', linestyle='--', label='t=100s')
    # ax1.axvline(x=150, color='red', linestyle='--', label='t=150s')
    ax1.set_ylabel(f"{y_unit_1}")
    # ax1.set_xlim(50, 250)
    # ax1.set_ylim(-0.27, -0.33)
    ax1.legend()

    ax2.plot(time, value_2, label=label_2)
    # ax2.axvline(x=100, color='gray', linestyle='--', label='t=100s')
    # ax2.axvline(x=150, color='red', linestyle='--', label='t=150s')
    ax2.set_ylabel(f"{y_unit_2}")
    ax2.set_xlabel("Time [s]")
    # ax2.set_xlim(50, 250)
    # ax2.set_ylim(-2.3, -3)
    ax2.legend()

    plt.tight_layout()

    if not turb:
        save_name += '_no_turbulence'
    if not dyn_wake:
        save_name += '_no_dyn_wake'
    if not dyn_stall:
        save_name += '_no_dyn_stall'
    plt.savefig(save_path / f"{save_name}.png")
    if show_plot:
        plt.show()



def plot_2_values(azimuth, value_1, value_2, label_1, label_2, y_unit, save_name, shear_exp, dyn_wake=True, dyn_stall=True, tower_effects=True, turb=True, show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"
    # make the size fit a 16:9 aspect ratio
    plt.figure(figsize=(24,14))
    plt.plot(azimuth, value_1, label=label_1)
    plt.plot(azimuth, value_2, label=label_2)
    plt.ylim(0.25, 1.05)
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


def plot_2_values_time(time, value_1, value_2, label_1, label_2, y_unit, save_name, shear_exp, dyn_wake=True, dyn_stall=True, tower_effects=True, turb=True, show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"
    # make the size fit a 16:9 aspect ratio
    plt.figure(figsize=(24,14))
    plt.plot(time, value_1, label=label_1)
    plt.plot(time, value_2, label=label_2)
    # plt.ylim(0.25, 1.05)
    plt.xlabel("Time [s]")
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

def plot_6_subplots_time(time,
                  value_1, value_2, value_3,
                  value_4, value_5, value_6,
                  label_1, label_2, label_3,
                  label_4, label_5, label_6,
                  y_unit_1, y_unit_2, y_unit_3,
                  y_unit_4, y_unit_5, y_unit_6,
                  save_name, shear_exp,
                  ylim_1=None, ylim_2=None, ylim_3=None,
                  ylim_4=None, ylim_5=None, ylim_6=None,
                  dyn_wake=True, dyn_stall=True, tower_effects=True, turb=True, show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"
    if not turb:
        save_name += "_no_turbulence"

    fig, axes = plt.subplots(6, 1, figsize=(36, 64), sharex=True)
    ax1, ax2, ax3, ax4, ax5, ax6 = axes

    values  = [value_1,  value_2,  value_3,  value_4,  value_5,  value_6]
    labels  = [label_1,  label_2,  label_3,  label_4,  label_5,  label_6]
    y_units = [y_unit_1, y_unit_2, y_unit_3, y_unit_4, y_unit_5, y_unit_6]
    ylims   = [ylim_1,   ylim_2,   ylim_3,   ylim_4,   ylim_5,   ylim_6]

    for ax, value, label, y_unit, ylim in zip(axes, values, labels, y_units, ylims):
        ax.plot(time, value, label=label)
        ax.axvline(x=100, color='gray', linestyle='--', label='t=100s')
        ax.axvline(x=150, color='red',  linestyle='--', label='t=150s')
        ax.set_ylabel(f"{y_unit}")
        ax.set_xlim(50, 250)
        if ylim is not None:
            ax.set_ylim(ylim[0], ylim[1])
        ax.legend()

    axes[-1].set_xlabel("Time [s]")
    plt.tight_layout()

    if not dyn_wake:
        save_name += '_no_dyn_wake'
    if not dyn_stall:
        save_name += '_no_dyn_stall'
    if not turb:
        save_name += '_no_turbulence'
    plt.savefig(save_path / f"{save_name}.png")
    if show_plot:
        plt.show()



def plot_3_values(azimuth,
                  value_1, value_2, value_3,
                  label_1, label_2, label_3,
                  y_unit, save_name,
                  shear_exp,
                  dyn_wake=True,
                  dyn_stall=True,
                  tower_effects=True,
                  turb=True,
                  show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"
    if not turb:
        save_name += "_no_turbulence"   
    # make the size fit a 16:9 aspect ratio
    plt.figure(figsize=(24,14))
    plt.plot(azimuth, value_1, label=label_1)
    plt.plot(azimuth, value_2, label=label_2)
    plt.plot(azimuth, value_3, label=label_3)
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

def plot_4_values(azimuth,
                  value_1, value_2, value_3, value_4,
                  label_1, label_2, label_3, label_4,
                  y_unit, save_name,
                  shear_exp,
                  dyn_wake=True,
                  dyn_stall=True,
                  tower_effects=True,
                  turb=True,
                  show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"
    if not turb:
        save_name += "_no_turbulence"
    # make the size fit a 16:9 aspect ratio
    plt.figure(figsize=(24,14))
    plt.plot(azimuth, value_1, label=label_1)
    plt.plot(azimuth, value_2, label=label_2)
    plt.plot(azimuth, value_3, label=label_3)
    plt.plot(azimuth, value_4, label=label_4)
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

def plot_4_values_2subplots(azimuth,
                             value_1, value_2, value_3, value_4,
                             value_5, value_6, value_7, value_8,
                             label_1, label_2, label_3, label_4,
                             label_5, label_6, label_7, label_8,
                             y_unit_1, y_unit_2, save_name,
                             shear_exp,
                             dyn_wake=True,
                             dyn_stall=True,
                             tower_effects=True,
                             turb=True, 
                             show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"
    if not turb:
        save_name += "_no_turbulence"

    # make the size fit a 16:9 aspect ratio with 2 stacked subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(24, 14), sharex=True)

    ax1.plot(azimuth, value_1, label=label_1)
    ax1.plot(azimuth, value_2, label=label_2)
    ax1.plot(azimuth, value_3, label=label_3)
    ax1.plot(azimuth, value_4, label=label_4)
    ax1.set_ylabel(f"{y_unit_1}")
    ax1.legend()

    ax2.plot(azimuth, value_5, label=label_5)
    ax2.plot(azimuth, value_6, label=label_6)
    ax2.plot(azimuth, value_7, label=label_7)
    ax2.plot(azimuth, value_8, label=label_8)
    ax2.set_ylabel(f"{y_unit_2}")
    ax2.set_xlabel("Azimuth [deg]")
    ax2.legend()

    plt.tight_layout()

    # save figure to plots folder with name save_name
    if not dyn_wake:
        save_name += '_no_dyn_wake'
    if not dyn_stall:
        save_name += '_no_dyn_stall'
    plt.savefig(save_path / f"{save_name}.png")
    if show_plot:
        plt.show()

def plot_4_values_2subplots_time(time,
                             value_1, value_2, value_3, value_4,
                             value_5, value_6, value_7, value_8,
                             label_1, label_2, label_3, label_4,
                             label_5, label_6, label_7, label_8,
                             y_unit_1, y_unit_2, save_name,
                             shear_exp,
                             dyn_wake=True,
                             dyn_stall=True,
                             tower_effects=True,
                             show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"

    # make the size fit a 16:9 aspect ratio with 2 stacked subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(24, 14), sharex=True)

    ax1.plot(time, value_1, label=label_1)
    ax1.plot(time, value_2, label=label_2)
    ax1.plot(time, value_3, label=label_3)
    ax1.plot(time, value_4, label=label_4)
    ax1.set_ylabel(f"{y_unit_1}")
    ax1.legend()

    ax2.plot(time, value_5, label=label_5)
    ax2.plot(time, value_6, label=label_6)
    ax2.plot(time, value_7, label=label_7)
    ax2.plot(time, value_8, label=label_8)
    ax2.set_ylabel(f"{y_unit_2}")
    ax2.set_xlabel("Time [s]")
    ax2.legend()

    plt.tight_layout()

    # save figure to plots folder with name save_name
    if not dyn_wake:
        save_name += '_no_dyn_wake'
    if not dyn_stall:
        save_name += '_no_dyn_stall'
    plt.savefig(save_path / f"{save_name}.png")
    if show_plot:
        plt.show()


def plot_2_values_blade_span(span_positions, value_1, value_2, label_1, label_2, y_unit, save_name, shear_exp, dyn_wake=True, dyn_stall=True, tower_effects=True, show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"
    # make the size fit a 16:9 aspect ratio
    plt.figure(figsize=(24,14))
    plt.plot(span_positions, value_1, label=label_1)
    plt.plot(span_positions, value_2, label=label_2)
    plt.xlabel("Blade span position [m]")
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




def plot_2_values_blade_span_subplots(span_positions, value_1, value_2, value_3, value_4, label_1, label_2, label_3, label_4, y_unit_1, y_unit_2, save_name, shear_exp, dyn_wake=True, dyn_stall=True, tower_effects=True, show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"

    # make the size fit a 16:9 aspect ratio with 2 stacked subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(24, 14), sharex=True)

    ax1.plot(span_positions, value_1, label=label_1)
    ax1.plot(span_positions, value_2, label=label_2)
    ax1.set_ylabel(f"{y_unit_1}")
    ax1.legend()

    ax2.plot(span_positions, value_3, label=label_3)
    ax2.plot(span_positions, value_4, label=label_4)
    ax2.set_ylabel(f"{y_unit_2}")
    ax2.set_xlabel("Blade span position [m]")
    ax2.legend()

    plt.tight_layout()

    # save figure to plots folder with name save_name
    if not dyn_wake:
        save_name += '_no_dyn_wake'
    if not dyn_stall:
        save_name += '_no_dyn_stall'
    plt.savefig(save_path / f"{save_name}.png")
    if show_plot:
        plt.show()





def plot_3_subplots(azimuth,
                  value_1, value_2, value_3,
                  label_1, label_2, label_3,
                  y_unit, save_name,
                  shear_exp,
                  dyn_wake=True,
                  dyn_stall=True,
                  tower_effects=True,
                  show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"
    # make the size fit a 16:9 aspect ratio
    plt.figure(figsize=(24,14))
    plt.plot(azimuth, value_1, label=label_1)
    plt.plot(azimuth, value_2, label=label_2)
    plt.plot(azimuth, value_3, label=label_3)
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


def plot_3_subplots_time(time,
                         
                  value_1, value_2, value_3,
                  label_1, label_2, label_3,
                  y_unit, save_name,
                  shear_exp,
                  dyn_wake=True,
                  dyn_stall=True,
                  tower_effects=True,
                  show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"
    # make the size fit a 16:9 aspect ratio
    plt.figure(figsize=(24,14))
    plt.plot(time, value_1, label=label_1)
    plt.plot(time, value_2, label=label_2)
    plt.plot(time, value_3, label=label_3)
    plt.xlabel("Time [s]")
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

def plot_3_subplots_time_2subplots(time,
                                   
                  value_1, value_2, value_3,
                  value_4, value_5, value_6,
                  label_1, label_2, label_3,
                  label_4, label_5, label_6,
                  y_unit_1, y_unit_2, save_name,
                  shear_exp,
                  dyn_wake=True,
                  dyn_stall=True,
                  tower_effects=True,
                  show_plot=False):

    # create folder if it doesn't exist
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)
    save_name += f"_shear_{shear_exp}"
    if not tower_effects:
        save_name += "_no_tower_effects"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(24, 14), sharex=True)

    ax1.plot(time, value_1, label=label_1)
    ax1.plot(time, value_2, label=label_2)
    ax1.plot(time, value_3, label=label_3)
    ax1.set_ylabel(f"{y_unit_1}")
    ax1.legend()

    ax2.plot(time, value_4, label=label_4)
    ax2.plot(time, value_5, label=label_5)
    ax2.plot(time, value_6, label=label_6)
    ax2.set_ylabel(f"{y_unit_2}")
    ax2.set_xlabel("Time [s]")
    ax2.legend()

    plt.tight_layout()

    if not dyn_wake:
        save_name += '_no_dyn_wake'
    if not dyn_stall:
        save_name += '_no_dyn_stall'
    plt.savefig(save_path / f"{save_name}.png")
    if show_plot:
        plt.show()


def plot_flexible(
    x_val,
    y_values,
    labels,
    x_label,
    y_units,
    save_name,
    subplots,
    values_per_subplot,
    shear_exp,
    ylims=None,
    xlims=None,
    dyn_wake=True,
    dyn_stall=True,
    tower=True,
    turb=True,
    show_plot=False,
):
    # --- normalize values_per_subplot ---
    if isinstance(values_per_subplot, int):
        values_per_subplot = [values_per_subplot] * subplots

    # --- auto-wrap flat lists into nested lists ---
    # if user passes [u, v, w] with subplots=3, values_per_subplot=1
    # wrap each element: [[u], [v], [w]]
    if not isinstance(y_values[0], (list, np.ndarray)) or (
        isinstance(y_values[0], np.ndarray) and y_values[0].ndim == 1 and len(y_values) == subplots
    ):
        y_values = [[y] for y in y_values]

    if not isinstance(labels[0], list):
        labels = [[l] for l in labels]

    # --- validate inputs ---
    assert len(y_values) == subplots,  "y_values must have one list per subplot"
    assert len(labels)   == subplots,  "labels must have one list per subplot"
    assert len(y_units)  == subplots,  "y_units must have one entry per subplot"

    if ylims is None:
        ylims = [None] * subplots
    assert len(ylims) == subplots, "ylims must have one entry per subplot (or None)"
    assert len(values_per_subplot) == subplots, "values_per_subplot must match number of subplots"

    # --- create folder ---
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)

    # --- build save name ---
    save_name += f"_shear_{shear_exp}"
    if not tower:
        save_name += "_no_tower"
    if not turb:
        save_name += "_no_turbulence"
    if not dyn_wake:
        save_name += "_no_dyn_wake"
    if not dyn_stall:
        save_name += "_no_dyn_stall"

    # --- plot ---
    fig, axes = plt.subplots(subplots, 1, figsize=(32, 9 * subplots), sharex=True)
    if subplots == 1:
        axes = [axes]

    for ax, y_list, label_list, y_unit, ylim in zip(axes, y_values, labels, y_units, ylims):
        for y, label in zip(y_list, label_list):
            ax.plot(x_val, y, label=label)
        ax.set_ylabel(y_unit)
        ax.legend()
        if ylim is not None:
            ax.set_ylim(ylim[0], ylim[1])

    if xlims is not None:
        axes[0].set_xlim(xlims[0], xlims[1])  # shared x axis, only need to set once

    axes[-1].set_xlabel(x_label)
    plt.tight_layout()
    plt.savefig(save_path / f"{save_name}.png")
    if show_plot:
        plt.show()
    plt.close()

def plot_psd_flexible(
    signals,
    labels,
    fs,
    y_units,
    save_name,
    subplots,
    values_per_subplot,
    shear_exp,
    omega,
    ylims=None,
    xlims=None,
    nperseg=1024,
    dyn_wake=True,
    dyn_stall=True,
    tower=True,
    turb=True,
    show_plot=False,
):
    from scipy import signal as scipy_signal

    # --- cast bools ---
    turb      = bool(turb)
    tower     = bool(tower)
    dyn_wake  = bool(dyn_wake)
    dyn_stall = bool(dyn_stall)

    # --- normalize values_per_subplot ---
    if isinstance(values_per_subplot, int):
        values_per_subplot = [values_per_subplot] * subplots

    # --- auto-wrap flat lists into nested lists ---
    if not isinstance(signals[0], (list, np.ndarray)) or (
        isinstance(signals[0], np.ndarray) and signals[0].ndim == 1 and len(signals) == subplots
    ):
        signals = [[s] for s in signals]

    if not isinstance(labels[0], list):
        labels = [[l] for l in labels]

    # --- validate inputs ---
    assert len(signals) == subplots, "signals must have one list per subplot"
    assert len(labels)  == subplots, "labels must have one list per subplot"
    assert len(y_units) == subplots, "y_units must have one entry per subplot"

    if ylims is None:
        ylims = [None] * subplots
    assert len(ylims) == subplots, "ylims must have one entry per subplot (or None)"
    assert len(values_per_subplot) == subplots, "values_per_subplot must match number of subplots"

    # --- create folder ---
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)

    # --- build save name ---
    save_name += f"_psd_shear_{shear_exp}"
    if not tower:
        save_name += "_no_tower"
    if not turb:
        save_name += "_no_turbulence"
    if not dyn_wake:
        save_name += "_no_dyn_wake"
    if not dyn_stall:
        save_name += "_no_dyn_stall"

    # --- plot ---
    fig, axes = plt.subplots(subplots, 1, figsize=(32, 9 * subplots), sharex=True)
    if subplots == 1:
        axes = [axes]

    for ax, sig_list, label_list, y_unit, ylim in zip(axes, signals, labels, y_units, ylims):
        for sig, label in zip(sig_list, label_list):
            f, Pxx = scipy_signal.welch(sig, fs, nperseg=nperseg)
            f_norm = f * 2 * np.pi / omega  # normalise: 1P = 1, 3P = 3, etc.
            ax.semilogy(f_norm, Pxx, label=label)

        # add vertical lines at 1P, 3P, 6P
        for n, style in zip([1, 3, 6, 9], ['--', '-.', ':', '-']):
            ax.axvline(x=n, color='gray', linestyle=style, alpha=0.7)

        # force integer ticks on x axis
        ax.xaxis.set_major_locator(plt.MultipleLocator(1))
        
        ax.set_ylabel(y_unit)
        ax.legend()
        if ylim is not None:
            ax.set_ylim(ylim[0], ylim[1])

    if xlims is not None:
        axes[0].set_xlim(xlims[0], xlims[1])

    axes[-1].set_xlabel("Frequency [1P rotational frequency]")
    plt.tight_layout()
    plt.savefig(save_path / f"{save_name}.png")
    if show_plot:
        plt.show()
    plt.close()

