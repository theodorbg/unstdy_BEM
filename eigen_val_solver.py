import scipy.linalg as la
import numpy as np
from structure import FlexibleStructure11DOF

"""
pseudo code start

structure = FlexibleStructure11DOF()
K = structure.K
M =structure.M

pseudo code end

"""

structure = FlexibleStructure11DOF(
    omega_init=0.0,
    file_blade="data/blade_data.csv",
    hub_height=119,
    bot_thickness=3.32,
    top_thickness=3.32,
    l_shaft=7.1,
    cone=0.0,
    yaw=0.0,
    tilt=0.0,
    pitch_init=[0.0, 0.0, 0.0],
    inertia_rotor=1.6e8,
    omega_modes=[3.93, 6.10, 11.28],
    tower_stiffness=1.7e6,
    nacelle_mass=446000.0,
    zeta_modal=0.0,
    zeta_tower=0.0,
    include_gravity=True,
    file_modes="data/modeshapes.txt"
    )

u_y_all, u_z_all, gm = [], [], []
for blade in range(structure.n_blades):
    u_y, u_z = structure._pitch_rotated_modes(blade)
    u_y_all.append(u_y)
    u_z_all.append(u_z)
    gm.append(structure._calc_GM(u_y, u_z))

K = structure._build_K(gm)
M = structure._build_M(gm, u_y_all, u_z_all)

N_DOF = 11

omega_sqr, v_matrix = la.eig(K, M)
# temporary omega calculation, will be sorted later
omega_temp = np.sqrt(np.abs(omega_sqr))


mode_shapes_matrix = np.zeros([N_DOF, N_DOF])
#Normalizing modeshapes
for m in range(N_DOF):
    print(f"Mode {m+1}/{N_DOF}")
    id=np.unravel_index(np.argmax(abs(v_matrix[:,m]),axis=None),v_matrix.shape)
    mode_shapes_matrix[:,m]=np.divide(v_matrix[:,m],v_matrix[id[1],m])

#sorting omega and corresponding mode shapes 
sort_id = omega_temp.argsort()
omega = omega_temp[sort_id[::-1]]
mode_shapes_matrix = mode_shapes_matrix[:,sort_id[::-1]]

# ── LaTeX table of mode shapes with highlighted dominant cells ────────────────

DOF_LABELS = [
    ("Tower",    ""),
    ("Rotation", ""),
    ("B1", "1\\textsuperscript{st} flap"),
    ("B1", "1\\textsuperscript{st} edge"),
    ("B1", "2\\textsuperscript{nd} flap"),
    ("B2", "1\\textsuperscript{st} flap"),
    ("B2", "1\\textsuperscript{st} edge"),
    ("B2", "2\\textsuperscript{nd} flap"),
    ("B3", "1\\textsuperscript{st} flap"),
    ("B3", "1\\textsuperscript{st} edge"),
    ("B3", "2\\textsuperscript{nd} flap"),
]

omega_real = np.real(omega)

# One color per mode column, cycling through 4 colors
COLORS = ["modeA", "modeB"]
THRESHOLD = 0.3  # |value| >= this gets highlighted

def fmt(val, col_idx, highlight=False):
    s = f"{np.real(val):.2f}"
    color = COLORS[col_idx % len(COLORS)]
    if highlight:
        return f"\\cellcolor{{{color}!50}}\\textbf{{{s}}}"  # was !25
    else:
        return s
    
col_spec = "ll" + "r" * N_DOF
lines = []

# LaTeX color definitions (add to preamble note)
preamble_note = (
    "% Add to LaTeX preamble:\n"
    "% \\usepackage[table]{xcolor}\n"
    "% \\definecolor{modeA}{RGB}{31, 119, 180}   % blue\n"
    "% \\definecolor{modeB}{RGB}{214, 39, 40}    % red\n"
    "% \\definecolor{modeC}{RGB}{44, 160, 44}    % green\n"
    "% \\definecolor{modeD}{RGB}{148, 103, 189}  % purple\n"
)
print(preamble_note)
lines.append("\\begin{table}[H]")
lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
lines.append("\\hline")

# Frequency header row
freq_cells = []
for j in range(N_DOF):
    color = COLORS[j % len(COLORS)]
    freq_cells.append(f"\\cellcolor{{{color}!40}}{omega_real[j]:.2f}")  # was !15
lines.append(
    f"\\multicolumn{{2}}{{l}}{{$\\omega$ [rad/s]}} & " +
    " & ".join(freq_cells) + " \\\\"
)
lines.append("\\hline")

prev_blade = None
for row_idx, (blade, dof_name) in enumerate(DOF_LABELS):
    row_vals = mode_shapes_matrix[row_idx, :]

    if blade in ("Tower", "Rotation"):
        b_str = f"\\multicolumn{{2}}{{l}}{{{blade}}}"
        cells = [fmt(row_vals[j], j, highlight=abs(np.real(row_vals[j])) >= THRESHOLD)
                 for j in range(N_DOF)]
        lines.append(f"{b_str} & " + " & ".join(cells) + " \\\\")
        prev_blade = blade
    else:
        if blade != prev_blade:
            b_str = f"\\multirow{{3}}{{*}}{{{blade}}}"
            prev_blade = blade
        else:
            b_str = ""
        cells = [fmt(row_vals[j], j, highlight=abs(np.real(row_vals[j])) >= THRESHOLD)
                 for j in range(N_DOF)]
        lines.append(f"{b_str} & {dof_name} & " + " & ".join(cells) + " \\\\")
        if "2" in dof_name and "flap" in dof_name:
            lines.append("\\hline")

lines.append("\\end{tabular}")
lines.append("\\caption{Mode shapes of the 11 DOF system}")
lines.append("\\label{tab:mode_shapes_eigenvals}")
lines.append("\\end{table}")

print("\n".join(lines))