def print_latex_table(df_results):
    caption = r"Steady-state performance vs. hub wind speed"
    label = r"tab:cp_2_1"

    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\begin{tabular}{|c|c|c|c|c|c|}")
    print(r"\hline")
    print(
        r"\textbf{$V_{hub} \left[\frac{m}{s}\right]$} & "
        r"\textbf{$C_p [-]$} & "
        r"\textbf{$P_{rotor}[MW]$} & "
        r"\textbf{$P_{gen}[MW]$} & "
        r"\textbf{$\omega \left[\frac{rad}{s}\right]$} & "
        r"\textbf{$\theta_p [^\circ]$} \\ \hline"
    )

    for _, row in df_results.sort_values("V_hub").iterrows():
        print(
            f"{row['V_hub']:.1f} & "
            f"{row['cp_rotor']:.4f} & "
            f"{row['mech_out_rotor'] / 1e6:.4f} & "
            f"{row['power_gen'] / 1e6:.4f} & "
            f"{row['omega']:.4f} & "
            f"{row['pitch']:.4f} \\\\ \\hline"
        )

    print(r"\end{tabular}")
    print(rf"\caption{{{caption}}}")
    print(rf"\label{{{label}}}")
    print(r"\end{table}")
