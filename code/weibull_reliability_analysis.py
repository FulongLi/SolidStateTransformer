import numpy as np
import matplotlib.pyplot as plt
from reliability.Fitters import Fit_Weibull_2P
from reliability.Probability_plotting import Weibull_probability_plot

# =========================
# 0) Input: Three temperature point data (unit: hours)
#    failures = time of failed samples
#    right_censored = time of samples that have not failed at the end (right censored)
# =========================

data = {
    125: {
        "failures": [780, 860, 940, 1030, 1120, 1250],   # Example: replace with real data
        "right_censored": [1400, 1400, 1400, 1400],      # Example: use [] if no censored data
    },
    150: {
        "failures": [420, 510, 580, 640, 700, 750, 810, 880, 950, 1100, 1250, 1300, 1450, 1600, 1800],
        "right_censored": [],  # No censored data for this group
    },
    175: {
        "failures": [180, 220, 260, 310, 360, 420, 480], # Example: replace with real data
        "right_censored": [550, 550, 550],               # Example
    }
}

# Use temperature (C)
T_use_C = 55.0

# Boltzmann constant (eV/K)
kB = 8.617333262e-5

# =========================
# 1) Weibull fit at each temperature, extract eta/beta/B10/B1
# =========================
results = {}

for T_C, d in data.items():
    failures = np.array(d["failures"], dtype=float)
    rc = np.array(d["right_censored"], dtype=float) if len(d["right_censored"]) > 0 else None

    wb = Fit_Weibull_2P(
        failures=failures,
        right_censored=rc,
        show_probability_plot=False
    )

    eta = wb.alpha
    beta = wb.beta

    # B10/B1 (Weibull 2P quantile points)
    B10 = eta * (-np.log(0.9))**(1/beta)
    B1  = eta * (-np.log(0.99))**(1/beta)

    results[T_C] = {"eta": eta, "beta": beta, "B10": B10, "B1": B1}

    print(f"\nWeibull fit @ {T_C}C")
    print(f"  eta:  {eta:.2f} h")
    print(f"  beta: {beta:.2f}")
    print(f"  B10:  {B10:.2f} h")
    print(f"  B1:   {B1:.2f} h")

    # Probability plot (optional: one plot for each temperature)
    plt.figure(figsize=(7, 5))
    Weibull_probability_plot(failures=failures, right_censored=rc)
    plt.title(f"Weibull Probability Plot @ {T_C}C")
    plt.tight_layout()
    plt.show()

# =========================
# 2) Arrhenius fit: ln(eta) vs 1/T
#    Can also use ln(B10) vs 1/T, more relevant for engineering life metrics
# =========================
temps_C = np.array(sorted(results.keys()), dtype=float)
temps_K = temps_C + 273.15
x = 1.0 / temps_K  # 1/T

# Use eta or B10 for fitting (B10 recommended for engineering)
y = np.log(np.array([results[T]["B10"] for T in temps_C], dtype=float))  # ln(B10)

# Linear fit y = a + m*x
m, a = np.polyfit(x, y, 1)

Ea_fit = m * kB  # eV
print("\nArrhenius fit using ln(B10) vs 1/T")
print(f"  slope m: {m:.4e}")
print(f"  Ea:      {Ea_fit:.3f} eV")

# Arrhenius plot
plt.figure(figsize=(7, 5))
plt.plot(x, y, marker='o', linestyle='-')
plt.xlabel("1/T (1/K)")
plt.ylabel("ln(B10)  [ln(hours)]")
plt.title("Arrhenius Plot (based on B10)")
plt.tight_layout()
plt.show()

# =========================
# 3) Extrapolate to use temperature: AF + predicted lifetime
#    Select a reference stress temperature (e.g. 150C) for AF extrapolation
# =========================
T_ref_C = 150.0
T_ref_K = T_ref_C + 273.15
T_use_K = T_use_C + 273.15

AF = np.exp((Ea_fit / kB) * (1.0 / T_use_K - 1.0 / T_ref_K))

eta_ref = results[T_ref_C]["eta"]
B10_ref = results[T_ref_C]["B10"]
B1_ref  = results[T_ref_C]["B1"]

eta_use = eta_ref * AF
B10_use = B10_ref * AF
B1_use  = B1_ref * AF

print(f"\nExtrapolation to {T_use_C:.1f}C (reference = {T_ref_C:.0f}C)")
print(f"  AF:      {AF:.2f}")
print(f"  eta_use: {eta_use:.2f} h  ({eta_use/8760:.2f} years)")
print(f"  B10_use: {B10_use:.2f} h  ({B10_use/8760:.2f} years)")
print(f"  B1_use:  {B1_use:.2f} h  ({B1_use/8760:.2f} years)")
