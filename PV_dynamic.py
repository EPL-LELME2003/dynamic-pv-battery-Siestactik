from pyomo.environ import ConcreteModel, Var, Objective, Constraint, NonNegativeReals, minimize, SolverFactory
import matplotlib.pyplot as plt

# Data / Parameters
load = [99, 93, 88, 87, 87, 88, 109, 127, 140, 142, 142, 140, 140, 140, 137, 139, 146, 148, 148, 142, 134, 123, 108, 93] # kWh par heure
lf_pv = [0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 9.80E-04, 2.47E-02, 9.51E-02, 1.50E-01, 2.29E-01, 2.98E-01, 3.52E-01, 4.15E-01, 4.58E-01, 3.73E-01, 2.60E-01, 2.19E-01, 1.99E-01, 8.80E-02, 7.03E-02, 3.90E-02, 9.92E-03, 1.39E-06, 0.00E+00, 0.00E+00] # %
timestep = len(load)
c_pv = 2500 # €/kWp
c_batt = 1000 # €/kWh
eff_batt_in = 0.95
eff_batt_out = 0.95
chargetime = 4  # hours to charge fully the battery

# Model
model = ConcreteModel()

# Define model variables
model.P_pv = Var(domain=NonNegativeReals)
model.E_pv = Var(range(timestep), domain=NonNegativeReals)
model.SOC_max = Var(domain=NonNegativeReals)
model.SOC = Var(range(timestep), domain=NonNegativeReals)
model.P_batt_in = Var(range(timestep), domain=NonNegativeReals)
model.P_batt_out = Var(range(timestep), domain=NonNegativeReals)

# Define the constraints
model.energy_balance = Constraint(range(timestep), rule=lambda model, t: model.E_pv[t] + model.P_batt_out[t] - model.P_batt_in[t] == load[t])
model.pv_prod = Constraint(range(timestep), rule=lambda model, t: model.E_pv[t] <= model.P_pv*lf_pv[t])
model.batt_prod = Constraint(range(timestep), rule=lambda model, t: model.SOC[t] <= model.SOC_max)
model.batt_charge = Constraint(range(timestep-1), rule=lambda model, t: model.SOC[t+1] == model.SOC[t] + model.P_batt_in[t]*eff_batt_in - model.P_batt_out[t]/eff_batt_out)
model.batt_in = Constraint(range(timestep), rule=lambda model, t: model.P_batt_in[t] <= model.SOC_max/chargetime)
model.batt_out = Constraint(range(timestep), rule=lambda model, t: model.P_batt_out[t] <= model.SOC_max/chargetime)

model.initial_conditions = Constraint(expr=model.SOC[0] == model.SOC_max)

# Define the objective functions
model.f = Objective(expr=model.P_pv*c_pv + model.SOC_max*c_batt, sense=minimize) 

# Specify the path towards your solver (gurobi) file
solver = SolverFactory('gurobi')
solver.solve(model)

# Results - Print the optimal PV size and optimal battery capacity
print(f'PV size = {model.P_pv.value:.2f} kW')
print(f'Battery size = {model.SOC_max.value:.2f} kWh')
print(f'Cost of the system = {model.f()*1e-6:.2f} M€')

# Plotting - Generate a graph showing the evolution of (i) the load, 
# (ii) the PV production and, (iii) the soc of the battery
time = [i for i in range(timestep)]

plt.plot(time, load, label='Load')
plt.plot(time, [model.E_pv[t].value for t in range(timestep)], label='PV Prod')
plt.plot(time, [model.SOC[t].value for t in range(timestep)], label='Battery SOC')
plt.legend()
plt.grid()
plt.show()
