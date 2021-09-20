from pyformind_finam import Model

par_file = "formind_parameters/beech_forest.par"

sw = 30
model = Model()
model.read_par_file(par_file)

model.start()

for i in range(30):
    model.set_soil_water(float(sw))
    model.step()

print(f"{sw};{model.get_lai()};{model.get_biomass()};{model.get_photo_production()}")
