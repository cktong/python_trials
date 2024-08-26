from pulp import LpMaximize, LpMinimize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD, LpInteger, LpBinary
import scipy.stats as stats

# Define the model
model = LpProblem(name="solar-system-optimization", sense=LpMinimize)

# Types of components
types = range(3)  # Example with 3 types

# Define the decision variables
x_p = {t: LpVariable(f"solar_panels_{t}", lowBound=0,
                     cat=LpInteger) for t in types}
x_b = {t: LpVariable(f"batteries_{t}", lowBound=0, cat=LpInteger)
       for t in types}
x_i = {t: LpVariable(f"inverters_{t}", lowBound=0, cat=LpInteger)
       for t in types}
y_p = {t: LpVariable(f"select_panel_{t}", cat=LpBinary) for t in types}
y_b = {t: LpVariable(f"select_battery_{t}", cat=LpBinary) for t in types}
y_i = {t: LpVariable(f"select_inverter_{t}", cat=LpBinary) for t in types}

# Given loan rate and term
loan_rate = 0.02  # Example loan rate
loan_term = 10  # Fixed loan term in years
project_duration = 40  # Total project duration in years

# Costs for each type (example data)
C_p = [1000, 1500, 2000]  # Cost per panel
C_b = [500, 750, 1000]    # Cost per battery
C_i = [300, 450, 600]     # Cost per inverter
C_e = 0.10                # Cost of electricity from the grid in USD/kWh

# Depreciation coefficients (example data)
depreciation_p = [10, 15, 20]  # Lifespan of panels in years
depreciation_b = [5, 7, 10]    # Lifespan of batteries in years
depreciation_i = [10, 10, 10]  # Lifespan of inverters in years

# Capacities for each type (example data)
panel_capacity = [5, 6, 7]  # kW per panel type per day
battery_capacity = [10, 12, 14]  # kW storage per battery type
inverter_capacity = [20, 25, 30]  # kW per inverter type

# Mean output and standard deviation percentages
mean_output_percentage = 0.80  # 60% average output
std_dev_percentage = 0.10      # 10% standard deviation

# Calculate the mean output and standard deviation in kWh for each panel type
mean_output = [mean_output_percentage * panel_capacity[t] for t in types]
std_dev_output = [std_dev_percentage * panel_capacity[t] for t in types]

# Calculate the number of replacement cycles within the project duration
replacement_cycles_p = {t: project_duration //
                        depreciation_p[t] for t in types}
replacement_cycles_b = {t: project_duration //
                        depreciation_b[t] for t in types}
replacement_cycles_i = {t: project_duration //
                        depreciation_i[t] for t in types}

# Calculate replacement costs
replacement_cost_p = lpSum(
    C_p[t] * x_p[t] * (replacement_cycles_p[t] + 1) for t in types)
replacement_cost_b = lpSum(
    C_b[t] * x_b[t] * (replacement_cycles_b[t] + 1) for t in types)
replacement_cost_i = lpSum(
    C_i[t] * x_i[t] * (replacement_cycles_i[t] + 1) for t in types)

# Capital cost including replacements
capital_cost = replacement_cost_p + replacement_cost_b + replacement_cost_i

# Interest cost calculation based on fixed loan term
interest_cost = loan_rate * capital_cost * loan_term

# Objective function
model += (capital_cost + interest_cost)

# Add constraints
E_required_daily = 100  # Daily energy requirement in kWh
total_budget = 200000  # Relaxed total budget in USD

# Desired confidence level (e.g., 90%)
confidence_level = 0.70
z_score = stats.norm.ppf(confidence_level)

# Calculate required storage to meet energy requirements with the desired confidence level
required_storage = lpSum(
    x_p[t] * (E_required_daily - (mean_output[t] - z_score * std_dev_output[t])) for t in types)

# Ensure energy requirements are met with backup storage
model += (lpSum(x_p[t] * panel_capacity[t] for t in types)
          >= E_required_daily, "panel_capacity_constraint")
model += (lpSum(x_b[t] * battery_capacity[t] for t in types)
          >= required_storage, "battery_capacity_constraint")
model += (lpSum(x_i[t] * inverter_capacity[t] for t in types)
          >= E_required_daily, "inverter_capacity_constraint")

# Connection between solar panels and batteries (storage capacity should be greater than or equal to generated energy)
model += (lpSum(x_p[t] * panel_capacity[t] for t in types) <= lpSum(x_b[t]
          * battery_capacity[t] for t in types), "battery_storage_constraint")

# Budget constraint
model += (capital_cost + interest_cost <= total_budget, "budget_constraint")

# Selection constraints: ensure exactly one type of each component is selected
model += (lpSum(y_p[t] for t in types) == 1, "panel_selection_constraint")
model += (lpSum(y_b[t] for t in types) == 1, "battery_selection_constraint")
model += (lpSum(y_i[t] for t in types) == 1, "inverter_selection_constraint")

# Ensure number of components selected corresponds to the selected type
M = 1000  # A sufficiently large number
for t in types:
    model += (x_p[t] <= M * y_p[t], f"panel_type_{t}_constraint")
    model += (x_b[t] <= M * y_b[t], f"battery_type_{t}_constraint")
    model += (x_i[t] <= M * y_i[t], f"inverter_type_{t}_constraint")

# Solve the model using CBC solver
solver = PULP_CBC_CMD(msg=1)
status = model.solve(solver)

# Debugging: Print solver status
print(f"Solver status: {status}")

if status == -1:
    print("Problem is infeasible. Reviewing constraints...")

# Get results if feasible
if status == 1:
    solar_panels = {t: x_p[t].value() for t in types}
    batteries = {t: x_b[t].value() for t in types}
    inverters = {t: x_i[t].value() for t in types}
    selected_panels = {t: y_p[t].value() for t in types}
    selected_batteries = {t: y_b[t].value() for t in types}
    selected_inverters = {t: y_i[t].value() for t in types}

    # Debugging: Print variable values
    print(f"Solar panels: {solar_panels}")
    print(f"Batteries: {batteries}")
    print(f"Inverters: {inverters}")
    print(f"Selected panels (binary): {selected_panels}")
    print(f"Selected batteries (binary): {selected_batteries}")
    print(f"Selected inverters (binary): {selected_inverters}")

    # Calculate total daily energy generated
    total_energy_generated_daily = sum(
        panel_capacity[t] * solar_panels[t] for t in types)

    # Calculate total cost
    capital_cost_value = sum(C_p[t] * solar_panels[t] * (replacement_cycles_p[t] + 1) +
                             C_b[t] * batteries[t] * (replacement_cycles_b[t] + 1) +
                             C_i[t] * inverters[t] * (replacement_cycles_i[t] + 1) for t in types)
    interest_cost_value = loan_rate * capital_cost_value * loan_term
    total_cost = capital_cost_value + interest_cost_value

    # Calculate total annual savings from solar energy
    total_annual_energy_generated = total_energy_generated_daily * 365
    total_annual_savings = total_annual_energy_generated * C_e

    # Cost per kilowatt-hour
    cost_per_kwh = total_cost / \
        total_annual_energy_generated if total_annual_energy_generated != 0 else float(
            'inf')

    # Breakeven point calculation
    breakeven_years = total_cost / \
        total_annual_savings if total_annual_savings != 0 else float('inf')

    # Print results
    print("Optimal number of solar panels by type:", solar_panels)
    print("Optimal number of batteries by type: ", batteries)
    print("Optimal number of inverters by type: ", inverters)
    print("Selected solar panel types: ", selected_panels)
    print("Selected battery types: ", selected_batteries)
    print("Selected inverter types: ", selected_inverters)
    print("Total daily energy generated(kWh): ", total_energy_generated_daily)
    print("Capital cost(USD): ", capital_cost_value)
    print("Interest cost(USD): ", interest_cost_value)
    print("Total cost(USD): ", total_cost)
    print("Total annual energy generated(kWh): ", total_annual_energy_generated)
    print("Total annual savings(USD): ", total_annual_savings)
    print("Cost per kilowatt-hour(USD/kWh): ", cost_per_kwh)
    print("Breakeven point (years): ", breakeven_years)