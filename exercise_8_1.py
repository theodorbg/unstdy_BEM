import numpy as np
from scipy.integrate import odeint
from numpy import sin, cos
from plots import *
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ── Parameters ────────────────────────────────────────────────
M, m, L, g = 1.0, 0.5, 2.0, 9.81

# ── Equations of Motion ───────────────────────────────────────
def eom(y, t):
    x, xdot, theta, thetadot = y

    M_mat = np.array([[M + m*L,                  -0.5*m*L**2*sin(theta)],
                      [-0.5*m*L**2*sin(theta),    (1/3)*m*L**3         ]])

    F_vec = np.array([0.5*m*L**2*thetadot**2*cos(theta),
                      0.5*m*L**2*g*cos(theta)])

    xddot, thetaddot = np.linalg.solve(M_mat, F_vec)
    return [xdot, xddot, thetadot, thetaddot]

# ── Solver ────────────────────────────────────────────────────
def solve_pendulum(y0, t):
    sol      = odeint(eom, y0, t)
    x        = sol[:, 0]
    xdot     = sol[:, 1]
    theta    = sol[:, 2]
    thetadot = sol[:, 3]

    derivs    = np.array([eom(sol[i], t[i]) for i in range(len(t))])
    xddot     = derivs[:, 1]
    thetaddot = derivs[:, 3]

    return x, theta, xdot, thetadot, xddot, thetaddot

# ── Solve ─────────────────────────────────────────────────────
y0 = [0.0, 0.0, 0.1, 0.0]
t  = np.linspace(0, 10, 2000)
x, theta, xdot, thetadot, xddot, thetaddot = solve_pendulum(y0, t)

# ── Static Plots ──────────────────────────────────────────────
plot_flexible(
    t,
    [
        [x, theta],
        [xdot, thetadot],
        [xddot, thetaddot]
    ],
    [["Position of cart", "Angle of pendulum"],
     ["Velocity of cart", "Angular velocity of pendulum"],
     ["Acceleration of cart", "Angular acceleration of pendulum"]],
    "Time (s)",
    ["x Position of cart [m] / Angle of pendulum [rad]",
     "Velocity of cart [m/s] / Angular velocity of pendulum [rad/s]",
     "Acceleration of cart [m/s^2] / Angular acceleration of pendulum [rad/s^2]"],
    save_name="pendulum_solution.png"
)

# ── Animation Setup ───────────────────────────────────────────
# Cartesian coordinates of pivot and pendulum tip
piv_x = x                            # pivot follows cart
tip_x = piv_x + L * cos(theta)
tip_y =        -L * sin(theta)

cart_w, cart_h = 0.4, 0.25
x_min = min(x) - 1.5
x_max = max(x) + L + 1.5

fig_anim, ax = plt.subplots(figsize=(10, 5))
ax.set_facecolor('#1a1a2e')
fig_anim.patch.set_facecolor('#1a1a2e')
ax.set_xlim(x_min, x_max)
ax.set_ylim(-L - 0.5, L + 0.5)
ax.set_aspect('equal')
ax.axhline(0, color='#444466', linewidth=1.5, linestyle='--')
ax.set_title('Cart-Pendulum Non-linear EoM', color='white', fontsize=13)
ax.tick_params(colors='white')
for spine in ax.spines.values():
    spine.set_edgecolor('#444466')

# Ground, cart, wheels
ax.add_patch(plt.Rectangle((x_min, -0.08), x_max - x_min, 0.08, color='#2d2d4e'))
cart_patch = plt.Rectangle((0, -cart_h), cart_w, cart_h, color='#4e8cff', zorder=3)
ax.add_patch(cart_patch)
wheel1 = plt.Circle((0, 0), 0.07, color='#aaaacc', zorder=4)
wheel2 = plt.Circle((0, 0), 0.07, color='#aaaacc', zorder=4)
ax.add_patch(wheel1)
ax.add_patch(wheel2)

# Rod, bob, trail
rod_line,   = ax.plot([], [], color='#ff9f43', linewidth=3,  zorder=5)
bob,        = ax.plot([], [], 'o', color='#ff6b6b', markersize=10, zorder=6)
trail_line, = ax.plot([], [], color='#ff6b6b', linewidth=0.8, alpha=0.4, zorder=2)
time_text   = ax.text(x_min + 0.1, 0.75, '', color='white', fontsize=10)

trail_x, trail_y = [], []

# ── Animation Functions ───────────────────────────────────────
def init():
    rod_line.set_data([], [])
    bob.set_data([], [])
    trail_line.set_data([], [])
    return rod_line, bob, cart_patch, wheel1, wheel2, trail_line

def update(i):
    cx = x[i] - cart_w / 2
    cart_patch.set_xy((cx, -cart_h))
    wheel1.center = (cx + 0.1,          -cart_h - 0.04)
    wheel2.center = (cx + cart_w - 0.1, -cart_h - 0.04)

    rod_line.set_data([piv_x[i], tip_x[i]], [0, tip_y[i]])
    bob.set_data([tip_x[i]], [tip_y[i]])

    trail_x.append(tip_x[i])
    trail_y.append(tip_y[i])
    trail_line.set_data(trail_x, trail_y)

    time_text.set_text(f't = {t[i]:.2f} s')
    return rod_line, bob, cart_patch, wheel1, wheel2, trail_line, time_text

# ── Run & Save ────────────────────────────────────────────────
ani = animation.FuncAnimation(fig_anim, update, frames=len(t),
                               init_func=init, interval=40, blit=True)
ani.save('pendulum_animation.gif', writer='pillow', fps=25)
plt.close(fig_anim)
