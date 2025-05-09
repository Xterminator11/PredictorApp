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
from modules.navigator import Navbar

st.suspend = True

st.session_state.json_metadata = json.loads(
    open(
        os.path.join(os.path.dirname(__file__), "metadata.json"), "r", encoding="utf-8"
    ).read()
)

st.set_page_config(
    page_title="Predictor Home Page",
    page_icon="https://brandlogos.net/wp-content/uploads/2021/12/indian_premier_league-brandlogo.net_.png",
)
Navbar()

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


def multi_select_check_1():
    if st.session_state.booster_2 or st.session_state.booster_3:
        st.session_state.booster_2 = False
        st.session_state.booster_3 = False


def multi_select_check_2():
    if st.session_state.booster_1 or st.session_state.booster_3:
        st.session_state.booster_1 = False
        st.session_state.booster_3 = False


def multi_select_check_3():
    if st.session_state.booster_2 or st.session_state.booster_1:
        st.session_state.booster_2 = False
        st.session_state.booster_1 = False


def get_booster_data_file(match_id):

    # 1.⁠ ⁠Game 1 to Game 20
    # 2.⁠ ⁠⁠Game 21 to Game 40
    # 3.⁠ ⁠⁠Game 41 to Game 60
    # 4.⁠ ⁠⁠Game 61 to Game 70
    # 5.⁠ ⁠⁠Game 71 to Game 74

    if 0 <= match_id <= 20:
        return "match_booster.json"
    elif 21 <= match_id <= 40:
        return "match_booster_1.json"
    elif 41 <= match_id <= 60:
        return "match_booster_2.json"
    elif 61 <= match_id <= 70:
        return "match_booster_3.json"
    elif 71 <= match_id <= 74:
        return "match_booster_4.json"


def get_booster_information():

    if len(st.session_state.next_matches) == 0:
        st.subheader("No Matches to be played")
        return False, False, False, {}
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]

        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")

        booster_data_found = False
        s3object = f"{user_name}/{get_booster_data_file(match_id)}"
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


def store_booster_information():

    if len(st.session_state.next_matches) == 0:
        st.subheader("No Matches to be played")
        return False, False, False, {}
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]

        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")

        booster_1, booster_2, booster_3, booster_data = get_booster_information()

        if st.session_state.booster_1 is True:
            booster_data["booster_1"] = match_id

        if st.session_state.booster_2 is True:
            booster_data["booster_2"] = match_id

        if st.session_state.booster_3 is True:
            booster_data["booster_3"] = match_id

        s3object = f"{user_name}/{get_booster_data_file(match_id)}"

        s3 = boto3.resource("s3")
        s3object = s3.Object("predictor-app-dallas-ipl2025", s3object)

        s3object.put(Body=(bytes(json.dumps(booster_data).encode("UTF-8"))))


def clear_booster_details():

    if len(st.session_state.next_matches) == 0:
        st.subheader("No Matches to be played")
        return False, False, False, {}
    else:
        ## Add headers

        match_details = json.loads(st.session_state.next_matches)[0]

        user_name = str(st.session_state.user_name).replace(" ", "").lower()
        match_id = match_details.get("MatchNumber")

        booster_1, booster_2, booster_3, booster_data = get_booster_information()

        for booster_keys in booster_data.keys():
            if booster_data.get(booster_keys) == match_id:
                booster_data[booster_keys] = 0
            else:
                continue

        s3object = f"{user_name}/match_booster.json"

        s3 = boto3.resource("s3")
        s3object = s3.Object("predictor-app-dallas-ipl2025", s3object)
        s3object.put(Body=(bytes(json.dumps(booster_data).encode("UTF-8"))))


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

        # Store Booster Data

        store_booster_information()


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

        st.subheader("Select Booster for this match")
        booster_1, booster_2, booster_3 = st.columns(3, border=True)
        st.divider()

        booster_5x, booster_3x, booster_2x, booster_data = get_booster_information()

        booster_1.toggle(
            "5x 🔥🔥🔥🔥🔥",
            disabled=booster_5x,
            label_visibility="visible",
            help=(
                "5X of your total score"
                if booster_5x is False
                else f"Booster was used in match number {booster_data.get("booster_1")}"
            ),
            key="booster_1",
            on_change=multi_select_check_1,
        )
        booster_2.toggle(
            "3x 🔥🔥🔥 ",
            disabled=booster_3x,
            label_visibility="visible",
            help=(
                "3X of your total score"
                if booster_3x is False
                else f"Booster was used in match number {booster_data.get("booster_2")}"
            ),
            key="booster_2",
            on_change=multi_select_check_2,
        )
        booster_3.toggle(
            "2x 🔥🔥",
            disabled=booster_2x,
            label_visibility="visible",
            help=(
                "2X of your total score"
                if booster_2x is False
                else f"Booster was used in match number {booster_data.get("booster_3")}"
            ),
            key="booster_3",
            on_change=multi_select_check_3,
        )

        with st.form("predictions", clear_on_submit=True, enter_to_submit=False):
            st.subheader("Select Predictions for this match")
            for question in st.session_state.json_metadata.get("question_list"):
                left_container, right_container = st.columns(2, border=False)
                left_container.text(
                    f"{question.get("questions")} ({question.get("points")} Points)"
                )
                if question.get("display_type") == "radio":
                    right_container.radio(
                        label="Select Below",
                        options=[
                            match_details.get("HomeTeam"),
                            match_details.get("AwayTeam"),
                        ],
                        key=question.get("q_key"),
                    )
                elif question.get("display_type") == "slider":
                    right_container.slider(
                        label="Select Below",
                        key=question.get("q_key"),
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
            clear_booster_details()
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

        booster_1, booster_2, booster_3, contents_booster = get_booster_information()
        try:
            data = s3.get_object(Bucket="predictor-app-dallas-ipl2025", Key=s3object)
            contents = json.loads(data["Body"].read().decode("utf-8"))

            for booster in contents_booster.keys():
                if contents_booster.get(booster) == match_id:
                    booster_details = (
                        "5x"
                        if booster == "booster_1"
                        else "3x" if booster == "booster_2" else "2x"
                    )
                    st.subheader(f"Booster Selected for this match : {booster_details}")

            for data_selections in contents.get("Selections"):
                left, right = st.columns(2, vertical_alignment="center")
                for question in st.session_state.json_metadata.get("question_list"):
                    if question.get("q_key") == data_selections.get("q_key"):
                        left.subheader(
                            f":orange[{question.get("questions")} ({question.get("points")} Points)]"
                        )
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


if st.suspend == True:
    st.header("Due to Operations Sindoor !! Prediction game is suspended")
else:
    if socket.gethostname() == "MacBookPro.lan":
        st.session_state.user_name = "Gururaj Rao"
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

        # Render Statistics

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
                st.header("Your selections are locked for today")
                display_details_of_the_prediction()
            ## Add Questions

            st.button("Log out", on_click=st.logout)
