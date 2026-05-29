import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

class SpringMassDamperSystem:
    def __init__(self,
                 k=2,
                 m=0.5,
                 damping_ratio=0.2,
                 force_amplitude=3.0,
                 force_frequency_fraction=0.95,
                 x_stat=1.5):
        self.k = k  # spring stiffness
        self.m = m  # mass
        self.damping_ratio = damping_ratio
        self.force_amplitude = force_amplitude  # amplitude of the external force
        self.x_stat = x_stat  # static displacement
        self.omega_natural = np.sqrt(k / m)  # natural frequency
        self.damping_factor = damping_ratio * 2 * self.omega_natural
        self.forcing_frequency = force_frequency_fraction * self.omega_natural  # forcing frequency (resonance)

    def eom(self, t, z):
            x, x_dot = z
            F = self.force_amplitude * np.sin(self.forcing_frequency * t)
            x_ddot = (F - self.damping_factor * x_dot - self.k * x) / self.m
            return [x_dot, x_ddot]

    def solve(self, t_span=(0, 50), initial_conditions=(0, 0)):
        t = np.linspace(t_span[0], t_span[1], 5000)
        z = solve_ivp(self.eom, t_span, initial_conditions, t_eval=t, method='RK45')
        return z.t, z.y.T

    def plot(self, t, z):
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(t, z[:, 0] * self.k / self.force_amplitude)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('x·k / F  (dynamic amplification)')
        ax.set_title('Spring-Mass-Damper: Normalized Displacement')
        ax.grid(True)
        plt.tight_layout()
        plt.show()
        
    def plot_daf(self, t, z):
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(t, z[:, 0] / self.x_stat)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Dynamic Amplification Factor (DAF)')
        ax.set_title('Spring-Mass-Damper: Dynamic Amplification Factor')
        ax.grid(True)
        plt.tight_layout()
        plt.show()
    
    # def plot_daf_omega(self, z):
    #     fig, ax = plt.subplots(figsize=(10, 5))
    #     ax.plot(self.forcing_frequency / self.omega_natural, z[:, 0] / self.x_stat)
    #     ax.set_xlabel('Forcing Frequency / Natural Frequency')
    #     ax.set_ylabel('Dynamic Amplification Factor (DAF)')
    #     ax.set_title('Spring-Mass-Damper: Dynamic Amplification Factor')
    #     ax.grid(True)
    #     plt.tight_layout()
    #     plt.show()
        

sys = SpringMassDamperSystem()
t, z = sys.solve()
# sys.plot(t, z)
sys.plot_daf(t, z)
# sys.plot_daf_omega(z)