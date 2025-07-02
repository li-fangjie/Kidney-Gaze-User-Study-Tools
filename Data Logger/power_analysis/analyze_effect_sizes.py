import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.stats.power import TTestIndPower

def cohens_d(x1, x2):
    n1, n2 = len(x1), len(x2)
    pooled_sd = np.sqrt(
        ((n1 - 1)*np.std(x1, ddof=1)**2 + (n2 - 1)*np.std(x2, ddof=1)**2) / (n1 + n2 - 2)
    )
    return (np.mean(x1) - np.mean(x2)) / pooled_sd

def filter_group(df, task, expertise, guidance):
    return df[
        (df['Task Type'] == task) &
        (df['Expertise Level'] == expertise) &
        (df['Guidance Type'] == guidance)
    ]

def power_curve_plot(effect_size, label):
    analysis = TTestIndPower()
    sample_sizes = np.arange(5, 101)
    powers = analysis.power(effect_size=effect_size, nobs1=sample_sizes, alpha=0.05)

    required_n = analysis.solve_power(effect_size=effect_size, power=0.8, alpha=0.05)

    plt.figure(figsize=(8, 5))
    plt.plot(sample_sizes, powers, label=f'd = {effect_size:.2f}')
    plt.axhline(0.8, color='red', linestyle='--', label='Power = 0.8')
    plt.axvline(required_n, color='green', linestyle='--', label=f'n ≈ {required_n:.0f}')
    plt.title(f'Power Curve for {label}')
    plt.xlabel('Sample Size per Group')
    plt.ylabel('Power')
    plt.legend()
    plt.tight_layout()
    plt.show()

    print(f"\nPower analysis for {label}: need ~{required_n:.0f} samples per group for 80% power.\n")

def main(xlsx_file):
    df = pd.read_excel(xlsx_file, engine='openpyxl')
    df.columns = df.columns.str.strip()

    # Normalize for filtering
    df['Task Type'] = df['Task Type'].astype(str).str.strip().str.lower()
    df['Expertise Level'] = df['Expertise Level'].astype(str).str.strip().str.lower()
    df['Guidance Type'] = df['Guidance Type'].astype(str).str.strip().str.lower()

    df['Percentage AOI'] = pd.to_numeric(df['Percentage AOI'], errors='coerce')

    comparisons = [
        ("ablating", "expert", "selfgaze", "novice", "guided"),
        ("scoping", "expert", "selfgaze", "novice", "guided"),
    ]

    for task, exp1, guide1, exp2, guide2 in comparisons:
        g1 = filter_group(df, task, exp1, guide1)
        g2 = filter_group(df, task, exp2, guide2)

        aoi1 = g1['Percentage AOI'].dropna().values
        aoi2 = g2['Percentage AOI'].dropna().values

        print(f"Checking {task}: {exp1}({guide1}) n={len(aoi1)} vs {exp2}({guide2}) n={len(aoi2)}")

        if len(aoi1) >= 2 and len(aoi2) >= 2:
            d = cohens_d(aoi1, aoi2)
            print(f"Running power analysis for {task}: Cohen's d = {d:.2f}")
            power_curve_plot(d, f"{task}: {exp1} vs {exp2}")
        else:
            print(f"Not enough data for power analysis for {task}. Skipping.\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simple power analysis")
    parser.add_argument('xlsx_file', type=str, help='Excel file with data')
    args = parser.parse_args()

    main(args.xlsx_file)

# python analyze_effect_sizes.py Kidney_Eye_Gaze_Data.xlsx