Use a nearest-match overwrite for the low-speed region.

````python
# ...existing code...
df_turb = pd.read_csv("sim_data/csv/cp_2_2_turb_results.csv")
df_turb_low = pd.read_csv("sim_data/csv/cp_2_2_turb_low_speeds_results.csv")

# replace low-speed rows in df_turb with nearest available rows from df_turb_low
low_max = df_turb_low["V_hub"].max()
mask_low = df_turb["V_hub"] <= low_max

cols_to_replace = ["cp_rotor", "mech_out_rotor", "power_gen", "omega", "pitch"]

low_v = df_turb_low["V_hub"].to_numpy()
for idx, v in df_turb.loc[mask_low, "V_hub"].items():
    j = np.abs(low_v - v).argmin()  # nearest low-speed point
    df_turb.loc[idx, cols_to_replace] = df_turb_low.loc[j, cols_to_replace].to_numpy()

# optional: save merged result
df_turb.to_csv("sim_data/csv/cp_2_2_turb_results_merged.csv", index=False)
print("saved merged csv: sim_data/csv/cp_2_2_turb_results_merged.csv")
# ...existing code...
````

If you prefer, this can also be done by interpolation (smoother), but the above uses only “available” low-speed points.