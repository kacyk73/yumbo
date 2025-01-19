import datetime
import os
import streamlit as st
import romz_ampl
import romz_datetime
import plot_hours_per_day
import plot_invoicing_periods_histogram
import plot_schedule_stacked_histogram
import plot_task
import plot_tasks_gantt
import plot_tasks_per_day
import glb
import sbar


def get_tasks_for_expert(expert_name):
    tasks = glb.data["tasks"]
    links = glb.data["links"]

    # Filter the tasks related to the expert
    tasks_for_expert = links[links["Expert"] == expert_name]["Task"]

    # Use .isin() to filter tasks directly
    return tasks[tasks["Name"].isin(tasks_for_expert)]


def show_tasks_gantt_chart(expert_name):
    tasks = get_tasks_for_expert(expert_name)
    work_done = glb.data[f"schedule {expert_name}"].loc[tasks["Name"]].sum(axis=1)
    plot_tasks_gantt.plot(tasks, work_done)


def show_schedule_as_table(expert_name):
    tasks = get_tasks_for_expert(expert_name)
    start_date = romz_datetime.to_string(tasks["Start day"].min())
    end_date = romz_datetime.to_string(tasks["End day"].max())

    # Retrieve the relevant schedule data
    df = glb.data[f"schedule {expert_name}"].loc[tasks["Name"], start_date:end_date]

    # Apply styling to the DataFrame
    styled_df = df.style.format(precision=2) \
                        .highlight_between(left=0.24, right=None, props='color:white; background-color:purple') \
                        .highlight_between(left=None, right=0.24, props='color:white; background-color:white;')

    st.dataframe(styled_df)


def show_commitment_per_task(expert_name):
    tasks_for_expert = get_tasks_for_expert(expert_name)
    col1, col2, col3 = st.columns(3)
    j = 0
    for idx in tasks_for_expert.index:
        j += 1
        task = tasks_for_expert.loc[idx]
        schedule = glb.data[f"schedule {expert_name}"]
        xbday = glb.data["xbday"]
        bounds = xbday.loc[ xbday["Task"] == task["Name"]].loc[ xbday["Expert"] == expert_name]
        with col1:
            if(j % 3 == 1):
                plot_task.plot(task, schedule, bounds)

        with col2:
            if(j % 3 == 2):
                plot_task.plot(task, schedule, bounds)

        with col3:
            if(j % 3 == 0):
                plot_task.plot(task, schedule, bounds)


def show_summary():
    if glb.data["show_experts_overview"]:
        st.subheader(":blue[Experts overview]", divider="blue")
        col1, col2, col3 = st.columns(3)
        with col1:
            plot_tasks_gantt.plot_summary()
        with col2:
            plot_tasks_per_day.plot_summary()
        with col3:
            plot_hours_per_day.plot_summary()


def show_solver_output():
    st.subheader(f":green[Solver output at {glb.data['solver timestamp']}]", divider="blue")
    st.code(glb.data["solver output"])


def show_one_row(expert_name):
    report_column_no = glb.data["report_column_no"]
    col_list = st.columns(report_column_no)
    for ii, col in enumerate(col_list):
        with col:
            chart_name  = glb.data[f"report_column_{ii+1}"]
            if chart_name == "Task's Gantt chart":
                show_tasks_gantt_chart(expert_name)
            elif chart_name == "Tasks per day":
                plot_tasks_per_day.plot(glb.data[f"schedule {expert_name}"])
            elif chart_name == "Hours per day":
                plot_hours_per_day.plot(glb.data[f"schedule {expert_name}"])
            elif chart_name == "Hours per day stacked":
                plot_schedule_stacked_histogram.plot(expert_name)
            elif chart_name == "Invoice period workload":
                plot_invoicing_periods_histogram.plot(expert_name)
            else:
                st.write(chart_name)


def show_main_panel():
    show_summary()

    experts = glb.data["experts"].sort_values(by='Name')
    for e in experts.index:
        expert_name = experts.loc[e, "Name"]
        st.subheader(":blue[{name}] {comment}".format(name=expert_name, comment=experts.loc[e, "Comment"]), divider="blue")
        if glb.data["report"].loc[expert_name, "Show?"]:
            show_one_row(expert_name)

            if glb.data["report"].loc[expert_name, "Table?"]:
                show_schedule_as_table(expert_name)

            if glb.data["report"].loc[expert_name, "Commitment?"]:
                show_commitment_per_task(expert_name)
    show_solver_output()


def set_page_config():
    st.set_page_config(page_title="Yumbo",layout="wide")
    # css = '''
    # <style>
    #     [data-testid="stSidebar"]{
    #         min-width: 400px;
    #         max-width: 800px;
    #     }
    # </style>
    # '''
    # st.html(css)


def show_page_header():
    st.title(":red[Yumbo.] Scheduling, Planning and Resource Allocation")
    st.subheader("Zbigniew Romanowski, Paweł Koczyk")
    st.caption("Source code, documentation and sample Excel input files can be found on [Yumbo's](https://github.com/romz-pl/yambo) GitHub repository.")
    st.caption("_{d}_".format(d=datetime.datetime.now().strftime("%d %B %Y, %H:%M:%S %p")))


def shwo_yumbo_description():
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        dd = os.path.dirname(__file__)
        with open(f"{dd}/../doc/yumbo.md", "r") as f:
            st.markdown(f'''{f.read()}''')

    st.divider()
    st.image(f"{dd}/../doc/yumbo.webp")
    st.caption("Image generated by ChatGPT")


def main():
    # plt.style.use('seaborn-v0_8-whitegrid')
    set_page_config()
    show_page_header()

    with st.sidebar:
        uploaded_file = sbar.load_excel_file()
        if uploaded_file != None:
            new_input = sbar.show(uploaded_file)

    if uploaded_file == None:
        shwo_yumbo_description()
        return

    if new_input:
        try:
            romz_ampl.solve(uploaded_file.name)
        except Exception as e:
            st.subheader(f":red[Exception during solving process.] {e}")
            return

    show_main_panel()


######################## CALL MAIN FUNCTION ##################

if __name__ == "__main__":
    main()


