import pandas as pd

df = pd.read_csv("input_alpha_timeseries.csv")


df["timestamp"] = pd.to_datetime(df["timestamp"])


df = df.sort_values(
    by=["segment_id", "junction_side", "timestamp"]
)

df["alpha_t"] = df["alpha"]

df["alpha_t_plus_30"] = (
    df
    .groupby(["segment_id", "junction_side"])["alpha"]
    .shift(-1)
)

training_df = df.dropna(
    subset=["alpha_t", "alpha_t_plus_30"]
)

training_df = training_df[
    ["segment_id", "junction_side", "alpha_t", "alpha_t_plus_30"]
]

training_df.to_csv("alpha_regression_training.csv", index=False)