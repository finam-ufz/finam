"""Plot illustrating time integration"""

import matplotlib.pyplot as plt
import numpy as np

x = np.asarray(range(6))
y = np.asarray([0, 1, 1.5, 1.2, 0.5, 1.0])

pulls = np.asarray([0.5, 3.5])
x_interp = np.asarray([0.5, 0.5, 1, 2, 3, 3.5, 3.5])
y_interp = np.asarray([0.0, 0.5, 1, 1.5, 1.2, 0.85, 0.0])

fig, ax = plt.subplots(figsize=(6, 2.5))
ax.plot(x, y, marker="o", color="black", ls="", zorder=10, label="Data")
ax.plot(x, y, color="blue", label="Linear", zorder=3)

ax.axhline(0, color="grey", zorder=2)
ax.axvline(pulls[0], color="black", label="Pull steps", zorder=2)
ax.axvline(pulls[1], color="black", zorder=2)

ax.fill(x_interp, y_interp, color="orange", alpha=0.5, label="AuC", zorder=1)

ax.set_title("Time integration")

ax.set_xlabel("time")
ax.set_xticklabels([])

legend = ax.legend(loc=1, framealpha=1.0)
legend.set_zorder(100)

plt.tight_layout()
plt.show()
