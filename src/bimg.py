import io
import streamlit as st
import matplotlib
import romz_datetime
import pandas as pd
import glb
import time

#
# Plot task with its constrains
#

def plot(task, schedule, bounds):
    time_start = time.perf_counter()

    # Generate task-specific data
    x_task = pd.date_range(start=task.Start, end=task.End, freq="D")
    y_task = schedule.loc[task.Name, x_task]

    # Create figure and axis
    fig = matplotlib.figure.Figure(figsize=(glb.bimg("Width"), glb.bimg("Height")))
    ax = fig.subplots()

    # Plot task data
    ax.plot(x_task, y_task, glb.bimg("Plot:format"), markeredgewidth=glb.bimg("Plot:markeredgewidth"), label=f"Task {task.Name}")
    ax.step(x_task, y_task, linewidth=glb.bimg("Step:linewidth"), where="mid")

    # Configure grid and axis properties
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5, integer=True))
    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))
    ax.yaxis.grid(alpha=0.5)
    ax.set_axisbelow(True)
    ax.set_xlim([x_task[0], x_task[-1]])
    ax.tick_params(axis="x", labelsize="x-small")
    ax.tick_params(axis="y", labelsize="x-small")

    # Add task bounds
    for row in bounds.itertuples(index=False):
        bound_days = pd.date_range(start=row.Start, end=row.End, freq="D")
        ax.fill_between(bound_days,
                        row.Lower,
                        row.Upper,
                        color=glb.bimg("Fill:color"),
                        hatch=glb.bimg("Fill:hatch"),
                        alpha=glb.bimg("Fill:alpha")
                        )

    # Add legend and finalize layout
    ax.legend(loc="upper right")
    fig.tight_layout()

    # Save and display the plot
    with io.BytesIO() as buf:
        fig.savefig(buf, format="png", dpi=glb.bimg("Dpi"), pil_kwargs={"compress_level": 1})
        buf.seek(0)
        st.image(buf)

    time_end = time.perf_counter()
    glb.data["time:bimg:cnt"] += 1
    glb.data["time:bimg:val"] += time_end - time_start
