import datetime
import numpy as np
import pandas as pd
import os
import romz_datetime
from amplpy import AMPL, modules
import glb

quarters_in_hour = 4

def tasks():
    today = glb.today()
    df = glb.data["tasks"]

    # Calculate start and end days relative to today
    df["Start Relative"] = (df["Start"] - today).dt.days
    df["End Relative"] = (df["End"] - today).dt.days

    # Use vectorized string formatting for better performance
    formatted_rows = df.apply(
        lambda row: f"'{row['Name']}' {row['Start Relative']} {row['End Relative']} "
        f"{row['Work'] * quarters_in_hour}\n",
        axis=1,
    )

    df.drop(columns=["Start Relative", "End Relative"], inplace=True)

    return ''.join(formatted_rows)


def offday():
    today = glb.today()
    # Determine the date range
    min_date = glb.data["tasks"]["Start"].min()
    max_date = glb.data["tasks"]["End"].max()

    # Generate weekends within the range using a mask for Saturdays and Sundays
    weekends = pd.bdate_range(start=min_date, end=max_date, freq='C', weekmask='Sat Sun')
    holidays = glb.data["public holidays"]["Date"]

    # Combine weekends and holidays into a sorted list
    # The set off_days is the union of weekends and holidays.
    # Sorting is not necessary. However, it does give deterministic (repetitive) results.
    off_days = sorted(set(weekends.union(holidays)))

    # Create the result buffer
    buf = "\n".join(f"{idx + 1} {(day - today).days}" for idx, day in enumerate(off_days))

    return len(off_days), buf


def xbday():
    today = glb.today()
    # Preprocessing for efficient lookups
    df = glb.data["xbday"]
    df_tasks = glb.data["tasks"].set_index("Name")  # Set "Name" as index for quick task lookup
    holidays = set(glb.data["public holidays"]["Date"])  # Convert holidays to a set for faster checks

    result = []
    id_counter = 0

    # Iterate efficiently using itertuples
    for row in df.itertuples(index=False):
        task_name = row.Task
        expert_name = row.Expert
        lower = row.Lower * quarters_in_hour
        upper = row.Upper * quarters_in_hour

        # Calculate valid date range considering task bounds and xbday range
        task_start, task_end = df_tasks.loc[task_name, ["Start", "End"]]
        range_start = max(row.Start, task_start)
        range_end = min(row.End, task_end)
        # Generate business days using pandas
        valid_days = pd.bdate_range(
            start=range_start,
            end=range_end,
            freq="C",
            holidays=holidays,
            weekmask="Mon Tue Wed Thu Fri"
        )

        # Process valid days
        for d in valid_days:
            day_offset = (d - today).days
            id_counter += 1
            result.append(f"{id_counter} '{expert_name}' '{task_name}' {day_offset} {lower} {upper}")

    # Combine results into a single string and return
    return id_counter, "\n".join(result)




def xbsum():
    today = glb.today()
    df = glb.data["xbsum"]
    result = []

    # Iterate over rows using itertuples for better performance
    for idx, row in enumerate(df.itertuples(index=False), start=1):
        expert = row.Expert
        task = row.Task
        start = (row.Start - today).days
        end = (row.End - today).days
        lower = row.Lower * quarters_in_hour
        upper = row.Upper * quarters_in_hour

        # Append formatted string to result list
        result.append(f"{idx} '{expert}' '{task}' {start} {end} {lower} {upper}")

    # Join the result list with newline characters
    return len(result), "\n".join(result)


def ubday():
    today = glb.today()
    df = glb.data["ubday"]
    holidays = set(glb.data["public holidays"]["Date"])

    result = []
    id = 0

    for row in df.itertuples(index=False):
        # Generate business days excluding holidays
        valid_days = pd.bdate_range(start=row.Start, end=row.End, freq='C', holidays=holidays)

        # Format the output
        for day in valid_days:
            id += 1
            relative_day = (day - today).days
            result.append(f"{id} '{row.Expert}' {relative_day} {row.Lower} {row.Upper}")

    return id, "\n".join(result)


def ubsum():
    today = glb.today()
    df = glb.data["ubsum"]
    result = [
        f"{id+1} '{row.Expert}' '{row.Task}' {(row.Start - today).days} "
        f"{(row.End - today).days} "
        f"{row.Lower} {row.Upper}"
        for id, row in enumerate(df.itertuples(index=False))
    ]
    return len(result), "\n".join(result)


def experts():
    return "\n".join(f"'{name}'" for name in glb.data["experts"]["Name"])


def expert_bounds():
    today = glb.today()
    df = glb.data["expert bounds"]
    result = [
        f"{id+1} '{row.Expert}' {(row.Start - today).days} "
        f"{(row.End - today).days} "
        f"{row.Lower * quarters_in_hour} "
        f"{row.Upper * quarters_in_hour}"
        for id, row in enumerate(df.itertuples(index=False))
    ]
    return len(result), "\n".join(result)


def links():
    df = glb.data["links"]
    return "\n".join(f"'{expert}' '{task}'" for expert, task in zip(df["Expert"], df["Task"]))


def invoicing_periods():
    today = glb.today()
    df = glb.data["invoicing periods"]
    result = [
        f"'{row.Name}' {(row.Start - today).days} {(row.End - today).days}"
        for row in df.itertuples(index=False)
    ]
    return "\n".join(result)


def invoicing_periods_bounds():
    today = glb.today()
    df = glb.data["invoicing periods bounds"]
    return "\n".join(
        f"'{expert}' '{period}' "
        f"{lower * quarters_in_hour} "
        f"{upper * quarters_in_hour}"
        for expert, period, lower, upper in zip(df["Expert"], df["Period"], df["Lower"], df["Upper"])
    )


def data_file(name):
    ampl_data_file = "./ampl-translated-from-excel/{}.dat".format(name)
    with open(ampl_data_file, 'w') as f:
        f.write(f'param HOURS_PER_DAY := {glb.hours_per_day() * quarters_in_hour};\n\n')

        buf = experts()
        f.write('set EXPERTN :=\n')
        f.write(buf)
        f.write(';\n\n')

        expert_bound_no, buf = expert_bounds()
        f.write(f'param EBOUND_NO := {expert_bound_no};\n\n')
        f.write('param EBOUND:\n')
        f.write('1   2   3   4   5 :=\n')
        f.write(buf)
        f.write(';\n\n')

        buf = tasks()
        f.write('param:\n')
        f.write('TASKN: TASKS TASKE TASKW :=\n')
        f.write(buf)
        f.write(';\n\n')

        buf = invoicing_periods()
        f.write('param:\n')
        f.write('PAYROLLN: PAYROLLS PAYROLLE :=\n')
        f.write(buf)
        f.write(';\n\n')

        buf = invoicing_periods_bounds()
        f.write('param:\n')
        f.write('EXPPAY: PAYROLLBL PAYROLLBU :=\n')
        f.write(buf)
        f.write(';\n\n')

        offday_no, buf = offday()
        f.write(f'param OFFDAY_NO := {offday_no};\n\n')
        f.write('param OFFDAY :=\n')
        f.write(buf)
        f.write(';\n\n')

        xbday_no, buf = xbday()
        f.write(f'param XBDAY_NO := {xbday_no};\n\n')
        f.write('param XBDAY:\n')
        f.write('1   2   3   4   5 :=\n')
        f.write(buf)
        f.write(';\n\n')

        xbsum_no, buf = xbsum()
        f.write(f'param XBSUM_NO := {xbsum_no};\n\n')
        f.write('param XBSUM:\n')
        f.write('1   2   3   4   5   6 :=\n')
        f.write(buf)
        f.write(';\n\n')

        ubday_no, buf = ubday()
        f.write(f'param UBDAY_NO := {ubday_no};\n\n')
        f.write('param UBDAY:\n')
        f.write('1   2   3   4 :=\n')
        f.write(buf)
        f.write(';\n\n')

        ubsum_no, buf = ubsum()
        f.write(f'param UBSUM_NO := {ubsum_no};\n\n')
        f.write('param UBSUM:\n')
        f.write('1   2   3   4   5   6 :=\n')
        f.write(buf)
        f.write(';\n\n')

        buf = links()
        f.write('set LINKS :=\n')
        f.write(buf)
        f.write(';\n\n')

    return ampl_data_file



def save_schedule(ampl):
    today = glb.today()
    tasks_name = glb.data["tasks"]["Name"]
    experts_name = glb.data["experts"]["Name"]

    day_no = int(ampl.get_data("DAY_NO").to_pandas().iloc[0, 0])
    days = pd.date_range(start=today + pd.Timedelta(days=1), periods=day_no, freq='D')

    for en in experts_name:
        schedule = {
            tn: ampl.get_data(f"{{d in 1..DAY_NO}} X['{en}', d, '{tn}']").to_pandas().iloc[:, 0]
            for tn in tasks_name
        }
        # Create DataFrame from fetched data
        df = pd.DataFrame(schedule, dtype=np.float16).T
        df.columns = days
        glb.data[f"schedule {en}"] = df / quarters_in_hour


def save_day_no(ampl):
    glb.data["DAY_NO"] = ampl.get_parameter("DAY_NO").to_pandas().astype(int).iat[0,0]


def save(ampl):
    save_schedule(ampl)
    save_day_no(ampl)


# activate AMPL license
def set_ampl_license():
    uuid = os.environ.get("AMPLKEY_UUID")
    if uuid is not None:
        modules.activate(uuid)


def solve(name):
    file = data_file(name)

    set_ampl_license()
    ampl = AMPL()
    solver = glb.data["misc"].iloc[0]["Solver"]
    ampl.set_option("solver", solver)

    # Set solver-specific options
    solver_options = {
        "highs": "outlev=1",
        "gcg": "tech:outlev-native=4",
        "scip": "tech:outlev-native=5",
    }

    if solver in solver_options:
        ampl.option[f"{solver}_options"] = solver_options[solver]

    # Change directory to AMPL's working directory
    ampl.cd(os.path.dirname(os.path.dirname(__file__)))

    ampl.read("./res/ampl_mathematical_model.mod.py")
    ampl.read_data(file)

    # Capture solver output and timestamp
    glb.data["solver output"] = ampl.get_output("solve;")
    glb.data["solver timestamp"] = datetime.datetime.now().strftime("%d %B %Y, %H:%M:%S %p")

    # Check if solving was successful
    if ampl.solve_result != "solved":
        raise Exception(f"Failed to solve AMPL problem. AMPL returned flag: {ampl.solve_result}")

    save(ampl)

