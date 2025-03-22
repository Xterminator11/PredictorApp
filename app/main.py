import streamlit as st
import json
import os
import socket
import boto3
from jsonpath_ng.ext import parse
from datetime import datetime, timedelta
import datetime as dt
import pandas as pd
import botocore
from botocore.errorfactory import ClientError
from jsonpath_ng.ext import parse

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

    if len(st.session_state.next_matches) == 0:
        st.subheader("No Matches to be played")
        pass
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]

        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")
        json_data = {
            "UserName": user_name,
            "MatchId": match_id,
            "MatchTime": match_details.get("DateUtc"),
            "SubmitTime": datetime.now(tz=dt.timezone.utc).strftime(
                format="%Y-%m-%d %H:%M:%S"
            ),
        }
        selections = []
        for question in st.session_state.json_metadata.get("question_list"):
            selections.append(
                {
                    "q_key": question.get("q_key"),
                    "q_val": st.session_state.get(question.get("q_key")),
                }
            )
        json_data["Selections"] = selections
        s3object = f"{user_name}/{user_name}_{match_id}.json"

        s3 = boto3.resource("s3")
        s3object = s3.Object("predictor-app-dallas-ipl2025", s3object)

        s3object.put(Body=(bytes(json.dumps(json_data).encode("UTF-8"))))


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

    if len(st.session_state.next_matches) == 0:
        st.subheader("No Matches to be played")
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]
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


def form_rendering():

    if len(st.session_state.next_matches) == 0:
        st.subheader("No Matches to be played")
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]

        with st.form("predictions", clear_on_submit=True, enter_to_submit=False):

            for questions in st.session_state.json_metadata.get("question_list"):
                left_container, right_container = st.columns(2, border=False)
                left_container.text(questions.get("questions"))
                if questions.get("display_type") == "radio":
                    right_container.radio(
                        label="Select Below",
                        options=[
                            match_details.get("HomeTeam"),
                            match_details.get("AwayTeam"),
                        ],
                        key=questions.get("q_key"),
                    )
                elif questions.get("display_type") == "slider":
                    right_container.slider(
                        label="Select Below",
                        key=questions.get("q_key"),
                        min_value=1,
                        max_value=1000,
                    )
                else:
                    continue
            st.form_submit_button("Submit Predictions", on_click=store_data_values)


def check_match_date_selected():

    if len(st.session_state.next_matches) == 0:
        st.subheader("No Matches to be played")
        return True
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]
        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")

        s3object = f"{user_name}/{user_name}_{match_id}.json"
        s3 = boto3.client("s3")
        try:
            s3.head_object(Bucket="predictor-app-dallas-ipl2025", Key=s3object)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                return True
        return True


def clear_selections():

    if len(st.session_state.next_matches) == 0:
        st.subheader("No Matches to be played")
        return True
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]
        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")

        s3object = f"{user_name}/{user_name}_{match_id}.json"
        s3 = boto3.client("s3")
        try:
            s3.delete_object(Bucket="predictor-app-dallas-ipl2025", Key=s3object)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                return True
        return True


def display_details_of_the_prediction():

    if len(st.session_state.next_matches) == 0:
        st.subheader("No Matches to be played")
        pass
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]
        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")

        s3object = f"{user_name}/{user_name}_{match_id}.json"
        s3 = boto3.client("s3")
        try:
            data = s3.get_object(Bucket="predictor-app-dallas-ipl2025", Key=s3object)
            contents = json.loads(data["Body"].read().decode("utf-8"))

            for data_selections in contents.get("Selections"):
                left, right = st.columns(2, vertical_alignment="center")
                for question in st.session_state.json_metadata.get("question_list"):
                    if question.get("q_key") == data_selections.get("q_key"):
                        left.text(question.get("questions"))
                        right.text(data_selections.get("q_val"))
                    else:
                        continue

            st.button(
                "Do you want to clear all your selection?",
                key="clear",
                on_click=clear_selections,
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                return True
        return True


if socket.gethostname() == "MacBookPro.lan":
    st.session_state.user_name = "Gururaj Tester"
    st.session_state.next_matches = get_next_match_from_json()
    st.header(f"Welcome, {st.session_state.user_name}!")
    body_rendering()
    ## Add Questions
    check_match_date_selected = check_match_date_selected()
    if not check_match_date_selected:
        form_rendering()
    else:
        st.header("Your selections are locked for today")
        display_details_of_the_prediction()

    st.button("Log out", on_click=st.logout)
else:
    if not st.experimental_user.is_logged_in:
        login_screen()
    else:
        st.session_state.user_name = st.experimental_user.name
        st.session_state.next_matches = get_next_match_from_json()
        st.header(f"Welcome, {st.session_state.user_name}!")
        body_rendering()
        check_match_date_selected = check_match_date_selected()
        if not check_match_date_selected:
            form_rendering()
        else:
            st.header("You Have Already Made selection for this match")
            display_details_of_the_prediction()
        ## Add Questions

        st.button("Log out", on_click=st.logout)
