import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

# ----------------------------------------------------------
# 1. Title with team name
# ----------------------------------------------------------
st.title("🏇 Horse Race Winner Predictor — Team Vanguard")

# ----------------------------------------------------------
# 2. One-line decision support caption
# ----------------------------------------------------------
st.caption(
    "This dashboard helps analysts identify the most likely winning horses "
    "and compare predicted win probabilities across upcoming race fields."
)

# ----------------------------------------------------------
# Load data
# ----------------------------------------------------------
@st.cache_data
def load_data():
    horse = pd.read_csv("race-result-horse.csv")
    race = pd.read_csv("race-result-race.csv")
    df = pd.merge(horse, race, on="race_id", how="left")
    return df

df = load_data()

# ----------------------------------------------------------
# Simple data preparation
# ----------------------------------------------------------
# Target: 1 if the horse finished 1st, else 0
df["is_win"] = np.where(df["finishing_position"] == "1", 1, 0)

# Clean numeric fields
df["win_odds"] = pd.to_numeric(df["win_odds"], errors="coerce")
df["draw"] = pd.to_numeric(df["draw"], errors="coerce")
df["actual_weight"] = pd.to_numeric(df["actual_weight"], errors="coerce")
df["race_date"] = pd.to_datetime(df["race_date"], errors="coerce")

# Derived feature: implied win probability from odds
df["market_prob"] = 1 / df["win_odds"].replace(0, np.nan)

# Select features
feature_cols = ["draw", "actual_weight", "market_prob"]
model_df = df.dropna(subset=feature_cols + ["is_win"]).copy()

# ----------------------------------------------------------
# 3. Headline metrics using st.metric
# ----------------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Total Rows", len(df))
col2.metric("Training Samples", len(model_df))
col3.metric("Win Rate", f"{model_df['is_win'].mean():.1%}")

# ----------------------------------------------------------
# 4. At least one useful filter
# ----------------------------------------------------------
st.subheader("Filter the Race Field")

# Filter by race_id
race_options = ["All"] + sorted(model_df["race_id"].dropna().unique().astype(str).tolist())
selected_race = st.selectbox("Select a Race ID", race_options)

if selected_race != "All":
    model_df = model_df[model_df["race_id"] == int(selected_race)]

# Filter by win odds range
min_odds, max_odds = st.slider(
    "Filter by Win Odds",
    float(model_df["win_odds"].min()),
    float(model_df["win_odds"].max()),
    (float(model_df["win_odds"].min()), float(model_df["win_odds"].max()))
)
model_df = model_df[
    (model_df["win_odds"] >= min_odds) &
    (model_df["win_odds"] <= max_odds)
]

# ----------------------------------------------------------
# Train simple model
# ----------------------------------------------------------
if len(model_df) > 50:
    X = model_df[feature_cols]
    y = model_df["is_win"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    model_df["pred_win_prob"] = model.predict_proba(X[feature_cols])[:, 1]

    # Model performance on test set
    y_test_pred = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_test_pred)

    st.metric("Model AUC", f"{auc:.3f}")
else:
    st.warning("Please select a race or expand the odds range to train the model.")
    model_df["pred_win_prob"] = np.nan

# ----------------------------------------------------------
# 5. At least one supporting chart
# ----------------------------------------------------------
st.subheader("Predicted Win Probability by Horse")

chart_df = model_df.dropna(subset=["pred_win_prob"]).copy()

if not chart_df.empty:
    fig = px.bar(
        chart_df,
        x="pred_win_prob",
        y="horse_name",
        orientation="h",
        color="pred_win_prob",
        title="Horses Ranked by Predicted Win Probability",
        labels={"pred_win_prob": "Predicted Win Probability", "horse_name": "Horse"},
        template="plotly_white"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No predictions to display yet.")

# ----------------------------------------------------------
# Prediction table
# ----------------------------------------------------------
st.subheader("Horse Ranking Table")

display_cols = [
    "horse_name",
    "race_id",
    "draw",
    "actual_weight",
    "win_odds",
    "market_prob",
    "pred_win_prob"
]

existing_cols = [c for c in display_cols if c in model_df.columns]
result_table = model_df[existing_cols].copy()

if not result_table.empty:
    result_table = result_table.sort_values("pred_win_prob", ascending=False)
    st.dataframe(result_table, use_container_width=True)

# ----------------------------------------------------------
# Top 3 recommendation
# ----------------------------------------------------------
if not result_table.empty:
    st.subheader("Top 3 Horses to Watch")
    top3 = result_table.head(3)
    for i, row in top3.iterrows():
        st.metric(
            label=f"{i+1}. {row['horse_name']}",
            value=f"Win Probability: {row['pred_win_prob']:.1%}",
            delta=f"Odds: {row['win_odds']:.1f}"
        )

# ----------------------------------------------------------
# 6. Data period and refresh decision
# ----------------------------------------------------------
st.subheader("Data & Refresh Information")

min_date = df["race_date"].min()
max_date = df["race_date"].max()

st.write(f"Data period: from {min_date.date()} to {max_date.date()}.")
st.write("Refresh decision: The dashboard should be refreshed weekly after new race results are added.")
