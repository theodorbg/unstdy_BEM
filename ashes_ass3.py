from load_ashes import load_ashes

ashes_18ms = load_ashes(
    r"C:\Users\tgilh\OneDrive\Dokumenter\Ashes 3.31\46310\Assignment 3\18ms"
)
ashes_7ms = load_ashes(
    r"C:\Users\tgilh\OneDrive\Dokumenter\Ashes 3.31\46310\Assignment 3\7ms"
)

# Access like: ashes_18ms.bladex.direction
ashes_18ms.blade1.time   # time array [s]
ashes_18ms.blade1.z      # out-of-plane tip deflection [m]
ashes_18ms.blade1.y      # in-plane tip deflection [m]

ashes_18ms.blade2.z
ashes_18ms.blade3.y

import matplotlib.pyplot as plt

# add 7ms and plot together with 18ms for comparison
# for blade, label in [(ashes_18ms.blade1, "Blade 1_18ms"),
#                      (ashes_18ms.blade2, "Blade 2_18ms"),
#                      (ashes_18ms.blade3, "Blade 3_18ms")]:
#     plt.plot(blade.time, blade.z, label=label)

# for blade, label in [(ashes_7ms.blade1, "Blade 1_7ms"),
#                      (ashes_7ms.blade2, "Blade 2_7ms"),
#                      (ashes_7ms.blade3, "Blade 3_7ms")]:
#     plt.plot(blade.time, blade.z, label=label)
# create subplot with 2 rows and 1 column, share x-axis
fig, axs = plt.subplots(2, 1, sharex=True, figsize=(10, 8))
plt.title("Ashes: Blade 1 tip deflection comparison")
# Plot out-of-plane deflection for blade 1 in both cases
axs[0].plot(ashes_18ms.blade1.time, ashes_18ms.blade1.z, label="Blade 1_18ms")
axs[0].plot(ashes_7ms.blade1.time, ashes_7ms.blade1.z, label="Blade 1_7ms")
axs[0].set_ylabel("Tip deflection flapwise [m]")
axs[0].legend()
# Plot in-plane deflection for blade 1 in both cases
axs[1].plot(ashes_18ms.blade1.time, ashes_18ms.blade1.y, label="Blade 1_18ms")
axs[1].plot(ashes_7ms.blade1.time, ashes_7ms.blade1.y, label="Blade 1_7ms")
axs[1].set_xlabel("Time [s]")
axs[1].set_ylabel("Tip deflection edgewise [m]")
axs[1].legend()
plt.tight_layout()
plt.show()