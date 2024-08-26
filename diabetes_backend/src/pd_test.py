import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time

timestamps = [
    f"2020-01-01 {hr}:{min}:31" for min in range(10, 60) for hr in range(10, 11)
]


np.random.seed(seed=1111)
data = np.random.randint(1, high=100, size=len(timestamps))

df = pd.DataFrame({"test": timestamps, "res": data})
df["test"] = pd.to_datetime(df["test"]).apply(
    lambda t: t.replace(day=31, year=2000, month=12)
)
# df.apply(lambda dt: dt.replace(day=1))
# df = df.set_index("test")

# df.resample("20T")
custom_df = df.groupby(pd.Grouper(key="test", freq="15T")).count()
custom_df["Mean"] = df.groupby(pd.Grouper(key="test", freq="15T")).mean()
custom_df["raw"] = df.groupby(pd.Grouper(key="test", freq="15T"))["res"].apply(list)
print(custom_df)
custom_df.index = custom_df.index.strftime("%B %d, %Y, %r")
print(custom_df)

df["raw"] = df.groupby(pd.Grouper(key="test", freq="15T"))["res"].apply(list)
agg_df = df.groupby([pd.Grouper(key="test", freq="15T")])["res"].agg(
    ["mean", "median", "var", "count", "std"]
)
# agg_df.merge(custom_df, left_on='test', right_on='test')
# df["raw"] = df.groupby(pd.Grouper(key='test', freq='15T'))["res"].apply(list)
print("df")
print(agg_df)
