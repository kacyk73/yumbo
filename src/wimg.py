import glb
import io
import matplotlib
import numpy as np
import pandas as pd
import streamlit as st
import time

#
# Invoicing Periods Workload
#
def plot(expert_name):
    time_start = time.perf_counter()

    invper = glb.data["invoicing periods"]
    schedule = glb.data[f"schedule {expert_name}"]
    invper_bounds = glb.data["invoicing periods bounds"]

    # Filter the bounds for the given expert
    bounds = invper_bounds[ invper_bounds["Expert"] == expert_name ]
    assert bounds["Lower"].dtype == bounds["Upper"].dtype
    dtype = bounds["Lower"].dtype


    if bounds.empty:
        st.write(":green[No limits have been set for the invoicing periods.]")
        return

    # Precompute invoicing period start and end as a dictionary for quick lookup
    invper_dict = invper.set_index("Name")[["Start", "End"]].to_dict("index")

    # Calculate workload for each period
    y = np.empty(bounds.shape[0], dtype=dtype)
    for idx, period in enumerate(bounds["Period"]):
        period_data = invper_dict[period]
        start = pd.Timestamp(period_data["Start"])
        end = pd.Timestamp(period_data["End"])
        x_task = pd.date_range(start=start, end=end, freq="D").intersection(schedule.columns)
        y[idx] = schedule.loc[:, x_task].sum().sum()

    ylower = bounds["Lower"].to_numpy(dtype=dtype)
    yupper = bounds["Upper"].to_numpy(dtype=dtype)
    yerr = np.array([y - ylower, yupper - y], dtype=dtype)

    # Create the plot
    fig = matplotlib.figure.Figure(figsize=(glb.wimg("Width"), glb.wimg("Height")))
    ax = fig.subplots()
    ax.set_ylabel("Hours")
    ax.set_title("Invoicing Periods Workload")
    ax.bar(
        bounds["Period"],
        y,
        yerr=yerr,
        color=glb.wimg("Bar:color"),
        ecolor=glb.wimg("Bar:ecolor"),
        capsize=glb.wimg("Bar:capsize"),
    )
    ax.tick_params(axis="x", rotation=0, labelsize="x-small")
    ax.tick_params(axis="y", labelsize="x-small")

    # Finalize and display the plot
    fig.tight_layout()
    with io.BytesIO() as buf:
        fig.savefig(buf, format="png", dpi=glb.wimg("Dpi"), pil_kwargs={"compress_level": 1})
        buf.seek(0)
        st.image(buf)

    time_end = time.perf_counter()
    glb.data["time:wimg:cnt"] += 1
    glb.data["time:wimg:val"] += time_end - time_start
