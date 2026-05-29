import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from pathlib import Path


# Global text size control
FONT_SIZE = 40
# Default line styles and widths to cycle through
LINE_STYLES = ['-', '--', '-.', ':']
LINE_STYLES = ['-']
LINE_WIDTH  = 8
# --- NEW: global tick-density controls ---
X_MAJOR_NBINS = 8            # for MaxNLocator on x in plot_flexible
Y_MAJOR_NBINS = 8            # for MaxNLocator on y in plot_flexible
X_MINOR_SUBDIV = 2           # AutoMinorLocator subdivisions
Y_MINOR_SUBDIV = 2           # AutoMinorLocator subdivisions
PSD_X_MAJOR_STEP = 1.0       # major x-step in plot_psd_flexible (1P units)

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

def plot_flexible(
    x_val: np.ndarray = None,
    y_values: list = None,
    labels: list = None,
    x_label: str = None,
    y_units: list = None,
    save_name: str = None,
    shear_exp: float = 0.2,
    ylims=None,
    xlims=None,
    fig_size=32,
    vlines=None,
    hlines=None,
    dyn_wake=True,
    dyn_stall=True,
    structural_dynamics=False,
    tower=True,
    turb=0,
    show_plot=False,
    x_major_nbins: int = X_MAJOR_NBINS,
    y_major_nbins: int = Y_MAJOR_NBINS,
    x_minor_subdiv: int = X_MINOR_SUBDIV,
    y_minor_subdiv: int = Y_MINOR_SUBDIV,
    legend_loc="upper center",
    shared_legend: bool = True,
    legend_bbox_to_anchor=(0.5, 1.02),
    legend_ncol: int = 5,
):
    x_val = np.asarray(x_val).flatten()

    # inline format support:
    # y_values = [y_list0, labels0, y_list1, labels1, ...]
    if labels is None and isinstance(y_values, list) and len(y_values) % 2 == 0:
        parsed_y, parsed_labels = [], []
        inline_ok = True
        for i in range(0, len(y_values), 2):
            y_i = y_values[i]
            l_i = y_values[i + 1]
            if not isinstance(y_i, (list, tuple, np.ndarray)):
                inline_ok = False
                break
            if not isinstance(l_i, (list, tuple, np.ndarray)):
                inline_ok = False
                break
            parsed_y.append(list(y_i))
            parsed_labels.append(list(l_i))
        if inline_ok:
            y_values = parsed_y
            labels = parsed_labels

    if labels is None:
        raise ValueError("labels is required unless provided inline inside y_values.")

    subplots = len(y_values)

    if not isinstance(y_values[0], (list, np.ndarray, tuple)):
        y_values = [[y] for y in y_values]
    if not isinstance(labels[0], list):
        labels = [[l] for l in labels]

    assert len(y_values) == subplots, "y_values must have one list per subplot"
    assert len(labels) == subplots, "labels must have one list per subplot"
    assert len(y_units) == subplots, "y_units must have one entry per subplot"

    if ylims is None:
        ylims = [None] * subplots
    assert len(ylims) == subplots, "ylims must have one entry per subplot"

    def _normalize_lines(lines_in, n_subplots):
        if lines_in is None:
            return [[] for _ in range(n_subplots)]
        if isinstance(lines_in, (int, float, np.floating, dict)):
            return [[lines_in] for _ in range(n_subplots)]
        if isinstance(lines_in, (list, tuple, np.ndarray)):
            if len(lines_in) == n_subplots:
                out = []
                for item in lines_in:
                    if item is None:
                        out.append([])
                    elif isinstance(item, (int, float, np.floating, dict, tuple, list)):
                        out.append([item] if not isinstance(item, list) else item)
                    else:
                        raise TypeError(f"Unsupported line item type: {type(item)}")
                return out
            return [list(lines_in) for _ in range(n_subplots)]
        raise TypeError(f"Unsupported lines type: {type(lines_in)}")

    hlines_per_subplot = _normalize_lines(hlines, subplots)
    vlines_per_subplot = _normalize_lines(vlines, subplots)

    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)

    # shear_exp_string = f"{shear_exp:.2f}".replace(".", "p")
    # save_name += f"_shear_{shear_exp_string}"
    if not tower:
        save_name += "_no_tower"
    if not dyn_wake:
        save_name += "_no_dyn_wake"
    if not dyn_stall:
        save_name += "_no_dyn_stall"
    if not structural_dynamics:
        save_name += "_rigid_structure"
    else:        
        save_name += "_flexible_structure"
    save_name += f"_turb_{turb}"

    fig, axes = plt.subplots(subplots, 1, figsize=(fig_size, 9 * subplots), sharex=True)
    if subplots == 1:
        axes = [axes]

    for idx, (ax, y_list, label_list, y_unit, ylim, h_lines, v_lines) in enumerate(zip(
        axes, y_values, labels, y_units, ylims, hlines_per_subplot, vlines_per_subplot
    )):
        for i, (y_item, label) in enumerate(zip(y_list, label_list)):
            # y_item can be:
            # 1) y-array (uses shared x_val)
            # 2) (x_custom, y_custom)
            if isinstance(y_item, (tuple, list)) and len(y_item) == 2:
                x_plot = np.asarray(y_item[0]).flatten()
                y_plot = np.asarray(y_item[1]).flatten()
            else:
                x_plot = x_val
                y_plot = np.asarray(y_item).flatten()

            if x_plot.shape[0] != y_plot.shape[0]:
                raise ValueError(
                    f"x/y length mismatch for '{label}': "
                    f"len(x)={x_plot.shape[0]}, len(y)={y_plot.shape[0]}"
                )

            ax.plot(
                x_plot, y_plot,
                label=label,
                linewidth=LINE_WIDTH,
                linestyle=LINE_STYLES[i % len(LINE_STYLES)],
            )

        # color cycle for ref lines (vlines + hlines)
        ref_colors = plt.rcParams["axes.prop_cycle"].by_key().get(
            "color", ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]
        )
        ref_idx = 0
        def _next_ref_color():
            nonlocal ref_idx
            c = ref_colors[ref_idx % len(ref_colors)]
            ref_idx += 1
            return c

        for vline in v_lines:
            if isinstance(vline, dict):
                color_v = vline.get("color", _next_ref_color())
                ax.axvline(
                    x=vline["x"],
                    color=color_v,
                    linestyle=vline.get("linestyle", "--"),
                    linewidth=vline.get("linewidth", LINE_WIDTH),
                    alpha=vline.get("alpha", 1.0),
                    label=vline.get("label", None),
                )
            elif isinstance(vline, (tuple, list)):
                if len(vline) == 2:
                    x_v, label_v, style = vline[0], vline[1], {}
                elif len(vline) == 3 and isinstance(vline[2], dict):
                    x_v, label_v, style = vline
                else:
                    raise ValueError("vline must be (x, label) or (x, label, style_dict)")
                color_v = style.get("color", _next_ref_color())
                ax.axvline(
                    x=float(x_v),
                    color=color_v,
                    linestyle=style.get("linestyle", "--"),
                    linewidth=style.get("linewidth", LINE_WIDTH),
                    alpha=style.get("alpha", 1.0),
                    label=label_v,
                )

        for hline in h_lines:
            if isinstance(hline, dict):
                y_h = hline.get("y", hline.get("value"))
                if y_h is None:
                    raise ValueError("hline dict must contain 'y' or 'value'")
                color_h = hline.get("color", _next_ref_color())
                ax.axhline(
                    y=float(y_h),
                    color=color_h,
                    linestyle=hline.get("linestyle", "--"),
                    linewidth=hline.get("linewidth", LINE_WIDTH),
                    alpha=hline.get("alpha", 1.0),
                    label=hline.get("label", None),
                )
            elif isinstance(hline, (tuple, list)):
                if len(hline) == 2:
                    y_h, label_h, style = hline[0], hline[1], {}
                elif len(hline) == 3 and isinstance(hline[2], dict):
                    y_h, label_h, style = hline
                else:
                    raise ValueError("hline must be (y, label) or (y, label, style_dict)")
                color_h = style.get("color", _next_ref_color())
                ax.axhline(
                    y=float(y_h),
                    color=color_h,
                    linestyle=style.get("linestyle", "--"),
                    linewidth=style.get("linewidth", LINE_WIDTH),
                    alpha=style.get("alpha", 1.0),
                    label=label_h,
                )
            else:
                ax.axhline(
                    y=float(hline),
                    color=_next_ref_color(),
                    linestyle="--",
                    linewidth=LINE_WIDTH,
                )

                
        ax.set_ylabel(y_unit)

        if not shared_legend and legend_loc is not None:
            if isinstance(legend_loc, (list, tuple)):
                if legend_loc[idx] is not None:
                    ax.legend(loc=legend_loc[idx])
            else:
                ax.legend(loc=legend_loc)

        ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=x_major_nbins))
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=y_major_nbins))
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(x_minor_subdiv))
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(y_minor_subdiv))
        ax.minorticks_on()
        ax.grid(True, which='major', alpha=1, linestyle='--')
        ax.grid(True, which='minor', alpha=0.5, linestyle=':')   # lower alpha for minor
        if ylim is not None:
            ax.set_ylim(ylim[0], ylim[1])

    if shared_legend:
        handles, labels_all = [], []
        seen = set()
        for ax in axes:
            h, l = ax.get_legend_handles_labels()
            for hh, ll in zip(h, l):
                if ll and ll not in seen:
                    handles.append(hh)
                    labels_all.append(ll)
                    seen.add(ll)

        fig.legend(
            handles,
            labels_all,
            loc=legend_loc,
            bbox_to_anchor=legend_bbox_to_anchor,
            ncol=legend_ncol,
            frameon=True,
        )

    if xlims is not None:
        axes[0].set_xlim(xlims[0], xlims[1])  # shared x axis, only need to set once

    axes[-1].set_xlabel(x_label)
    plt.tight_layout(rect=(0, 0, 1, 0.92))
    plt.savefig(save_path / f"{save_name}.png", bbox_inches="tight")
    if show_plot:
        plt.show()
    plt.close()

def plot_flexible_old(
    x_val: np.ndarray = None,
    y_values: list = None,
    labels: list = None,
    x_label: str = None,
    y_units: list = None,
    save_name: str = None,
    shear_exp: float = 0.2,
    ylims=None,
    xlims=None,
    fig_size = 32,
    vlines=None,          # e.g. [{"x": 100, "color": "gray", "linestyle": "--", "label": "t=100s"}, ...]
    hlines=None,
    dyn_wake=True,
    dyn_stall=True,
    tower=True,
    turb=0,
    show_plot=False,
    x_major_nbins: int = X_MAJOR_NBINS,      # NEW
    y_major_nbins: int = Y_MAJOR_NBINS,      # NEW
    x_minor_subdiv: int = X_MINOR_SUBDIV,    # NEW
    y_minor_subdiv: int = Y_MINOR_SUBDIV     # NEW
):
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
    - hlines: list of dictionaries for horizontal lines
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

        # --- normalize hlines to per-subplot list ---
    def _normalize_hlines(hlines_in, n_subplots):
        if hlines_in is None:
            return [[] for _ in range(n_subplots)]

        # single spec (number or dict) -> apply to all subplots
        if isinstance(hlines_in, (int, float, np.floating, dict)):
            return [[hlines_in] for _ in range(n_subplots)]

        if isinstance(hlines_in, (list, tuple, np.ndarray)):
            # per-subplot form
            if len(hlines_in) == n_subplots:
                out = []
                for item in hlines_in:
                    if item is None:
                        out.append([])
                    elif isinstance(item, (int, float, np.floating, dict)):
                        out.append([item])
                    elif isinstance(item, (list, tuple, np.ndarray)):
                        out.append(list(item))
                    else:
                        raise TypeError(f"Unsupported hlines item type: {type(item)}")
                return out

            # global list form -> apply same lines to all subplots
            return [list(hlines_in) for _ in range(n_subplots)]

        raise TypeError(f"Unsupported hlines type: {type(hlines_in)}")

    hlines_per_subplot = _normalize_hlines(hlines, subplots)

    # --- create folder ---
    save_path = Path("plots")
    save_path.mkdir(exist_ok=True)

    # --- build save name ---
    shear_exp_string = f"{shear_exp:.2f}".replace(".", "p")
    save_name += f"_shear_{shear_exp_string}"
    if not tower:
        save_name += "_no_tower"
    if not dyn_wake:
        save_name += "_no_dyn_wake"
    if not dyn_stall:
        save_name += "_no_dyn_stall"
    save_name += f"_turb_{turb}"

    # --- plot ---
    # --- plot ---
    fig, axes = plt.subplots(subplots, 1, figsize=(fig_size, 9 * subplots), sharex=True)
    if subplots == 1:
        axes = [axes]

    for ax, y_list, label_list, y_unit, ylim, h_lines, v_lines in zip(
        axes, y_values, labels, y_units, ylims, hlines_per_subplot, vlines_per_subplot
    ):
        for i, (y_item, label) in enumerate(zip(y_list, label_list)):
            # y_item can be:
            # 1) y-array (uses shared x_val)
            # 2) (x_custom, y_custom)
            if isinstance(y_item, (tuple, list)) and len(y_item) == 2:
                x_plot = np.asarray(y_item[0]).flatten()
                y_plot = np.asarray(y_item[1]).flatten()
            else:
                x_plot = x_val
                y_plot = np.asarray(y_item).flatten()

            if x_plot.shape[0] != y_plot.shape[0]:
                raise ValueError(
                    f"x/y length mismatch for '{label}': "
                    f"len(x)={x_plot.shape[0]}, len(y)={y_plot.shape[0]}"
                )

            ax.plot(
                x_plot, y_plot,
                label=label,
                linewidth=LINE_WIDTH,
                linestyle=LINE_STYLES[i % len(LINE_STYLES)],
            )

        # color cycle for ref lines (vlines + hlines)
        ref_colors = plt.rcParams["axes.prop_cycle"].by_key().get(
            "color", ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]
        )
        ref_idx = 0
        def _next_ref_color():
            nonlocal ref_idx
            c = ref_colors[ref_idx % len(ref_colors)]
            ref_idx += 1
            return c

        for vline in v_lines:
            if isinstance(vline, dict):
                color_v = vline.get("color", _next_ref_color())
                ax.axvline(
                    x=vline["x"],
                    color=color_v,
                    linestyle=vline.get("linestyle", "--"),
                    linewidth=vline.get("linewidth", LINE_WIDTH),
                    alpha=vline.get("alpha", 1.0),
                    label=vline.get("label", None),
                )
            elif isinstance(vline, (tuple, list)):
                if len(vline) == 2:
                    x_v, label_v, style = vline[0], vline[1], {}
                elif len(vline) == 3 and isinstance(vline[2], dict):
                    x_v, label_v, style = vline
                else:
                    raise ValueError("vline must be (x, label) or (x, label, style_dict)")
                color_v = style.get("color", _next_ref_color())
                ax.axvline(
                    x=float(x_v),
                    color=color_v,
                    linestyle=style.get("linestyle", "--"),
                    linewidth=style.get("linewidth", LINE_WIDTH),
                    alpha=style.get("alpha", 1.0),
                    label=label_v,
                )

        for hline in h_lines:
            if isinstance(hline, dict):
                y_h = hline.get("y", hline.get("value"))
                if y_h is None:
                    raise ValueError("hline dict must contain 'y' or 'value'")
                color_h = hline.get("color", _next_ref_color())
                ax.axhline(
                    y=float(y_h),
                    color=color_h,
                    linestyle=hline.get("linestyle", "--"),
                    linewidth=hline.get("linewidth", LINE_WIDTH),
                    alpha=hline.get("alpha", 1.0),
                    label=hline.get("label", None),
                )
            elif isinstance(hline, (tuple, list)):
                if len(hline) == 2:
                    y_h, label_h, style = hline[0], hline[1], {}
                elif len(hline) == 3 and isinstance(hline[2], dict):
                    y_h, label_h, style = hline
                else:
                    raise ValueError("hline must be (y, label) or (y, label, style_dict)")
                color_h = style.get("color", _next_ref_color())
                ax.axhline(
                    y=float(y_h),
                    color=color_h,
                    linestyle=style.get("linestyle", "--"),
                    linewidth=style.get("linewidth", LINE_WIDTH),
                    alpha=style.get("alpha", 1.0),
                    label=label_h,
                )
            else:
                ax.axhline(
                    y=float(hline),
                    color=_next_ref_color(),
                    linestyle="--",
                    linewidth=LINE_WIDTH,
                )

                
        ax.set_ylabel(y_unit)
        ax.legend()
        ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=x_major_nbins))
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=y_major_nbins))
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(x_minor_subdiv))
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(y_minor_subdiv))
        ax.minorticks_on()
        ax.grid(True, which='major', alpha=1, linestyle='--')
        ax.grid(True, which='minor', alpha=0.5, linestyle=':')   # lower alpha for minor
        if ylim is not None:
            ax.set_ylim(ylim[0], ylim[1])

    if xlims is not None:
        axes[0].set_xlim(xlims[0], xlims[1])  # shared x axis, only need to set once

    axes[-1].set_xlabel(x_label)
    plt.title(save_name.replace("_", " ").title(), fontsize=FONT_SIZE)
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
    show_plot=False,
    x_major_step: float = PSD_X_MAJOR_STEP,   # NEW
    x_minor_subdiv: int = X_MINOR_SUBDIV      # NEW
):
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

        ax.xaxis.set_major_locator(ticker.MultipleLocator(x_major_step))
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(x_minor_subdiv))
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
    

def section_divider(message: str):
    print('#'*60)
    print(message)
    print('#'*60)

