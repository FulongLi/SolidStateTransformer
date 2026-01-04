"""
Solid State Transformer (SST) Analysis and Simulation Module

This module provides comprehensive analysis tools for Solid State Transformer
design, simulation, and performance evaluation.

Author: Fulong Li
License: CC BY 4.0
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class SSTParameters:
    """Data class for SST system parameters"""
    input_voltage: float = 400.0  # VAC (line-to-line, 3-phase)
    output_voltage: float = 208.0  # VAC (line-to-line)
    power_rating: float = 10.0  # kW
    switching_frequency: float = 50.0  # kHz
    efficiency: float = 0.95  # 95%
    thd_limit: float = 0.03  # 3%


class SSTAnalyzer:
    """Main class for SST analysis and simulation"""
    
    def __init__(self, params: SSTParameters):
        """
        Initialize SST analyzer with system parameters
        
        Args:
            params: SSTParameters object containing system specifications
        """
        self.params = params
        self.fundamental_freq = 60.0  # Hz (grid frequency)
        
    def calculate_power_losses(self, output_power: float) -> dict:
        """
        Calculate power losses in the SST system
        
        Args:
            output_power: Output power in kW
            
        Returns:
            Dictionary containing various loss components
        """
        total_loss = output_power * (1 - self.params.efficiency) / self.params.efficiency
        
        # Estimate loss distribution (typical for SST)
        switching_losses = total_loss * 0.35  # 35% switching losses
        conduction_losses = total_loss * 0.30  # 30% conduction losses
        magnetic_losses = total_loss * 0.20    # 20% magnetic/core losses
        other_losses = total_loss * 0.15       # 15% other losses
        
        return {
            'total_loss': total_loss,
            'switching_losses': switching_losses,
            'conduction_losses': conduction_losses,
            'magnetic_losses': magnetic_losses,
            'other_losses': other_losses,
            'input_power': output_power + total_loss
        }
    
    def calculate_dc_link_voltage(self) -> float:
        """
        Calculate required DC link voltage for the rectifier stage
        
        Returns:
            DC link voltage in volts
        """
        # For 3-phase rectifier: Vdc ≈ 1.35 * Vline-to-line
        vdc = 1.35 * self.params.input_voltage * np.sqrt(2)
        return vdc
    
    def calculate_transformer_turns_ratio(self) -> float:
        """
        Calculate transformer turns ratio for DC-DC isolation stage
        
        Returns:
            Turns ratio (N2/N1)
        """
        vdc_in = self.calculate_dc_link_voltage()
        # Assuming similar DC link on output side
        vdc_out = 1.35 * self.params.output_voltage * np.sqrt(2)
        turns_ratio = vdc_out / vdc_in
        return turns_ratio
    
    def calculate_switching_losses(self, output_power: float, 
                                   mosfet_params: Optional[dict] = None) -> float:
        """
        Calculate switching losses based on MOSFET parameters
        
        Args:
            output_power: Output power in kW
            mosfet_params: Dictionary with MOSFET parameters (optional)
            
        Returns:
            Switching losses in kW
        """
        if mosfet_params is None:
            # Default SiC MOSFET parameters
            mosfet_params = {
                'E_on': 0.5,  # mJ (turn-on energy)
                'E_off': 0.3,  # mJ (turn-off energy)
                'V_ds': 600,   # V (drain-source voltage)
                'I_d': 20,     # A (drain current)
            }
        
        # Switching frequency in Hz
        f_sw = self.params.switching_frequency * 1000
        
        # Number of switches (assuming full-bridge topology)
        n_switches = 8  # 6 for rectifier + 2 for inverter (simplified)
        
        # Switching losses per switch
        P_sw_per_switch = (mosfet_params['E_on'] + mosfet_params['E_off']) * f_sw / 1000
        
        # Total switching losses
        total_switching_losses = P_sw_per_switch * n_switches / 1000  # Convert to kW
        
        return total_switching_losses
    
    def harmonic_analysis(self, waveform: np.ndarray, 
                         sampling_rate: float = 10000) -> dict:
        """
        Perform harmonic analysis on a waveform
        
        Args:
            waveform: Time-domain waveform array
            sampling_rate: Sampling rate in Hz
            
        Returns:
            Dictionary containing THD and harmonic components
        """
        # FFT analysis
        fft_result = np.fft.fft(waveform)
        fft_freq = np.fft.fftfreq(len(waveform), 1/sampling_rate)
        
        # Get magnitude spectrum
        magnitude = np.abs(fft_result)
        
        # Find fundamental frequency component
        fundamental_idx = np.argmax(magnitude[1:len(magnitude)//2]) + 1
        fundamental_mag = magnitude[fundamental_idx]
        
        # Calculate THD
        harmonic_power = np.sum(magnitude[fundamental_idx*2:]**2)
        thd = np.sqrt(harmonic_power) / fundamental_mag
        
        # Extract harmonic components
        harmonics = {}
        for i in range(2, 10):  # 2nd to 9th harmonic
            harmonic_idx = fundamental_idx * i
            if harmonic_idx < len(magnitude):
                harmonics[f'h{i}'] = magnitude[harmonic_idx] / fundamental_mag
        
        return {
            'thd': thd,
            'fundamental_frequency': fft_freq[fundamental_idx],
            'harmonics': harmonics
        }
    
    def generate_sine_wave(self, amplitude: float, frequency: float,
                          duration: float, sampling_rate: float = 10000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a sine wave for simulation
        
        Args:
            amplitude: Waveform amplitude in volts
            frequency: Frequency in Hz
            duration: Duration in seconds
            sampling_rate: Sampling rate in Hz
            
        Returns:
            Tuple of (time_array, waveform_array)
        """
        t = np.linspace(0, duration, int(sampling_rate * duration))
        waveform = amplitude * np.sin(2 * np.pi * frequency * t)
        return t, waveform
    
    def plot_power_analysis(self, output_power_range: np.ndarray):
        """
        Plot power analysis over a range of output powers
        
        Args:
            output_power_range: Array of output power values in kW
        """
        losses = [self.calculate_power_losses(p) for p in output_power_range]
        total_losses = [l['total_loss'] for l in losses]
        efficiencies = [p / (p + l['total_loss']) * 100 for p, l in zip(output_power_range, losses)]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot losses
        ax1.plot(output_power_range, total_losses, 'r-', linewidth=2)
        ax1.set_xlabel('Output Power (kW)')
        ax1.set_ylabel('Total Losses (kW)')
        ax1.set_title('Power Losses vs Output Power')
        ax1.grid(True, alpha=0.3)
        
        # Plot efficiency
        ax2.plot(output_power_range, efficiencies, 'b-', linewidth=2)
        ax2.set_xlabel('Output Power (kW)')
        ax2.set_ylabel('Efficiency (%)')
        ax2.set_title('Efficiency vs Output Power')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=self.params.efficiency * 100, color='r', 
                   linestyle='--', label='Target Efficiency')
        ax2.legend()
        
        plt.tight_layout()
        return fig
    
    def thermal_analysis(self, output_power: float, 
                        ambient_temp: float = 25.0) -> dict:
        """
        Perform basic thermal analysis
        
        Args:
            output_power: Output power in kW
            ambient_temp: Ambient temperature in °C
            
        Returns:
            Dictionary with thermal parameters
        """
        losses = self.calculate_power_losses(output_power)
        
        # Estimate junction temperature (simplified model)
        # Assuming thermal resistance Rth = 0.5 K/W per kW
        thermal_resistance = 0.5  # K/kW
        temp_rise = losses['total_loss'] * thermal_resistance
        junction_temp = ambient_temp + temp_rise
        
        return {
            'ambient_temperature': ambient_temp,
            'junction_temperature': junction_temp,
            'temperature_rise': temp_rise,
            'thermal_resistance': thermal_resistance
        }


def main():
    """Example usage of the SST analyzer"""
    
    # Create SST parameters
    params = SSTParameters(
        input_voltage=400.0,
        output_voltage=208.0,
        power_rating=10.0,
        switching_frequency=50.0,
        efficiency=0.95,
        thd_limit=0.03
    )
    
    # Initialize analyzer
    analyzer = SSTAnalyzer(params)
    
    # Calculate key parameters
    print("=== Solid State Transformer Analysis ===\n")
    print(f"DC Link Voltage: {analyzer.calculate_dc_link_voltage():.2f} V")
    print(f"Transformer Turns Ratio: {analyzer.calculate_transformer_turns_ratio():.3f}")
    
    # Power loss analysis
    output_power = 10.0  # kW
    losses = analyzer.calculate_power_losses(output_power)
    print(f"\n=== Power Loss Analysis (Output: {output_power} kW) ===")
    print(f"Total Losses: {losses['total_loss']:.3f} kW")
    print(f"Switching Losses: {losses['switching_losses']:.3f} kW")
    print(f"Conduction Losses: {losses['conduction_losses']:.3f} kW")
    print(f"Magnetic Losses: {losses['magnetic_losses']:.3f} kW")
    print(f"Input Power: {losses['input_power']:.3f} kW")
    
    # Thermal analysis
    thermal = analyzer.thermal_analysis(output_power)
    print(f"\n=== Thermal Analysis ===")
    print(f"Junction Temperature: {thermal['junction_temperature']:.2f} °C")
    print(f"Temperature Rise: {thermal['temperature_rise']:.2f} °C")
    
    # Harmonic analysis example
    t, waveform = analyzer.generate_sine_wave(120.0, 60.0, 0.1)
    # Add some harmonics for demonstration
    waveform += 5.0 * np.sin(2 * np.pi * 120.0 * t)  # 2nd harmonic
    waveform += 2.0 * np.sin(2 * np.pi * 180.0 * t)  # 3rd harmonic
    
    harmonic_result = analyzer.harmonic_analysis(waveform)
    print(f"\n=== Harmonic Analysis ===")
    print(f"THD: {harmonic_result['thd']*100:.2f}%")
    print(f"Fundamental Frequency: {harmonic_result['fundamental_frequency']:.2f} Hz")
    
    # Plot power analysis
    power_range = np.linspace(1, params.power_rating, 50)
    fig = analyzer.plot_power_analysis(power_range)
    plt.savefig('sst_power_analysis.png', dpi=150, bbox_inches='tight')
    print("\nPower analysis plot saved as 'sst_power_analysis.png'")


if __name__ == "__main__":
    main()

