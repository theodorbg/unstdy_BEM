
import os
import glob
import numpy as np

class BladeData:
    """Stores tip deflection time series for a single blade."""
    def __init__(self, time, y, z):
        self.time = time          # time [s]
        self.y = y                # in-plane tip deflection [m]
        self.z = z                # out-of-plane tip deflection [m]

class AshesResult:
    """Container for all blade tip deflections from one Ashes run."""
    def __init__(self):
        self.blade1 = None
        self.blade2 = None
        self.blade3 = None

def _parse_blade_file(filepath):
    """Parse a single Ashes Blade [Time] .txt file and return a BladeData object."""
    time, tip_oop, tip_ip = [], [], []

    col_time = col_oop = col_ip = None

    with open(filepath, "r") as f:
        lines = f.readlines()

    # Find the header line with column names (first non-comment, non-dashes data line)
    header_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("-") or stripped == "":
            continue
        # Look for the column name row (contains "Time")
        if "Time" in stripped and col_time is None:
            cols = stripped.split("\t")
            for j, c in enumerate(cols):
                if "Time" in c:
                    col_time = j
                elif "out-of-plane" in c and "deflection" in c.lower():
                    col_oop = j
                elif "in-plane" in c and "deflection" in c.lower():
                    col_ip = j
            header_idx = i
            continue
        # Skip stat rows (Min, Max, Mean, Standard deviation) and dashes
        if any(stripped.startswith(k) for k in ("Min", "Max", "Mean", "Standard", "---", "# Column")):
            continue
        # Data rows: must have found header and be tab-separated numeric
        if header_idx is not None and col_time is not None:
            parts = stripped.split("\t")
            try:
                time.append(float(parts[col_time]))
                tip_oop.append(float(parts[col_oop]))
                tip_ip.append(float(parts[col_ip]))
            except (ValueError, IndexError):
                continue

    return BladeData(
        time=np.array(time),
        y=np.array(tip_ip),
        z=np.array(tip_oop),
    )

def load_ashes(folder_path):
    result = AshesResult()

    # Debug: print all files found in the folder
    all_files = os.listdir(folder_path)
    print("Files found in folder:")
    for f in all_files:
        print(f"  {repr(f)}")

    blade_map = {
        "Blade [Time] [Blade 1]": "blade1",
        "Blade [Time] [Blade 2]": "blade2",
        "Blade [Time] [Blade 3]": "blade3",
    }

    for filename_stem, attr in blade_map.items():
        # Find any file whose name starts with the stem (handles any extension)
        matches = [f for f in all_files if f.startswith(filename_stem)]
        if matches:
            filepath = os.path.join(folder_path, matches[0])
            setattr(result, attr, _parse_blade_file(filepath))
            print(f"Loaded {matches[0]} → {attr} ({len(getattr(result, attr).time)} samples)")
        else:
            print(f"Warning: No file matching '{filename_stem}' found in {folder_path}")

    return result


# ── Example usage ──────────────────────────────────────────────────────────────
# ashes_18ms = load_ashes(r"C:\Users\tgilh\OneDrive\Dokumenter\Ashes 3.31\46310\Assignment 3\18ms")
# print(ashes_18ms.blade1.z[:5])   # out-of-plane deflection, blade 1
# print(ashes_18ms.blade2.y[:5])   # in-plane deflection, blade 2
