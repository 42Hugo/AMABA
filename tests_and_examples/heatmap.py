import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Provided data
data = {
    'Speed': [100, 100, 100, 100, 100, 90, 100, 80, 100, 100, 70, 100, 100, 60, 100, 100, 50, 100, 100, 40, 30, 20],
    'Power': [37.5, 38, 37.5, 40, 37.5, 37.5, 45, 37.5, 37.5, 50, 37.5, 60, 37.5, 37.5, 70, 37.5, 37.5, 80, 90, 37.5, 37.5, 37.5],
    'PPI_written': [1000, 1000, 1000, 1000, 900, 1000, 1000, 1000, 750, 1000, 1000, 1000, 600, 1000, 1000, 500, 1000, 1000, 1000, 1000, 1000, 1000],
    'Hysteresis': [31, 31, 31, 35, 46, 39, 39, 42, 40, 54, 20, 56, 48, 37, 54, 50, 57, 77, 79, 52, 92, 81]
}

# Calculate P/V
data['P/V'] = [p/s for p, s in zip(data['Power'], data['Speed'])]

df = pd.DataFrame(data)

# Create grid data
PPI_values = np.unique(df['PPI_written'])
PV_values = np.unique(df['P/V'])

# Create grid for contour plot
PPI_grid, PV_grid = np.meshgrid(PPI_values, PV_values)
Hysteresis_grid = np.empty(PPI_grid.shape)

# Fill grid with Hysteresis values
for i in range(PPI_grid.shape[0]):
    for j in range(PPI_grid.shape[1]):
        PPI_val = PPI_grid[i, j]
        PV_val = PV_grid[i, j]
        value = df[(df['PPI_written'] == PPI_val) & (df['P/V'] == PV_val)]['Hysteresis']
        Hysteresis_grid[i, j] = value if not value.empty else np.nan

# Plotting the contour plot
plt.figure(figsize=(10, 8))
contour = plt.contourf(PV_grid, PPI_grid, Hysteresis_grid.T, cmap="YlGnBu", levels=20)
plt.colorbar(contour)
plt.title('Hysteresis Contour Plot')
plt.xlabel('P/V')
plt.ylabel('PPI Written')
plt.show()
