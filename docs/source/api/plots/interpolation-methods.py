"""Plot illustrating linear and step-wise interpolation"""

import matplotlib.pyplot as plt
import numpy as np

x = np.asarray(range(6))
y = np.asarray([0, 1, 1.5, 1.2, 0.5, 1.0])

fig, ax = plt.subplots(figsize=(6, 2.5))
ax.plot(x, y, marker="o", color="black", ls="", zorder=10, label="Data")
ax.plot(x, y, color="blue", label="Linear", zorder=1)
ax.step(x, y + 0.02, where="pre", color="green", label="Step=0.0", zorder=2)
ax.step(x, y, where="mid", color="orange", label="Step=0.5", zorder=3)
ax.step(x, y - 0.02, where="post", color="red", label="Step=1.0", zorder=4)

ax.set_title("Linear and step-wise interpolation")

ax.set_xlabel("time")
ax.set_xticklabels([])

legend = ax.legend(loc=1, framealpha=1.0)
legend.set_zorder(100)

plt.show()
