Yes. Add a `legend_loc` argument and pass it to `ax.legend(...)`.

Use this patch in `plot_flexible`:

````python
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
    tower=True,
    turb=0,
    show_plot=False,
    x_major_nbins: int = X_MAJOR_NBINS,
    y_major_nbins: int = Y_MAJOR_NBINS,
    x_minor_subdiv: int = X_MINOR_SUBDIV,
    y_minor_subdiv: int = Y_MINOR_SUBDIV,
    legend_loc="best",          # NEW
):
    # ...existing code...
````

````python
# ...inside the subplot loop, replace ax.legend() with:
        # legend_loc can be str (same for all) or list (per subplot)
        loc_i = legend_loc if isinstance(legend_loc, str) else legend_loc[axes.index(ax)]
        ax.legend(loc=loc_i)
# ...existing code...
````

Better/safer per-subplot indexing (recommended):

````python
for idx, (ax, y_list, label_list, y_unit, ylim, h_lines, v_lines) in enumerate(zip(
    axes, y_values, labels, y_units, ylims, hlines_per_subplot, vlines_per_subplot
)):
    # ...existing plotting code...
    if isinstance(legend_loc, (list, tuple)):
        ax.legend(loc=legend_loc[idx])
    else:
        ax.legend(loc=legend_loc)
````

Example call:

````python
plot_flexible(
    # ...existing args...
    legend_loc=["upper right", "upper left", "lower right", "upper left"],
)
````

If you want exact manual placement, use `bbox_to_anchor`; I can add `legend_bbox` too.