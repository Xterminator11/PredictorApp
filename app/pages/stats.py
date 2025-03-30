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
import datetime as dt

st.set_page_config(
    page_title="Predictor Statistics",
    page_icon="https://brandlogos.net/wp-content/uploads/2021/12/indian_premier_league-brandlogo.net_.png",
)

st.session_state.booster_value = 1

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


def get_next_match_from_json() -> list:

    match_details_json = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "match_details.json"
    )

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


def get_booster_information(match_status, user_name):

    user_name = str(user_name).replace(" ", "").lower()
    match_id = match_status.get("MatchNumber")

    booster_data_found = False
    s3object = f"{user_name}/match_booster.json"
    s3 = boto3.client("s3")
    try:
        s3.head_object(Bucket="predictor-app-dallas-ipl2025", Key=s3object)
        booster_data_found = True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            booster_data_found = False
        else:
            booster_data_found = False

    booster_1 = False
    booster_2 = False
    booster_3 = False

    if booster_data_found is False:
        booster_data = {"booster_1": 0, "booster_2": 0, "booster_3": 0}

    else:
        data = s3.get_object(Bucket="predictor-app-dallas-ipl2025", Key=s3object)
        booster_data = json.loads(data["Body"].read().decode("utf-8"))

        booster_1 = True if booster_data.get("booster_1") > 0 else False
        booster_2 = True if booster_data.get("booster_2") > 0 else False
        booster_3 = True if booster_data.get("booster_3") > 0 else False

    return booster_1, booster_2, booster_3, booster_data


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

    booster_1, booster_2, booster_3, contents_booster = get_booster_information(
        match_status, st.session_state.user_name
    )

    for booster in contents_booster.keys():
        if contents_booster.get(booster) == int(match_number):
            booster_details = (
                "5x"
                if booster == "booster_1"
                else "3x" if booster == "booster_2" else "2x"
            )
            st.session_state.booster_value = int(booster_details.replace("x", ""))

    if not match_status.get("ResultsPublished"):
        st.session_state.statistics_url = "Not Available"
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

        st.session_state.statistics_url = match_status.get("ResultsStats").get(
            "StatsLink"
        )
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

            # Point Selection

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
                point.append(str(percentage_deviation * st.session_state.booster_value))
            else:
                if correct_selection == "Tie" and user_selection != "":
                    point.append(
                        str(question.get("points") * st.session_state.booster_value)
                    )
                else:
                    if user_selection == correct_selection:
                        point.append(
                            str(question.get("points") * st.session_state.booster_value)
                        )
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
    st.session_state.next_matches = get_next_match_from_json()
    st.subheader("This section contains individual games")
    selections = []
    for matches in st.session_state.json_match:
        if matches.get("MatchCompletionStatus") == "Completed":
            match_number = (
                str(matches.get("MatchNumber"))
                if matches.get("MatchNumber") > 9
                else f"0{matches.get("MatchNumber")}"
            )
            selections.append(
                f"{match_number} - {matches.get("HomeTeam")} vs {matches.get("AwayTeam")} ({matches.get("MatchCompletionStatus")})"
            )
    selections.sort(reverse=True)
    st.selectbox(
        "Pick The Game",
        options=selections,
        on_change=update_statistics,
        # index=None,
        # placeholder="Choose a match",
        key="selected_option",
        disabled=False,
    )
    update_statistics()

    with st.container():
        st.divider()
        st.subheader("Statistics of the match")
        if "statistics_url" in st.session_state:
            st.markdown(
                f"Statistics Provided by [espncricinfo]({st.session_state.statistics_url})"
            )
        if "df" in st.session_state:
            st.dataframe(
                data=st.session_state.df,
                on_select="ignore",
                hide_index=True,
                use_container_width=True,
            )

        st.divider()
        if st.session_state.booster_value != 1:
            st.subheader(
                f":red[Booster selected for this game : {st.session_state.booster_value}x]"
            )
        st.subheader("Prediction Results for the match")
        if "df_player" in st.session_state:
            st.dataframe(
                data=st.session_state.df_player,
                on_select="ignore",
                hide_index=True,
                use_container_width=True,
            )

    # Render Statistics

    st.button("Log out", on_click=st.logout)
else:

    if not st.experimental_user.is_logged_in or "name" not in st.experimental_user:
        login_screen()
    else:
        st.session_state.next_matches = get_next_match_from_json()
        st.session_state.user_name = st.experimental_user.name
        st.subheader("This section contains individual games")
        selections = []
        for matches in st.session_state.json_match:
            if matches.get("MatchCompletionStatus") == "Completed":
                match_number = (
                    str(matches.get("MatchNumber"))
                    if matches.get("MatchNumber") > 9
                    else f"0{matches.get("MatchNumber")}"
                )
                selections.append(
                    f"{match_number} - {matches.get("HomeTeam")} vs {matches.get("AwayTeam")} ({matches.get("MatchCompletionStatus")})"
                )
        selections.sort(reverse=True)
        st.selectbox(
            "Pick The Game",
            options=selections,
            on_change=update_statistics,
            # index=None,
            # placeholder="Choose a match",
            key="selected_option",
        )

        update_statistics()

        with st.container():
            st.divider()
            st.subheader("Statistics of the match")
            if "statistics_url" in st.session_state:
                st.markdown(
                    f"Statistics Provided by [link]({st.session_state.statistics_url})"
                )
            if "df" in st.session_state:
                st.dataframe(
                    data=st.session_state.df,
                    on_select="ignore",
                    hide_index=True,
                    use_container_width=True,
                )

            st.divider()
            if st.session_state.booster_value != 1:
                st.subheader(
                    f":red[Booster selected for this game : {st.session_state.booster_value}x]"
                )
            st.subheader("Prediction Results for the match")
            if "df_player" in st.session_state:
                st.dataframe(
                    data=st.session_state.df_player,
                    on_select="ignore",
                    hide_index=True,
                    use_container_width=True,
                )
        st.button("Log out", on_click=st.logout)
