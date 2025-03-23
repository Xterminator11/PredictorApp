import streamlit as st
import json
import boto3
import os
from jsonpath_ng.ext import parse
import pandas as pd
from modules.navigator import Navbar
import socket
import botocore
from botocore.errorfactory import ClientError

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


def login_screen():
    st.header("Welcome to Predictor App for IPL 2025")
    st.subheader("Please log in.")
    st.button("Log in with Google", on_click=st.login)


def get_individual_data_from_backend(match_id):

    ## Add headers
    user_name = str(st.session_state.user_name).replace(" ", "").lower()

    s3object = f"{user_name}/{user_name}_{match_id}.json"
    s3 = boto3.client("s3")
    try:
        data = s3.get_object(Bucket="predictor-app-dallas-ipl2025", Key=s3object)
        contents = json.loads(data["Body"].read().decode("utf-8"))
        return contents.get("Selections")

    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            return False


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

        df_player = pd.DataFrame(
            {
                "Question": ["Not Available"],
                "Your Prediction": ["Not Available"],
                "Correct Prediction": ["Not Available"],
                "Points": ["Not Available"],
            }
        )
        st.session_state.df_player = df_player

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

        ## You Individual Prediction

        questions = []
        prediction = []
        correct = []
        point = []

        for question in st.session_state.json_metadata.get("question_list"):
            questions.append(question.get("questions"))
            correct_selection = match_status.get("PredictionResults").get(
                question.get("q_key")
            )
            correct.append(correct_selection)

            match_selection = get_individual_data_from_backend(
                match_status.get("MatchNumber")
            )
            user_selection = ""
            if match_selection:
                for q_key in match_selection:
                    if q_key.get("q_key") == question.get("q_key"):
                        user_selection = q_key.get("q_val")
                        break
                    else:
                        continue
            else:
                if question.get("q_key") == "totalscore":
                    user_selection = 0
                else:
                    user_selection = ""
            prediction.append(str(user_selection))

            if question.get("q_key") == "totalscore":
                correct_score = int(correct_selection)
                your_score = int(user_selection)
                percentage_deviation = round(
                    (
                        (
                            abs(
                                100
                                - abs(
                                    ((correct_score - your_score) / (correct_score))
                                    * 100
                                )
                            )
                        )
                        / 100
                    )
                    * int(question.get("points")),
                    2,
                )
                point.append(str(percentage_deviation))
            else:
                if correct_selection == "Tie" and user_selection != "":
                    point.append(str(question.get("points")))
                else:
                    if user_selection == correct_selection:
                        point.append(str(question.get("points")))
                    else:
                        point.append(str(0))

        df_player = pd.DataFrame(
            {
                "Question": questions,
                "Your Prediction": prediction,
                "Correct Prediction": correct,
                "Points": point,
            }
        )
        st.session_state.df_player = df_player


if socket.gethostname() == "MacBookPro.lan":
    st.session_state.user_name = "Gururaj Rao"
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
        st.subheader("Statistics of the match")
        if "df" in st.session_state:
            st.table(st.session_state.df)

        st.divider()
        st.subheader("Prediction Results for the match")
        if "df_player" in st.session_state:
            st.table(st.session_state.df_player)

    # Render Statistics

    st.button("Log out", on_click=st.logout)
else:
    if not st.experimental_user.is_logged_in or "name" not in st.experimental_user:
        login_screen()
    else:
        st.session_state.user_name = st.experimental_user.name
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
            st.subheader("Statistics of the match")
            if "df" in st.session_state:
                st.table(st.session_state.df)

            st.divider()
            st.subheader("Prediction Results for the match")
            if "df_player" in st.session_state:
                st.table(st.session_state.df_player)
        st.button("Log out", on_click=st.logout)
