import numpy as np
from scipy.integrate import odeint
from numpy import sin, cos
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


def accel(x, theta, xdot, thetadot):
    """Return [xddot, thetaddot] given current state."""
    M_mat = np.array([[M + m*L,                  -0.5*m*L**2*sin(theta)],
                      [-0.5*m*L**2*sin(theta),    (1/3)*m*L**3         ]])
    F_vec = np.array([0.5*m*L**2*thetadot**2*cos(theta),
                      0.5*m*L**2*g*cos(theta)])
    return np.linalg.solve(M_mat, F_vec)   # [xddot, thetaddot]


# ── Solver (odeint) ───────────────────────────────────────────
def solve_pendulum_odeint(y0, t):
    sol      = odeint(eom, y0, t)
    x        = sol[:, 0]
    xdot     = sol[:, 1]
    theta    = sol[:, 2]
    thetadot = sol[:, 3]

    derivs    = np.array([eom(sol[i], t[i]) for i in range(len(t))])
    xddot     = derivs[:, 1]
    thetaddot = derivs[:, 3]

    return x, theta, xdot, thetadot, xddot, thetaddot


# ── Solver (Runge-Kutta-Nyström 4th order) ────────────────────
def solve_pendulum_RK_Nystrom(y0, t):
    n_steps   = len(t)
    x         = np.zeros(n_steps)
    theta     = np.zeros(n_steps)
    xdot      = np.zeros(n_steps)
    thetadot  = np.zeros(n_steps)
    xddot     = np.zeros(n_steps)
    thetaddot = np.zeros(n_steps)

    # Unpack initial conditions
    x[0], xdot[0], theta[0], thetadot[0] = y0
    xddot[0], thetaddot[0] = accel(x[0], theta[0], xdot[0], thetadot[0])

    for i in range(n_steps - 1):
        dt = t[i+1] - t[i]

        # Current positions, velocities, accelerations
        q   = np.array([x[i],    theta[i]])
        qd  = np.array([xdot[i], thetadot[i]])
        qdd = np.array([xddot[i], thetaddot[i]])

        def g(q_, qd_):
            return accel(q_[0], q_[1], qd_[0], qd_[1])

        # ── RKN4 stages ──────────────────────────────────────
        A = dt/2 * qdd
        b = dt/2 * (qd + 0.5*A)

        B = dt/2 * g(q + b,          qd + A)
        C = dt/2 * g(q + b,          qd + B)
        D = dt   * g(q + dt*(qd + C), qd + 2*C)

        # ── Advance ──────────────────────────────────────────
        q_new   = q  + dt*(qd + (1/3)*(A + B + C))
        qd_new  = qd + (1/3)*(A + 2*B + 2*C + D)
        qdd_new = g(q_new, qd_new)

        x[i+1]         = q_new[0]
        theta[i+1]     = q_new[1]
        xdot[i+1]      = qd_new[0]
        thetadot[i+1]  = qd_new[1]
        xddot[i+1]     = qdd_new[0]
        thetaddot[i+1] = qdd_new[1]

    return x, theta, xdot, thetadot, xddot, thetaddot


if __name__ == "__main__":
    # Same initial conditions and time grid for both solvers
    y0 = [0.0, 0.0, 0.1, 0.0]
    t  = np.linspace(0, 10, 2000)

    x_o,  th_o,  xd_o,  thd_o,  xdd_o,  thdd_o  = solve_pendulum_odeint(y0, t)
    x_r,  th_r,  xd_r,  thd_r,  xdd_r,  thdd_r  = solve_pendulum_RK_Nystrom(y0, t)

    fig, axs = plt.subplots(3, 2, figsize=(10, 8), sharex=True)

    # Positions
    axs[0, 0].plot(t, x_o,  label="odeint")
    axs[0, 0].plot(t, x_r,  "--", label="RKN4")
    axs[0, 0].set_ylabel("x [m]")

    axs[0, 1].plot(t, th_o, label="odeint")
    axs[0, 1].plot(t, th_r, "--", label="RKN4")
    axs[0, 1].set_ylabel("theta [rad]")

    # Velocities
    axs[1, 0].plot(t, xd_o)
    axs[1, 0].plot(t, xd_r, "--")
    axs[1, 0].set_ylabel("xdot [m/s]")

    axs[1, 1].plot(t, thd_o)
    axs[1, 1].plot(t, thd_r, "--")
    axs[1, 1].set_ylabel("thetadot [rad/s]")

    # Accelerations
    axs[2, 0].plot(t, xdd_o)
    axs[2, 0].plot(t, xdd_r, "--")
    axs[2, 0].set_ylabel("xddot [m/s²]")

    axs[2, 1].plot(t, thdd_o)
    axs[2, 1].plot(t, thdd_r, "--")
    axs[2, 1].set_ylabel("thetaddot [rad/s²]")

    axs[2, 0].set_xlabel("t [s]")
    axs[2, 1].set_xlabel("t [s]")

    axs[0, 0].legend(loc="upper right")
    fig.suptitle("odeint vs RKN4 for cart–pendulum", fontsize=12)
    fig.tight_layout()
    plt.show()