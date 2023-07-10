import pandas as pd
import numpy as np

# Create a sample time series DataFrame with an hourly frequency
date_rng = pd.date_range(start='2021-01-01', end='2021-01-10', freq='H')
data = {'value': np.random.randint(0, 100, size=len(date_rng))}
df = pd.DataFrame(data, index=date_rng)

# Display the original DataFrame
print("Original DataFrame:")
print(df.head())

# Resample the DataFrame from hourly to daily frequency, aggregating using the mean
daily_df = df.resample('D').mean()

# Display the resampled DataFrame
print("\nResampled DataFrame:")
print(daily_df)