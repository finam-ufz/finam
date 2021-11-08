from pyformind_finam import Model

par_file = "formind_parameters/beech_forest.par"

rw = 1.0
model = Model()
model.read_par_file(par_file)

model.start()

for i in range(30):
    model.set_reduction_factor(rw)
    model.step()

print(f"{rw};{model.get_lai()};{model.get_biomass()};{model.get_photo_production()}")
