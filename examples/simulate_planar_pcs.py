import jax

from jsrm.systems.planar_pcs import PlanarPCS
import jax.numpy as jnp

from typing import Callable
from jax import Array

import numpy as onp

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML

from diffrax import Tsit5

from functools import partial
from matplotlib.widgets import Slider

jax.config.update("jax_enable_x64", True)  # double precision
jnp.set_printoptions(
    threshold=jnp.inf,
    linewidth=jnp.inf,
    formatter={"float_kind": lambda x: "0" if x == 0 else f"{x:.2e}"},
)


def draw_robot_curve(
    robot: PlanarPCS,
    q: Array,
    num_points: int = 50,
):
    batched_forward_kinematics = jax.vmap(
        robot.forward_kinematics, in_axes=(None, 0), out_axes=-1
    )
    
    s_ps = jnp.linspace(0, robot.Lmax, num_points)
    chi_ps = batched_forward_kinematics(q, s_ps)

    curve = onp.array(chi_ps[1:, :], dtype=onp.float32).T

    return curve  # (N, 2)


def animate_robot_matplotlib(
    robot: PlanarPCS,
    t_list: Array,  # shape (T,)
    q_list: Array,  # shape (T, DOF)
    num_points: int = 50,
    interval: int = 50,
    slider: bool = None,
    animation: bool = None,
    show: bool = True,
):
    if slider is None and animation is None:
        raise ValueError("Either 'slider' or 'animation' must be set to True.")
    if animation and slider:
        raise ValueError(
            "Cannot use both animation and slider at the same time. Choose one."
        )

    width = jnp.linalg.norm(robot.L) * 3
    height = width

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax_slider = fig.add_axes([0.2, 0.05, 0.6, 0.03])  # [left, bottom, width, height]

    if animation:
        (line,) = ax.plot([], [], lw=4, color="blue")
        ax.set_xlim(-width / 2, width / 2)
        ax.set_ylim(0, height)
        title_text = ax.set_title("t = 0.00 s")

        def init():
            line.set_data([], [])
            title_text.set_text("t = 0.00 s")
            return line, title_text

        def update(frame_idx):
            q = q_list[frame_idx]
            t = t_list[frame_idx]
            curve = draw_robot_curve(robot, q, num_points)
            line.set_data(curve[:, 0], curve[:, 1])
            title_text.set_text(f"t = {t:.2f} s")
            return line, title_text

        ani = FuncAnimation(
            fig,
            update,
            frames=len(q_list),
            init_func=init,
            blit=False,
            interval=interval,
        )

        if show:
            plt.show()
        plt.close(fig)
        return HTML(ani.to_jshtml())

    elif slider:

        def update_plot(frame_idx):
            ax.cla()  # Clear current axes
            ax.set_xlim(-width / 2, width / 2)
            ax.set_ylim(0, height)
            ax.set_xlabel("X [m]")
            ax.set_ylabel("Y [m]")
            ax.set_title(f"t = {t_list[frame_idx]:.2f} s")
            q = q_list[frame_idx]
            curve = draw_robot_curve(robot, q, num_points)
            ax.plot(curve[:, 0], curve[:, 1], lw=4, color="blue")
            fig.canvas.draw_idle()

        # Create slider
        slider = Slider(
            ax=ax_slider,
            label="Frame",
            valmin=0,
            valmax=len(t_list) - 1,
            valinit=0,
            valstep=1,
        )
        slider.on_changed(update_plot)

        update_plot(0)  # Initial plot

        if show:
            plt.show()

        plt.close(fig)
        return HTML(
            "Slider animation not implemented in HTML format. Use matplotlib directly to view the slider."
        )  # Slider cannot be converted to HTML


if __name__ == "__main__":
    num_segments = 2
    rho = 1070 * jnp.ones(
        (num_segments,)
    )  # Volumetric density of Dragon Skin 20 [kg/m^3]
    params = {
        "th0": jnp.array(0.0),  # initial orientation angle [rad]
        "l": 1e-1 * jnp.ones((num_segments,)),
        "r": 2e-2 * jnp.ones((num_segments,)),
        "rho": rho,
        "g": jnp.array([0.0, -9.81]),
        "E": 2e3 * jnp.ones((num_segments,)),  # Elastic modulus [Pa]
        "G": 1e3 * jnp.ones((num_segments,)),  # Shear modulus [Pa]
    }
    params["D"] = 1e-3 * jnp.diag(
        (
            jnp.repeat(jnp.array([[1e0, 1e3, 1e3]]), num_segments, axis=0)
            * params["l"][:, None]
        ).flatten()
    )

    # ======================================================
    # Robot initialization
    # ======================================================
    robot = PlanarPCS(
        num_segments=num_segments,
        params=params,
        order_gauss=5,
    )

    # =====================================================
    # Simulation upon time
    # =====================================================
    # Initial configuration
    q0 = jnp.repeat(
        jnp.array([5.0 * jnp.pi, 0.1, 0.2])[None, :], num_segments, axis=0
    ).flatten()
    # Initial velocities
    qd0 = jnp.zeros_like(q0)

    # Actuation parameters
    tau = jnp.zeros_like(q0)
    # WARNING: actuation_args need to be a tuple, even if it contains only one element
    actuation_args = (tau,)

    # Simulation time parameters
    t0 = 0.0
    t1 = 2.0
    dt = 1e-4
    skip_step = 100  # how many time steps to skip in between video frames

    # Solver
    solver = Tsit5()  # Runge-Kutta 5(4) method

    ts, q_ts, qd_ts = robot.resolve_upon_time(
        q0=q0,
        qd0=qd0,
        actuation_args=actuation_args,
        t0=t0,
        t1=t1,
        dt=dt,
        skip_steps=skip_step,
        solver=solver,
        max_steps=None,
    )

    # =====================================================
    # End-effector position upon time
    # =====================================================
    forward_kinematics_end_effector = jax.jit(
        partial(
            robot.forward_kinematics,
            s=jnp.sum(robot.L),  # end-effector position
        )
    )
    chi_ee_ts = jax.vmap(forward_kinematics_end_effector)(q_ts)

    plt.figure()
    plt.plot(ts, chi_ee_ts[:, 1], label="End-effector x [m]")
    plt.plot(ts, chi_ee_ts[:, 2], label="End-effector y [m]")
    plt.xlabel("Time [s]")
    plt.ylabel("End-effector position [m]")
    plt.legend()
    plt.grid(True)
    plt.box(True)
    plt.tight_layout()
    plt.show()

    plt.figure()
    plt.scatter(chi_ee_ts[:, 1], chi_ee_ts[:, 2], c=ts, cmap="viridis")
    plt.axis("equal")
    plt.grid(True)
    plt.xlabel("End-effector x [m]")
    plt.ylabel("End-effector y [m]")
    plt.colorbar(label="Time [s]")
    plt.tight_layout()
    plt.show()

    # =====================================================
    # Energy computation upon time
    # =====================================================
    U_ts = jax.vmap(jax.jit(partial(robot.potential_energy)))(q_ts)
    T_ts = jax.vmap(jax.jit(partial(robot.kinetic_energy)))(q_ts, qd_ts)

    plt.figure()
    plt.plot(ts, U_ts, label="Potential Energy")
    plt.plot(ts, T_ts, label="Kinetic Energy")
    plt.xlabel("Time (s)")
    plt.ylabel("Energy (J)")
    plt.legend()
    plt.title("Energy over Time")
    plt.grid(True)
    plt.box(True)
    plt.tight_layout()
    plt.show()

    # =====================================================
    # Plot the robot configuration upon time
    # =====================================================
    animate_robot_matplotlib(
        robot=robot,
        t_list=ts,  # shape (T,)
        q_list=q_ts,  # shape (T, DOF)
        num_points=50,
        interval=100,  # ms
        slider=True,
    )
