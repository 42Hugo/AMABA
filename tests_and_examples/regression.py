import pandas as pd
import numpy as np
import statsmodels.api as sm


# Provided data
data = {
    "Speed": [
        100, 100, 90, 100, 100, 80, 100, 100, 70, 100, 60, 100, 50, 100, 100, 40, 100, 
        30, 100, 100, 20, 70, 100, 70, 20
    ],
    "Power": [
        37.5, 37.5, 37.5, 40, 37.5, 37.5, 45, 37.5, 37.5, 50, 37.5, 37.5, 37.5, 60, 
        37.5, 37.5, 70, 37.5, 80, 90, 37.5, 50, 70, 70, 37.5
    ],
    "PPI": [
        1000, 1000, 1000, 1000, 900, 1000, 1000, 750, 1000, 1000, 1000, 600, 1000, 1000, 
        500, 1000, 1000, 1000, 1000, 1000, 1000, 500, 500, 500, 500
    ],
    "Hysteresis": [
        31.0, 31.0, 38.9, 34.5, 46.1, 42.1, 39.0, 39.6, 20.1, 54.1, 36.5, 48.5, 57.1, 
        56.2, 49.6, 52.4, 54.0, 92.3, 77.0, 79.9, 81.4, 71.7, 48.1, 52.3, 68.8
    ]
}
df = pd.DataFrame(data)



# Assume df is your DataFrame containing the columns 'Speed', 'Power', 'PPI', and 'Hysteresis'
df['log_Hysteresis'] = np.log(df['Hysteresis'])
df['log_Power'] = np.log(df['Power'])
df['log_Speed'] = np.log(df['Speed'])
df['log_PPI'] = np.log(df['PPI'])

# Define the independent variables (adding a constant for the intercept)
X = df[['log_Power', 'log_Speed', 'log_PPI']]
X = sm.add_constant(X)

# Define the dependent variable
y = df['log_Hysteresis']

# Fit the regression model
model = sm.OLS(y, X).fit()

# Print the summary of the regression model
print(model.summary())
