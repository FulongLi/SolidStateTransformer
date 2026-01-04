"""
Dual Active Bridge (DAB) Inductor Selection Module
Converted from MATLAB code for technical note on Inductor selection for DAB

This module provides comprehensive tools for selecting and designing inductors
for Dual Active Bridge (DAB) converters used in Solid State Transformers.

Author: Fulong Li
License: CC BY 4.0
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional
import warnings


# Global semiconductor parameters
Coss_pri = 92e-12 / 10000  # [F] equivalent output capacitance of MOSFET in primary full-bridge
Ron_pri = 80e-3            # [Ohm] equivalent drain-source on-state resistance of MOSFET in primary full-bridge
Coss_sec = 260e-12         # [F] equivalent output capacitance of MOSFET in secondary full-bridge
Ron_sec = 21e-3            # [Ohm] equivalent drain-source on-state resistance of MOSFET in secondary full-bridge


def Irms_prim_phaseShift(phi, V1, V2, n, fsw, L):
    """
    Computation of primary RMS current for given operating point
    
    Source: Krismer_2011_03_17_Modeling_and_Optimization_of_Bidirectional_Dual_Active_Bridge_DC-DC_Converter_Topologies.pdf
    (warning: phi is defined without unit here, whereas Krismer uses [rad] --> phi = phi_Krismer/2/pi)
    
    Args:
        phi: Phase shift (normalized, not in radians)
        V1: Primary DC voltage [V]
        V2: Secondary DC voltage [V]
        n: Transformer turns ratio (N_prim/N_sec)
        fsw: Switching frequency [Hz]
        L: Total inductance [H]
        
    Returns:
        RMS current on primary side [A]
    """
    # RMS current for phase-shift modulation (duty ratios are 0.5)
    D1 = 0.5
    D2 = 0.5
    
    eRMS = (1 - 4 * abs(phi)) * (1 - 2 * abs(phi) + 4 * phi**2 - 3 * (D1 * (1 - D1) + D2 * (1 - D2)))
    Irms = 1 / (2 * fsw * L) * np.sqrt(D1**2 * V1**2 * (1 - 4/3 * D1) + 
                                        D2**2 * n**2 * V2**2 * (1 - 4/3 * D2) + 
                                        n * V1 * V2 / 3 * eRMS)
    
    return Irms


def ploss_vs_resolution(power, Lmin, Lmax, fsw, n, V1, V2, Ts, phase_shift_min):
    """
    Computation and plot of losses and resolution vs inductance
    
    Args:
        power: Power level [W]
        Lmin: Minimum inductance [H]
        Lmax: Maximum inductance [H]
        fsw: Switching frequency [Hz]
        n: Transformer turns ratio
        V1: Primary voltage [V]
        V2: Secondary voltage [V]
        Ts: Switching period [s]
        phase_shift_min: Minimum phase shift [normalized]
    """
    global Ron_pri, Ron_sec
    
    # Initialize lists
    phis = []
    Pconds = []
    resolutions = []
    Ls = []
    
    # Iterate through inductor values
    L = Lmin
    while L <= Lmax:
        Ls.append(L)
        a = -2
        b = 1
        c = -power * fsw * L / n / V1 / V2
        # Solve for phase shift
        roots = np.roots([a, b, c])
        phi = min(np.real(roots))
        phis.append(phi)
        
        resolution = (n * V1 * V2 * phi * (1 - 2*phi) / fsw / L) - \
                    (n * V1 * V2 * (phi - phase_shift_min) * (1 - 2*(phi - phase_shift_min)) / fsw / L)
        resolutions.append(resolution)
        
        # RMS current on the primary and secondary sides
        I_pri_RMS = Irms_prim_phaseShift(phi, V1, V2, n, fsw, L)
        I_sec_RMS = I_pri_RMS * n
        
        # RMS current running through two switches at all times (assuming negligible dead time)
        pri_Pcond = 2 * Ron_pri * I_pri_RMS**2
        sec_Pcond = 2 * Ron_sec * I_sec_RMS**2
        Pconds.append(pri_Pcond + sec_Pcond)
        
        L += 1e-6  # Increment by 1 µH
    
    # Convert to numpy arrays for plotting
    Ls = np.array(Ls) * 1e6  # Convert to µH
    Pconds = np.array(Pconds)
    resolutions = np.array(resolutions)
    
    # Plot losses and resolution against inductance
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    color1 = [0, 0.4470, 0.7410]
    color2 = [0.8500, 0.3250, 0.0980]
    
    ax1.set_xlabel(f'Total inductance [µH]')
    ax1.set_ylabel('Losses [W]', color=tuple(color1))
    line1 = ax1.plot(Ls, Pconds, color=tuple(color1), linewidth=2, label='Conduction losses')
    ax1.tick_params(axis='y', labelcolor=tuple(color1))
    ax1.grid(True, alpha=0.3)
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Resolution [W]', color=tuple(color2))
    line2 = ax2.plot(Ls, resolutions, color=tuple(color2), linewidth=2, label='Resolution')
    ax2.tick_params(axis='y', labelcolor=tuple(color2))
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='best')
    
    plt.title(f'Conduction loss/Resolution Tradeoff vs. Inductance @ {power}W')
    plt.tight_layout()
    return fig


def ploss_vs_P(Pmin, Pmax, Ltot, fsw, n, V1, V2):
    """
    Computation and plot of losses and efficiency vs power level
    
    Args:
        Pmin: Minimum power [W]
        Pmax: Maximum power [W]
        Ltot: Total inductance [H]
        fsw: Switching frequency [Hz]
        n: Transformer turns ratio
        V1: Primary voltage [V]
        V2: Secondary voltage [V]
    """
    global Ron_pri, Ron_sec
    
    powers = []
    Pconds = []
    Iout_rms = []
    effs = []
    
    for P in range(int(Pmin), int(Pmax) + 1):
        powers.append(P)
        
        a = -2
        b = 1
        c = -P * fsw * Ltot / n / V1 / V2
        # Solve for phase shift
        roots = np.roots([a, b, c])
        phi = min(np.real(roots))
        
        # RMS current on the primary and secondary sides
        I_pri_RMS = Irms_prim_phaseShift(phi, V1, V2, n, fsw, Ltot)
        I_sec_RMS = I_pri_RMS * n
        Iout_rms.append(I_sec_RMS)
        
        # RMS current running through two switches at all times (assuming negligible dead time)
        pri_Pcond = 2 * Ron_pri * I_pri_RMS**2
        sec_Pcond = 2 * Ron_sec * I_sec_RMS**2
        Pconds.append(pri_Pcond + sec_Pcond)
        
        # Efficiency
        effs.append(1 - Pconds[-1] / P)
    
    powers = np.array(powers)
    Pconds = np.array(Pconds)
    effs = np.array(effs)
    
    # Plot conduction losses and efficiency against power level
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    color1 = [0, 0.4470, 0.7410]
    color2 = [0.8500, 0.3250, 0.0980]
    
    ax1.set_xlabel('Power [W]')
    ax1.set_ylabel('Power losses [W]', color=tuple(color1))
    line1 = ax1.plot(powers, Pconds, color=tuple(color1), linewidth=2, label='Conduction losses')
    ax1.tick_params(axis='y', labelcolor=tuple(color1))
    ax1.grid(True, alpha=0.3)
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Efficiency [%]', color=tuple(color2))
    line2 = ax2.plot(powers, effs * 100, color=tuple(color2), linewidth=2, label='Efficiency')
    ax2.tick_params(axis='y', labelcolor=tuple(color2))
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='best')
    
    plt.title(f'Conduction losses and efficiency vs. Power Level @ L_tot = {Ltot*1e6:.2f} µH')
    plt.tight_layout()
    return fig


def dab_inductor_sizing_phaseShift(P: Optional[float] = None,
                                   V1: Optional[float] = None,
                                   V2: Optional[float] = None,
                                   fsw: Optional[float] = None,
                                   f_clk: Optional[float] = None,
                                   Llk: Optional[float] = None,
                                   n: Optional[float] = None,
                                   resolution_percentage: Optional[float] = None,
                                   Ltot: Optional[float] = None):
    """
    Main function for DAB inductor sizing based on phase shift modulation
    
    Args:
        P: Full rated power [W] (positive power implies power flow from V1->V2)
        V1: Input (primary) DC voltage [V]
        V2: Output (secondary) DC voltage [V]
        fsw: Switching frequency [Hz] (actual switching frequency of a single switch is fsw/2)
        f_clk: Clock frequency of the modulator in FPGA [Hz]
        Llk: Leakage inductance, referred to primary [H]
        n: Turns ratio (N_prim/N_sec)
        resolution_percentage: Maximum allowable change in power when minimum phase shift adjustment is made
        Ltot: Manual inductance selection [H] (if None, will prompt user)
    """
    global Coss_pri, Ron_pri, Coss_sec, Ron_sec
    
    # Default parameters (from original MATLAB code)
    if P is None:
        P = 1e3  # [W] rated active power
    if V1 is None:
        V1 = 720  # [V] input (primary) dc voltage
    if V2 is None:
        V2 = 40  # [V] output (secondary) dc voltage
    if fsw is None:
        fsw = 100e3  # [Hz] switching frequency
    if f_clk is None:
        f_clk = 250e6  # [Hz] clock frequency of the modulator in FPGA
    if Llk is None:
        Llk = 10e-6  # [H] leakage inductance, referred to primary
    if n is None:
        n = 15  # [-] turns ratio (N_prim/N_sec)
    if resolution_percentage is None:
        resolution_percentage = 0.025  # Maximum allowed is a percentage of full power
    
    Ts = 1 / fsw  # [s] switching period
    
    # Minimum power point where converter must be operating in ZVS
    P_min = 0.5 * P
    
    # Maximum allowable change in power when minimum phase shift adjustment is made [W]
    max_allowed_deltaP = resolution_percentage * P
    
    # ------------------------
    # Lower bound on L for ZVS
    # ------------------------
    # Minimum L to achieve ZVS (use P_min because it will be a stricter minimum L)
    # Selected inductor should be minimized while still meeting ZVS and resolution requirements at light load
    # Coss primary is used because that is where ZVS conditions need achieved
    Iout_min = P_min / V2
    Lmin = Coss_pri * (2 * Ts * V1 / ((1/n) * Iout_min * Ts + 8 * Coss_pri * V1))**2
    print(f'Lmin (ZVS): {Lmin}')
    
    a = -2
    b = 1
    c = -P_min * fsw * Lmin / n / V1 / V2
    # Solve for phase shift and controller resolution
    phase_shift_min = 1 / f_clk / Ts
    roots = np.roots([a, b, c])
    phi = min(np.real(roots))
    max_deltaP = (n * V1 * V2 * phi * (1 - 2*phi) / fsw / Lmin) - \
                (n * V1 * V2 * (phi - phase_shift_min) * (1 - 2*(phi - phase_shift_min)) / fsw / Lmin)
    
    # Whether or not the resolution limits the minimum L value
    resolution_limited = False
    
    # If min L to achieve ZVS doesn't provide enough resolution iterate up until it does
    while max_deltaP > max_allowed_deltaP:
        resolution_limited = True
        Lmin = Lmin * 1.0001
        a = -2
        b = 1
        c = -P_min * fsw * Lmin / n / V1 / V2
        roots = np.roots([a, b, c])
        phi = min(np.real(roots))
        max_deltaP = (n * V1 * V2 * phi * (1 - 2*phi) / fsw / Lmin) - \
                    (n * V1 * V2 * (phi - phase_shift_min) * (1 - 2*(phi - phase_shift_min)) / fsw / Lmin)
    
    if resolution_limited:
        limiter = 'resolution requirement'
    else:
        limiter = 'ZVS condition at minimum power'
    
    # ------------------------------------
    # Upper bound on L for power transfer
    # ------------------------------------
    
    # Maximum L for max power transfer
    phi_max = 0.25
    Lmax = (n * V1 * V2 * 0.25 * (1 - 2*phi_max)) / (P * fsw)
    min_deltaP = (n * V1 * V2 * phi_max * (1 - 2*phi_max) / fsw / Lmax) - \
                (n * V1 * V2 * (phi_max - phase_shift_min) * (1 - 2*(phi_max - phase_shift_min)) / fsw / Lmax)
    
    # Feasibility check on lower/upper bounds
    if Lmax < Lmin:
        warnings.warn(f'Maximum L required to operate at full power is too small, limited by {limiter} - '
                     f'loss model assumes ZVS and will, therefore, be inaccurate', UserWarning)
        
        print(f'Maximum L = {Lmax/1e-6:.2f} µH for phase shift = {phi_max} @ full power: {P}W but will not achieve {limiter}')
        print(f'Resolution @ full power (minimum delta P): {min_deltaP:.2f}W\n')
    else:
        print(f'Minimum L = {Lmin/1e-6:.2f} µH for phase shift = {phi:.4f} @ min power: {P_min}W, limited by {limiter}')
        print('(Based on ZVS and resolution @ min rated power)')
        print(f'Resolution for minimum L (minimum delta P): {max_deltaP:.2f}W\n')
        
        print(f'Maximum L = {Lmax/1e-6:.2f} µH for phase shift = {phi_max} @ full power: {P}W, limited by power transfer requirement')
        print(f'Resolution for maximum L (minimum delta P): {min_deltaP:.2f}W\n')
        print('Operating outside of specified conditions will yield a different operation than is modeled here\n')
        
        # Plot power losses vs resolution for inductance selection
        fig1 = ploss_vs_resolution(P, Lmin, Lmax, fsw, n, V1, V2, Ts, phase_shift_min)
        fig2 = ploss_vs_resolution(P_min, Lmin, Lmax, fsw, n, V1, V2, Ts, phase_shift_min)
        plt.show(block=False)
    
    # ----------------------------
    # Manual inductance selection
    # ----------------------------
    if Ltot is None:
        try:
            Ltot_input = input('Based on the provided information and your available inductance values, please select a total inductance value (in H): ')
            try:
                Ltot = float(Ltot_input)
            except ValueError:
                print('Invalid input. Using midpoint of recommended range.')
                Ltot = (Lmin + Lmax) / 2
        except (EOFError, KeyboardInterrupt):
            # Non-interactive mode or user interruption - use midpoint
            print('Using midpoint of recommended range for non-interactive mode.')
            Ltot = (Lmin + Lmax) / 2
    
    if Ltot < Lmin or Ltot > Lmax:
        print('WARNING: select a value between the recommended bounds to achieve desired operating conditions')
    
    # -----------------------------------------------------------
    # Computation and display of resulting design characteristics
    # -----------------------------------------------------------
    # Calculate operating point at full power
    a = -2
    b = 1
    c = -P * fsw * Ltot / n / V1 / V2
    # Solve for phase shift and controller resolution
    roots = np.roots([a, b, c])
    phi = min(np.real(roots))
    resolution = (n * V1 * V2 * phi * (1 - 2*phi) / fsw / Ltot) - \
                (n * V1 * V2 * (phi - phase_shift_min) * (1 - 2*(phi - phase_shift_min)) / fsw / Ltot)
    
    # Phase shift in seconds
    t_phi = phi * Ts
    
    # Print physical inductor sizing
    Lext = Ltot - Llk
    print(f'Selected inductance is {Ltot*1e6:.2f} µH, due to leakage Llk = {Llk} H, required external inductance is {Lext*1e6:.2f} µH\n')
    print(f'At full power, required phase shift is {phi:.4f} = {t_phi:.2e} seconds and resolution is {resolution:.2f}W')
    
    # Find max power for this inductor
    P_max_inductanceChoice = n * V2 * V1 * 0.25 * (1 - 2*0.25) / fsw / Ltot
    print(f'For inductance choice, the max power that could be operated at is {P_max_inductanceChoice:.2f}W')
    
    # Find full ZVS range
    P_min_inductanceChoice = (n * V2 / Ts) * (2 * Ts * V1 * np.sqrt(Coss_pri) / np.sqrt(Ltot) - 8 * Coss_pri * V1)
    print(f'For inductance choice, the minimum power that could achieve ZVS (resolution requirement not guaranteed) is {P_min_inductanceChoice:.2f}W')
    
    # RMS current on the primary and secondary sides
    I_pri_RMS = Irms_prim_phaseShift(phi, V1, V2, n, fsw, Ltot)
    I_sec_RMS = I_pri_RMS * n
    
    # RMS current running through two switches at all times (assuming negligible dead time)
    pri_Pcond = 2 * Ron_pri * I_pri_RMS**2
    sec_Pcond = 2 * Ron_sec * I_sec_RMS**2
    total_Pcond = pri_Pcond + sec_Pcond
    
    print(f'[At full power, using input inductance value] Expected primary RMS switch currents are: {I_pri_RMS:.2f}A and expected secondary RMS switch currents are: {I_sec_RMS:.2f}A')
    print(f'Conduction losses are predicted to be:\n{pri_Pcond:.2f}W (primary)\n{sec_Pcond:.2f}W (secondary)\n{total_Pcond:.2f}W (total)\n')
    
    # Use all components from loss model to predict efficiency
    Pin = P
    Pout = P - total_Pcond
    nu = (Pout / Pin)
    
    print(f'With current elements of loss model, the predicted efficiency is {nu*100:.2f}% @ full power')
    
    # ---------------------------------------------------------
    # Computation and plot of characteristics over power range
    # ---------------------------------------------------------
    if Lmax >= Lmin:
        fig3 = ploss_vs_P(P_min, P, Ltot, fsw, n, V1, V2)
        plt.show()
    
    return {
        'Lmin': Lmin,
        'Lmax': Lmax,
        'Ltot': Ltot,
        'phi': phi,
        'resolution': resolution,
        'I_pri_RMS': I_pri_RMS,
        'I_sec_RMS': I_sec_RMS,
        'total_Pcond': total_Pcond,
        'efficiency': nu
    }


def main():
    """Example usage of the DAB inductor sizing tool"""
    print("=== DAB Inductor Sizing Tool (Phase Shift Modulation) ===\n")
    
    # Run with default parameters
    # Use None for Ltot to allow automatic selection or user input
    # For non-interactive mode, you can specify a value like: Ltot=200e-6
    results = dab_inductor_sizing_phaseShift()
    
    print("\n=== Design Summary ===")
    print(f"Selected Inductance: {results['Ltot']*1e6:.2f} µH")
    print(f"Phase Shift: {results['phi']:.4f}")
    print(f"Efficiency: {results['efficiency']*100:.2f}%")
    print(f"Total Conduction Losses: {results['total_Pcond']:.2f}W")


if __name__ == "__main__":
    main()
