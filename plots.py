import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from pathlib import Path


# Global text size control
FONT_SIZE = 40
# Default line styles and widths to cycle through
# LINE_STYLES = ['-', '--', '-.', ':']
LINE_STYLES = [':']
LINE_WIDTH  = 8
plt.rcParams.update({
    "font.size": FONT_SIZE,
    "axes.titlesize": FONT_SIZE,
    "axes.labelsize": FONT_SIZE,
    "xtick.labelsize": FONT_SIZE,
    "ytick.labelsize": FONT_SIZE,
    "legend.fontsize": 40,
    "figure.titlesize": FONT_SIZE,
    "axes.grid": True,
    "axes.grid.which": "both",      # <-- ADD: enable both major and minor
    "grid.alpha": 0.8,
    "grid.linestyle": "--",
    "xtick.minor.visible": True,    # <-- ADD
    "ytick.minor.visible": True,
    "axes.ymargin": 0.1
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

    ax1.plot(span_positions, value_1, label=label_1, linewidth = 6)
    ax1.plot(span_positions, value_2, label=label_2, linewidth = 6)
    ax1.set_ylabel(f"{y_unit_1}")
    ax1.legend()

    ax2.plot(span_positions, value_3, label=label_3, linewidth = 6)
    ax2.plot(span_positions, value_4, label=label_4, linewidth = 6)
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
    x_val: np.ndarray,
    y_values: list,
    labels: list,
    x_label: str,
    y_units: list,
    save_name: str,
    shear_exp = float,
    ylims=None,
    xlims=None,
    fig_size = 32,
    vlines=None,          # e.g. [{"x": 100, "color": "gray", "linestyle": "--", "label": "t=100s"}, ...]
    dyn_wake=True,
    dyn_stall=True,
    tower=True,
    turb=0,
    show_plot=False):
    """
    Plotting function that can handle multiple subplots and multiple lines per subplot, with flexible input formats.

    Parameters:
    - x_val: 1D array of x values (shared across all subplots)
    - y_values: list of lists of y values, one list per subplot. Each inner list can contain multiple lines to plot on that subplot.
    - labels: list of lists of labels, matching the structure of y_values
    - x_label: label for the x axis (shared across all subplots)
    - y_units: list of y axis labels, one per subplot
    - save_name: base name for saving the plot (without extension)
    - shear_exp: shear exponent value to include in the save name
    - ylims: list of (min, max) tuples for y axis limits, one per subplot
    - xlims: list of (min, max) tuples for x axis limits, one per subplot
    - vlines: list of dictionaries for vertical lines
        # e.g. [{"x": 100, "color": "gray", "linestyle": "--", "label": "t=100s"}, ...]
    - dyn_wake, dyn_stall, tower, turb: booleans to control which features are included in the save name
    - dyn_stall: whether to include dynamic stall effects in the save name
    - tower: whether to include tower effects in the save name
    - turb: whether to include turbulence effects in the save name
    - show_plot: whether to display the plot after saving
    """
    subplots = len(y_values)
    values_per_subplot = [len(y) for y in y_values]
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
    if not dyn_wake:
        save_name += "_no_dyn_wake"
    if not dyn_stall:
        save_name += "_no_dyn_stall"
    save_name += f"_turb_{turb}"

    # --- plot ---
    fig, axes = plt.subplots(subplots, 1, figsize=(fig_size, 9 * subplots), sharex=True)
    if subplots == 1:
        axes = [axes]

    for ax, y_list, label_list, y_unit, ylim in zip(axes, y_values, labels, y_units, ylims):
        for i, (y, label) in enumerate(zip(y_list, label_list)):
            ax.plot(x_val, y, label=label,
                    linewidth=LINE_WIDTH,
                    linestyle=LINE_STYLES[i % len(LINE_STYLES)])
        if vlines is not None:
            for vline in vlines:
                ax.axvline(
                    x=vline["x"],
                    color=vline.get("color", "gray"),
                    linestyle=vline.get("linestyle", "--"),
                    linewidth=vline.get("linewidth", LINE_WIDTH),
                    alpha=vline.get("alpha", 1.0),
                    label=vline.get("label", None),
                )
        ax.set_ylabel(y_unit)
        ax.legend()
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=8))
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))   # <-- ADD THIS
        ax.minorticks_on()                                        # <-- ADD THIS
        ax.grid(True, which='major', alpha=1, linestyle='--')
        ax.grid(True, which='minor', alpha=0.5, linestyle=':')   # lower alpha for minor
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

# ...existing code...
# ...existing code...
def plot_psd_flexible(
    signals: list,
    labels: list,
    fs: float,
    y_units: list,
    save_name: str,
    shear_exp: float,
    omega: float,
    ylims=None,
    xlims=None,
    nperseg=1024,
    dyn_wake=True,
    dyn_stall=True,
    tower=True,
    turb=0,
    vlines=None,          # e.g. [{"x": 1, "color": "red", "linestyle": "--", "label": "1P"}, ...]
    show_plot=False):
    """
    Plotting function that can handle multiple subplots and multiple lines per subplot, with flexible input formats.

    Parameters:
    - signals: list of lists of signals, one list per subplot
    - labels: list of lists of labels, matching the structure of signals
    - fs: sampling frequency for PSD calculation
    - y_units: list of y axis labels, one per subplot
    - save_name: base name for saving the plot (without extension)
    - shear_exp: shear exponent value to include in the save name
    - omega: rotational frequency for normalizing the x axis of the PSD plot
    - ylims: list of (min, max) tuples for y axis limits, one per subplot
    - xlims: list of (min, max) tuples for x axis limits, one per subplot
    - nperseg: number of samples per segment for Welch's method
    - dyn_wake, dyn_stall, tower, turb: booleans to control which features are included in the save name
    - vlines: list of dicts for custom vertical lines, e.g.:
        [{"x": 1, "color": "red", "linestyle": "--", "label": "1P", "linewidth": 1.5, "alpha": 0.7}]
        If None, defaults to vertical lines at 1P, 3P, 6P, 9P in gray.
    - show_plot: whether to display the plot after saving
    """
    from scipy import signal as scipy_signal

    subplots = len(signals)
    values_per_subplot = [len(s) for s in signals]

    # --- cast bools ---
    tower     = bool(tower)
    dyn_wake  = bool(dyn_wake)
    dyn_stall = bool(dyn_stall)

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

    # --- create folder ---
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)

    # --- build save name ---
    save_name += f"_psd_shear_{shear_exp}"
    if not tower:
        save_name += "_no_tower"
    if not dyn_wake:
        save_name += "_no_dyn_wake"
    if not dyn_stall:
        save_name += "_no_dyn_stall"
    save_name += f"_turb_{turb}"
    # --- plot ---
    fig, axes = plt.subplots(subplots, 1, figsize=(32, 9 * subplots), sharex=True)
    if subplots == 1:
        axes = [axes]

    for ax, sig_list, label_list, y_unit, ylim in zip(axes, signals, labels, y_units, ylims):
        for i, (sig, label) in enumerate(zip(sig_list, label_list)):
            nperseg_actual = min(nperseg, len(sig))
            f, Pxx = scipy_signal.welch(sig, fs, nperseg=nperseg_actual)
            f_norm = f * 2 * np.pi / omega
            ax.semilogy(f_norm, Pxx, label=label,
                        linewidth=LINE_WIDTH,
                        linestyle=LINE_STYLES[i % len(LINE_STYLES)])

        if vlines is not None:
            for vline in vlines:
                ax.axvline(
                    x=vline["x"],
                    color=vline.get("color", "gray"),
                    linestyle=vline.get("linestyle", "--"),
                    linewidth=vline.get("linewidth", 1.5),
                    alpha=vline.get("alpha", 0.7),
                    label=vline.get("label", None),
                )
        else:
            for n, style in zip([1, 3, 6, 9], ['--', '-.', ':', '-']):
                ax.axvline(x=n, color='gray', linestyle=style, linewidth=1.5, alpha=0.7)

        ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.grid(True, which='major', alpha=1, linestyle='--')
        ax.grid(True, which='minor', alpha=1, linestyle=':')
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