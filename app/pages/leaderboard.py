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
    page_title="Leader Board",
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


def get_aggregate_data():

    ## Add headers
    user_name = str(st.session_state.user_name).replace(" ", "").lower()

    s3 = boto3.client("s3")
    try:
        s3object = "aggregates/leaderboard.txt"
        data = s3.get_object(Bucket="predictor-app-dallas-ipl2025", Key=s3object)
        contents = json.loads(data["Body"].read().decode("utf-8"))
        st.session_state.df_leaderboard = pd.DataFrame(contents)

        s3object = "aggregates/transactional.txt"
        data = s3.get_object(Bucket="predictor-app-dallas-ipl2025", Key=s3object)
        contents = json.loads(data["Body"].read().decode("utf-8"))
        df = pd.DataFrame(contents)
        st.session_state.df_all = df
        st.session_state.df_individual = df[df["UserName"] == user_name].reset_index(
            drop=True
        )

    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            return False


def get_user_name():
    if "df_all" not in st.session_state:
        return []
    else:
        df_user_name_list = (
            st.session_state.df_all.sort_values(by="UserName")["UserName"]
            .unique()
            .tolist()
        )
        return df_user_name_list


def get_user_data():

    if (
        st.session_state.user_select == "Select a User"
        or st.session_state.user_select is None
    ):
        return 0

    st.session_state.df_selected = st.session_state.df_all[
        st.session_state.df_all["UserName"] == st.session_state.user_select
    ].reset_index(drop=True)


if socket.gethostname() == "MacBookPro.lan":
    st.session_state.user_name = "Gururaj Rao"
    st.subheader("Leaderboard")
    selections = []
    get_aggregate_data()
    with st.container():
        st.divider()
        st.subheader("Overall Leaderboard")
        if "df_leaderboard" in st.session_state:
            st.dataframe(
                data=st.session_state.df_leaderboard,
                on_select="ignore",
                hide_index=True,
                use_container_width=True,
            )

        st.divider()
        st.subheader("Your Selections")
        if "df_individual" in st.session_state:
            st.dataframe(
                data=st.session_state.df_individual,
                on_select="ignore",
                hide_index=True,
                use_container_width=True,
            )

        st.divider()
        st.subheader("View Stats for other Users")
        st.selectbox(
            "Select User",
            options=get_user_name(),
            key="user_select",
            on_change=get_user_data,
            index=0,
            placeholder="Select a User",
        )
        get_user_data()
        # Render Statistics
        if "df_selected" in st.session_state:
            st.dataframe(
                data=st.session_state.df_selected,
                on_select="ignore",
                hide_index=True,
                use_container_width=True,
            )

    st.button("Log out", on_click=st.logout)
else:
    if not st.experimental_user.is_logged_in or "name" not in st.experimental_user:
        login_screen()
    else:
        st.session_state.user_name = st.experimental_user.name
    st.subheader("Leaderboard")
    selections = []
    get_aggregate_data()

    with st.container():
        st.divider()
        st.subheader("Overall Leaderboard")
        if "df_leaderboard" in st.session_state:
            st.dataframe(
                data=st.session_state.df_leaderboard,
                on_select="ignore",
                hide_index=True,
                use_container_width=True,
            )

        st.divider()
        st.subheader("Your Selections")
        if "df_individual" in st.session_state:
            st.dataframe(
                data=st.session_state.df_individual,
                on_select="ignore",
                hide_index=True,
                use_container_width=True,
            )

        st.divider()
        st.subheader("View Stats for other Users")
        st.selectbox(
            "Select User",
            options=get_user_name(),
            key="user_select",
            on_change=get_user_data,
            index=0,
            placeholder="Select a User",
        )
        get_user_data()
        # Render Statistics
        if "df_selected" in st.session_state:
            st.dataframe(
                data=st.session_state.df_selected,
                on_select="ignore",
                hide_index=True,
                use_container_width=True,
            )

        st.button("Log out", on_click=st.logout)
