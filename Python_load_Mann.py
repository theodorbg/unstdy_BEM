# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 12:10:51 2023
This is an example of how to load in a Mann box file and plot the contour and corresponding PSD. 
Use with care! I make many errors!
@author: cgrinde
"""
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

# Load routines stolen from Wind Energy Toolbox on Gitlab: 
#    https://gitlab.windenergy.dtu.dk/toolbox/WindEnergyToolbox/-/blob/master/wetb/wind/turbulence/mann_turbulence.py

def load(filename, N=(32, 32)):
    """Load mann turbulence box

    Parameters
    ----------
    filename : str
        Filename of turbulence box
    N : tuple, (ny,nz) or (nx,ny,nz)
        Number of grid points

    Returns
    -------
    turbulence_box : nd_array

    Examples
    --------
    >>> u = load('turb_u.dat')
    """
    data = np.fromfile(filename, np.dtype('<f'), -1)
    if len(N) == 2:
        ny, nz = N
        nx = len(data) / (ny * nz)
        assert nx == int(nx), "Size of turbulence box (%d) does not match ny x nz (%d), nx=%.2f" % (
            len(data), ny * nz, nx)
        nx = int(nx)
    else:
        nx, ny, nz = N
        assert len(data) == nx * ny * \
            nz, "Size of turbulence box (%d) does not match nx x ny x nz (%d)" % (len(data), nx * ny * nz)
    return data.reshape(nx, ny * nz)


#Example! Make sure to change numbers according to your setup!
#Defining size of box
n1=4096
n2=32
n3=32

Lx=6142.5
Ly=180
Lz=180

umean=8

deltay=Ly/(n2-1)
deltax=Lx/(n1-1)
deltaz=Lz/(n3-1)
deltat=deltax/umean

time=np.arange(deltat, n1*deltat+deltat, deltat)

# Load in the files and reshape them into 3D
u=load("Turbulence_generator/sim1.bin",  N=(n1, n2, n3))

ushp = np.reshape(u, (n1, n2, n3)) 


# Plot a countour
fig,ax=plt.subplots(1,1)
cp = ax.contourf(ushp[1000,:,:])
fig.colorbar(cp) # Add a colorbar to a plot
ax.set_title('Filled Contours Plot')
#ax.set_xlabel('x (cm)')
ax.set_ylabel('y (cm)')
plt.show()


# Picking a point on the velocity plane
sig=ushp[:,20,20]


fs=1/(time[1]-time[0])

#Compute and plot the power spectral density.
# Check out this site for inputs to the Welch
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html 
f, Pxx_den = signal.welch(sig, fs, nperseg=1024)
fig,ax=plt.subplots(1,1)
plt.loglog(f, Pxx_den)
plt.xlabel('frequency [Hz]')
plt.ylabel('PSD ')
plt.show()

# plot time history of wind speed at different positions and the PSD
fig,ax=plt.subplots(1,1, figsize=(12,6))
plt.plot(time, ushp[:,20,20], label="y=20, z=20")
plt.plot(time, ushp[:,10,10], label="y=10, z=10")
plt.xlabel('time [s]')
plt.ylabel('wind speed [m/s]')
plt.legend()
plt.show()

# calculate standard deviation adn turbulence intensity
std_dev=np.std(ushp[:,20,20])
turb_intensity=std_dev/umean
print(f"Standard deviation: {std_dev:.2f} m/s")
print(f"Turbulence intensity: {turb_intensity:.2%}")

# calculate a time series seen from a rotating blade point
# Assume blade is at 0 degrees azimuth (i.e., pointing in the x-direction)
blade_pos_y=0
blade_pos_z=0
blade_sig=ushp[:,blade_pos_y, blade_pos_z]
f_blade, Pxx_den_blade = signal.welch(blade_sig, fs, nperseg=1024)
fig,ax=plt.subplots(1,1)
plt.loglog(f_blade, Pxx_den_blade)
plt.xlabel('frequency [Hz]')
plt.ylabel('PSD ')
plt.title('PSD at blade position (y=0, z=0)')
plt.show()

# plot results in both time and frequency domain
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
ax1.plot(time, blade_sig, label="Blade position (y=0, z=0)")
ax1.plot(time, ushp[:,20,20], label="y=20, z=20")
ax1.set_xlabel('time [s]')
ax1.set_ylabel('wind speed [m/s]')
ax1.legend()
ax2.loglog(f_blade, Pxx_den_blade, label="Blade position (y=0, z=0)")
ax2.loglog(f, Pxx_den, label="y=20, z=20")
ax2.set_xlabel('frequency [Hz]')
ax2.set_ylabel('PSD ')
ax2.legend()
plt.show()