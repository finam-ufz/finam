import formind

model = formind.Model(100)

model.initialize()

for i in range(10):
    model.update()

model.finalize()
