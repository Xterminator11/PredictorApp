import streamlit as st
import json
import os
import socket
import boto3
from jsonpath_ng.ext import parse
from datetime import datetime, timedelta
import datetime as dt
import pandas as pd

st.session_state.json_metadata = json.loads(
    open(
        os.path.join(os.path.dirname(__file__), "metadata.json"), "r", encoding="utf-8"
    ).read()
)

title_alignment = """
<style>
#the-title {
  text-align: center
}
</style>
"""
st.markdown(title_alignment, unsafe_allow_html=True)


def login_screen():
    st.header("Welcome to Predictor App for IPL 2025")
    st.subheader("Please log in.")
    st.button("Log in with Google", on_click=st.login)


def store_data_values():
    # s3_bucket = boto3.client('s3')
    # s3_bucket.upload_file()
    pass


def get_next_match_from_json() -> list:

    match_details_json = os.path.join(os.path.dirname(__file__), "match_details.json")

    data_frame = pd.read_json(
        match_details_json,
        orient="records",
        convert_dates=["DateUtc"],
    )

    current_time = pd.Timestamp.now(tz=dt.timezone.utc)
    # Filter Data Frame Now

    data_frame = data_frame[data_frame["DateUtc"] > current_time.to_datetime64()]

    data_frame = data_frame[
        data_frame["MatchNumber"] == data_frame["MatchNumber"].min()
    ]

    if len(data_frame) == 0:
        return []
    return data_frame.fillna("").to_json(
        orient="records", date_format="iso", date_unit="s"
    )


def body_rendering():
    ## Now lets add match details.

    next_matches = get_next_match_from_json()
    if len(next_matches) == 0:
        st.subheader("No Matches to be played")
    else:
        ## Add headers

        match_details = json.loads(next_matches)[0]
        left, middle, right = st.columns(3, border=True, vertical_alignment="center")

        left.image(
            st.session_state.json_metadata.get("teams_image").get(
                match_details.get("HomeTeam")
            )
        )
        left.text(match_details.get("HomeTeam"))

        right.image(
            st.session_state.json_metadata.get("teams_image").get(
                match_details.get("AwayTeam")
            )
        )
        right.text(match_details.get("AwayTeam"))

        middle.text(
            "Match Number {} \nOn {} \nat {}".format(
                match_details.get("MatchNumber"),
                match_details.get("DateUtc"),
                match_details.get("Location"),
            )
        )
        # middle.image(
        #     "https://www.creativefabrica.com/wp-content/uploads/2021/11/09/Versus-Vs-Vector-Transparent-Background-Graphics-19913250-2-580x386.png"
        # )

        ## Add Questions

        with st.form("predictions", clear_on_submit=True, enter_to_submit=False):
            st.radio(
                label="Who Will win the game? (5 pts)",
                options=[
                    match_details.get("HomeTeam"),
                    match_details.get("AwayTeam"),
                ],
                key="winner",
            )
            st.radio(
                label="Which team will score most sixes? (10 pts)",
                options=[
                    match_details.get("HomeTeam"),
                    match_details.get("AwayTeam"),
                ],
                key="sixes",
            )
            st.radio(
                label="Which team will score most fours? (10 pts)",
                options=[
                    match_details.get("HomeTeam"),
                    match_details.get("AwayTeam"),
                ],
                key="fours",
            )
            st.radio(
                label="Which team will take most wickets? (10 pts)",
                options=[
                    match_details.get("HomeTeam"),
                    match_details.get("AwayTeam"),
                ],
                key="wickets",
            )
            st.radio(
                label="Will there be a century in this game? (5 pts)",
                options=["Yes", "No"],
                key="century",
            )
            st.slider(
                label="What will be the score posted by {}?".format(
                    match_details.get("HomeTeam")
                ),
                key="score_home",
                min_value=1,
                max_value=400,
            )
            st.slider(
                label="What will be the score posted by {}?".format(
                    match_details.get("AwayTeam")
                ),
                key="score_away",
                min_value=1,
                max_value=400,
            )
            st.form_submit_button("Submit Predictions", on_click=store_data_values)

        st.button("Log out", on_click=st.logout)


if socket.gethostname() == "MacBookPro.lan":
    st.session_state.user_name = "Gururaj Tester"
    st.header(f"Welcome, {st.session_state.user_name}!")
    body_rendering()

else:
    if not st.experimental_user.is_logged_in:
        login_screen()
    else:
        st.session_state.user_name = st.experimental_user.name
        st.header(f"Welcome, {st.session_state.user_name}!")
        body_rendering()
