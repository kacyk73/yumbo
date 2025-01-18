import pandas as pd
import io
import streamlit as st
import matplotlib
from matplotlib.figure import Figure
import matplotlib.ticker as tck
import romz_datetime
import datetime
import glb

def plot(df, start_day, end_day):
    # Ensure end_day is not before start_day
    end_day = max(end_day, start_day)

    # Generate the date range as string
    days = pd.period_range(start=start_day, end=end_day, freq="D").astype(str)

    # Count the number of tasks per day
    tasks_per_day = (df[days] > 0).sum()

    # Calculate plot limits
    left = matplotlib.dates.date2num(romz_datetime.from_string(days[0]) - datetime.timedelta(days=1))
    right = matplotlib.dates.date2num(romz_datetime.from_string(days[-1]) + datetime.timedelta(days=1))
    days = matplotlib.dates.datestr2num(days)

    # Determine bar width
    width = 0.9 if days.size < 10 else 1.0

    # Create figure and axis
    fig = Figure(figsize=(8, 4))
    ax = fig.subplots()

    # Configure plot properties
    ax.set_title("Tasks per day")
    ax.set_xlim([left, right])
    ax.yaxis.set_major_locator(tck.MaxNLocator(nbins=6, min_n_ticks=1, integer=True))
    ax.xaxis.set_major_locator(matplotlib.dates.AutoDateLocator(minticks=3, maxticks=6, interval_multiples=True))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter(romz_datetime.format()))
    ax.yaxis.grid(alpha=0.4)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelsize="x-small")
    ax.tick_params(axis="y", labelsize="x-small")

    # Add bars to the plot
    ax.bar(days, tasks_per_day, width, color="C3", hatch="\\", alpha=0.3)

    # Finalize and save the plot
    fig.tight_layout()
    with io.BytesIO() as buf:
        fig.savefig(buf, format="png", dpi=glb.dpi(), pil_kwargs={"compress_level": 1})
        buf.seek(0)
        st.image(buf)
