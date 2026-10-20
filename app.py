import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import joblib
from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score

st.set_page_config(page_title="Horse Racing Predictor", layout="wide")
MODEL_FILE = "racing_model.joblib"

# ---------------------- Data load & clean ----------------------
def parse_time_str(time_str):
    """Convert '1.22.33' string to total seconds"""
    if pd.isna(time_str) or time_str == "-":
        return np.nan
    try:
        parts = str(time_str).split(".")
        minute = int(parts[0])
        sec = int(parts[1])
        ms = int(parts[2])
        return minute * 60 + sec + ms / 100
    except:
        return np.nan

@st.cache_data
def load_data():
    df_horse = pd.read_csv("race-result-horse.csv")
    df_race = pd.read_csv("race-result-race.csv")
    df = pd.merge(df_horse, df_race, on="race_id", how="left")

    # clean columns
    df["finish_seconds"] = df["finish_time"].apply(parse_time_str)
    df["win_flag"] = (df["finishing_position"] == "1").astype(int)
    retire_list = ["WV", "WV‑A", "PU", "WX"]
    df["is_retired"] = df["finishing_position"].isin(retire_list).astype(int)
    df["win_odds"] = pd.to_numeric(df["win_odds"], errors="coerce")
    df["draw"] = pd.to_numeric(df["draw"], errors="coerce")
    df["actual_weight"] = pd.to_numeric(df["actual_weight"], errors="coerce")
    df["race_date"] = pd.to_datetime(df["race_date"], errors="coerce")
    df["market_prob"] = 1.0 / df["win_odds"].replace(0, np.nan)

    # filter finished horses for training
    df_finished = df[df["is_retired"] == 0].copy()
    return df, df_finished

# ---------------------- Simple feature (no complex rolling) ----------------------
def make_simple_features(df):
    """Very simple features, avoid time‑shift complexity"""
    # jockey average win rate
    jockey_win = df.groupby("jockey")["win_flag"].agg(["mean"]).reset_index()
    jockey_win.columns = ["jockey", "jockey_win_rate"]
    df = pd.merge(df, jockey_win, on="jockey", how="left")

    # trainer average win rate
    trainer_win = df.groupby("trainer")["win_flag"].agg(["mean"]).reset_index()
    trainer_win.columns = ["trainer", "trainer_win_rate"]
    df = pd.merge(df, trainer_win, on="trainer", how="left")

    feature_list = [
        "draw",
        "actual_weight",
        "market_prob",
        "jockey_win_rate",
        "trainer_win_rate"
    ]
    return df, feature_list

# ---------------------- Train model ----------------------
def train_model(df, feature_list):
    df_valid = df.dropna(subset=feature_list + ["win_flag"]).copy()
    # time‑based split
    split_day = pd.to_datetime("2014‑04‑01")
    train_set = df_valid[df_valid["race_date"] < split_day]
    test_set = df_valid[df_valid["race_date"] >= split_day]

    X_train = train_set[feature_list]
    y_train = train_set["win_flag"]
    X_test = test_set[feature_list]
    y_test = test_set["win_flag"]

    model = LGBMClassifier(
        n_estimators=200,
        learning_rate=0.05,
        scale_pos_weight=10,
        random_state=42,
        verbose=-1
    )
    model.fit(X_train, y_train)
    y_pred = model.predict_proba(X_test)[:,1]
    auc_score = roc_auc_score(y_test, y_pred)

    joblib.dump({"model": model, "features": feature_list}, MODEL_FILE)
    return model, auc_score, test_set

# ---------------------- Predict single race ----------------------
def predict_race(df_race_data, model, feature_list):
    df_in = df_race_data.dropna(subset=feature_list).copy()
    df_in["pred_win_prob"] = model.predict_proba(df_in[feature_list])[:, 1]
    df_in["ev_value"] = df_in["pred_win_prob"] * df_in["win_odds"] - 1
    df_in = df_in.sort_values("pred_win_prob", ascending=False).reset_index(drop=True)
    return df_in

# ---------------------- Streamlit UI ----------------------
def main():
    st.title("🏇 Horse Racing Simple Predictor")
    st.markdown("**Disclaimer: For study purpose only, NOT betting advice.**")

    df_all, df_finished = load_data()
    df_featured, features = make_simple_features(df_finished)

    menu = st.sidebar.radio("Menu", ["Data Overview", "Train Model", "Predict Race"])

    if menu == "Data Overview":
        st.header("Dataset Overview")
        col1, col2 = st.columns(2)
        col1.metric("Total Rows", len(df_all))
        col2.metric("Finished Horse Rows", len(df_finished))
        st.dataframe(df_featured.head(10), use_container_width=True)

        st.subheader("Odds Distribution")
        fig = px.histogram(df_featured[df_featured["win_odds"] < 100], x="win_odds", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    elif menu == "Train Model":
        st.header("Train LightGBM Model")
        if st.button("Start Training"):
            with st.spinner("Training model ..."):
                model, auc, test_df = train_model(df_featured, features)
            st.success(f"Training finished! Test AUC score: {round(auc,3)}")
            st.write("Used features:")
            st.write(features)

            # feature importance plot
            imp_df = pd.DataFrame({
                "feature": model.feature_name_,
                "importance": model.feature_importances_
            }).sort_values("importance", ascending=False)
            fig_imp = px.bar(imp_df, x="importance", y="feature", orientation="h", template="plotly_dark")
            st.plotly_chart(fig_imp, use_container_width=True)

    elif menu == "Predict Race":
        st.header("Predict Race Result")
        try:
            load_obj = joblib.load(MODEL_FILE)
            model = load_obj["model"]
            feat_cols = load_obj["features"]
        except:
            st.warning("Please go to 'Train Model' page and train first!")
            return

        race_id_list = sorted(df_featured["race_id"].unique())
        selected_race = st.selectbox("Pick a race_id", race_id_list)
        one_race_df = df_featured[df_featured["race_id"] == selected_race].copy()

        result = predict_race(one_race_df, model, feat_cols)
        show_columns = [
            "horse_name",
            "draw",
            "jockey",
            "trainer",
            "win_odds",
            "pred_win_prob",
            "ev_value"
        ]
        display_df = result[show_columns].copy()

        # color EV value
        def color_ev_cell(val):
            if pd.isna(val):
                return ""
            if val > 0:
                return "background-color:#005920"
            else:
                return "background-color:#701818"

        styled_table = display_df.style.format({
            "pred_win_prob": "{:.2%}",
            "ev_value": "{:.3f}",
            "win_odds": "{:.1f}"
        }).applymap(color_ev_cell, subset=["ev_value"])

        st.dataframe(styled_table, use_container_width=True)
        st.markdown("""
- **pred_win_prob**: Model‑estimated winning probability
- **ev_value = pred_win_prob * win_odds −1**
- Green cell: EV >0 (theoretical value horse)
- Red cell: EV <=0
        """)

        st.subheader("Top 3 Model Recommendation")
        top3 = display_df.head(3)
        for i, row in top3.iterrows():
            st.metric(
                label=f"{i+1}. {row['horse_name']}",
                value=f"Win prob: {row['pred_win_prob']:.1%}",
                delta=f"EV: {row['ev_value']:.2f}"
            )

if __name__ == "__main__":
    main()
