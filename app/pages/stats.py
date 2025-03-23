import streamlit as st
import json
import boto3
import os
from jsonpath_ng.ext import parse
import pandas as pd
from modules.navigator import Navbar

st.set_page_config(
    page_title="Predictor Statistics",
    page_icon="https://brandlogos.net/wp-content/uploads/2021/12/indian_premier_league-brandlogo.net_.png",
)

st.session_state.json_metadata = json.loads(
    open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "metadata.json"),
        "r",
        encoding="utf-8",
    ).read()
)

st.session_state.json_match = json.loads(
    open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "match_details.json"),
        "r",
        encoding="utf-8",
    ).read()
)

Navbar()


def get_individual_data_from_backend():
    pass


def update_statistics():

    if (
        st.session_state.selected_option == "Choose a match"
        or st.session_state.selected_option is None
    ):
        return 0
    match_number = str(st.session_state.selected_option).split("-")[0].strip()

    match_status = {}
    for matches in st.session_state.json_match:
        if matches.get("MatchNumber") == int(match_number):
            match_status = matches
        else:
            continue

    if not match_status.get("ResultsPublished"):
        df = pd.DataFrame(
            {
                "Stats": ["Not Available"],
                f"{match_status.get("HomeTeam")}": ["Not Available"],
                f"{match_status.get("AwayTeam")}": ["Not Available"],
            }
        )
        st.session_state.df = df
    else:

        # Get the Status By Team
        stats_list = []
        home_team = []
        away_team = []
        for question in st.session_state.json_metadata.get("question_list"):
            stats_list.append(question.get("stats_key"))
            home_team.append(
                match_status.get("ResultsStats").get(
                    f"HomeTeam_{question.get("q_key")}"
                )
            )
            away_team.append(
                match_status.get("ResultsStats").get(
                    f"AwayTeam_{question.get("q_key")}"
                )
            )

        df = pd.DataFrame(
            {
                "Stats": stats_list,
                f"{match_status.get("HomeTeam")}": home_team,
                f"{match_status.get("AwayTeam")}": away_team,
            }
        )
        st.session_state.df = df


st.header(f"Welcome, {st.session_state.user_name}!")
st.subheader("This section contains individual games")
selections = []
for matches in st.session_state.json_match:
    selections.append(
        f"{matches.get("MatchNumber")} - {matches.get("HomeTeam")} vs {matches.get("AwayTeam")} ({matches.get("MatchCompletionStatus")})"
    )
st.selectbox(
    "Pick The Game",
    options=selections,
    on_change=update_statistics,
    index=None,
    placeholder="Choose a match",
    key="selected_option",
)

with st.container():
    st.divider()
    st.subheader("Below is the statistics of the match")
    if "df" in st.session_state:
        st.table(st.session_state.df)
