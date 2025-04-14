import streamlit as st
import json
import boto3
import os
import pandas as pd
from modules.navigator import Navbar
import socket
import botocore
import datetime as dt

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


def update_results(input_metrics):
    if input_metrics == "totalscore":
        return (
            st.session_state.HomeTeam_totalscore + st.session_state.AwayTeam_totalscore
        )
    elif input_metrics == "winner":
        return (
            st.session_state.home_team
            if st.session_state.HomeTeam_winner == "Won"
            else st.session_state.away_team
        )
    elif input_metrics == "wicket":
        if st.session_state.HomeTeam_wickets == st.session_state.AwayTeam_wickets:
            return "Tie"
        else:
            return (
                st.session_state.home_team
                if st.session_state.AwayTeam_wickets > st.session_state.HomeTeam_wickets
                else st.session_state.away_team
            )
    else:
        if st.session_state.get(f"HomeTeam_{input_metrics}") == st.session_state.get(
            f"AwayTeam_{input_metrics}"
        ):
            return "Tie"
        else:
            return (
                st.session_state.home_team
                if st.session_state.get(f"HomeTeam_{input_metrics}")
                > st.session_state.get(f"AwayTeam_{input_metrics}")
                else st.session_state.away_team
            )


def store_match_details():
    st.text("Match Submitted")

    match_details = []
    for matches in st.session_state.json_match:
        if matches.get("MatchNumber") == st.session_state.match_number_selected:
            matches["PredictionResults"] = {
                "winner": update_results("winner"),
                "fours": update_results("fours"),
                "sixes": update_results("sixes"),
                "wickets": update_results("wickets"),
                "powerplay": update_results("powerplay"),
                "totalscore": str(update_results("totalscore")),
            }
            matches["ResultsStats"] = {
                "HomeTeam_totalscore": str(st.session_state.HomeTeam_totalscore),
                "HomeTeam_wickets": str(st.session_state.HomeTeam_wickets),
                "AwayTeam_totalscore": str(st.session_state.AwayTeam_totalscore),
                "AwayTeam_wickets": str(st.session_state.AwayTeam_wickets),
                "AwayTeam_fours": str(st.session_state.AwayTeam_fours),
                "AwayTeam_sixes": str(st.session_state.AwayTeam_sixes),
                "HomeTeam_fours": str(st.session_state.HomeTeam_fours),
                "HomeTeam_sixes": str(st.session_state.HomeTeam_sixes),
                "HomeTeam_powerplay": str(st.session_state.HomeTeam_powerplay),
                "AwayTeam_powerplay": str(st.session_state.AwayTeam_powerplay),
                "HomeTeam_winner": str(st.session_state.HomeTeam_winner),
                "AwayTeam_winner": str(st.session_state.AwayTeam_winner),
                "StatsLink": str(st.session_state.StatsLink),
            }
            matches["MatchCompletionStatus"] = "Completed"
            matches["ResultsPublished"] = True

            match_details.append(matches)
        else:
            match_details.append(matches)

    match_details_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "match_details.json"
    )
    with open(match_details_path, "w") as f:
        f.write(json.dumps(match_details, indent=4))
        f.close()
    st.session_state.json_match = json.loads(
        open(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "match_details.json"
            ),
            "r",
            encoding="utf-8",
        ).read()
    )


def update_match_label():
    if "selected_option" in st.session_state:
        st.session_state.home_team = (
            st.session_state.selected_option.split("-")[1]
            .split("(")[0]
            .split("vs")[0]
            .strip()
        )
        st.session_state.away_team = (
            st.session_state.selected_option.split("-")[1]
            .split("(")[0]
            .split("vs")[1]
            .strip()
        )

        st.session_state.match_number_selected = int(
            st.session_state.selected_option.split("-")[0].strip()
        )

        # Updata Values

        for matches in st.session_state.json_match:
            if matches.get("MatchNumber") == st.session_state.match_number_selected:
                st.session_state["HomeTeam_totalscore"] = (
                    int(matches.get("ResultsStats").get("HomeTeam_totalscore"))
                    if matches.get("ResultsStats").get("HomeTeam_totalscore")
                    != "NOT_PUBLISHED"
                    else 0
                )
                st.session_state.HomeTeam_wickets = (
                    int(matches.get("ResultsStats").get("HomeTeam_wickets"))
                    if matches.get("ResultsStats").get("HomeTeam_wickets")
                    != "NOT_PUBLISHED"
                    else 0
                )
                st.session_state.AwayTeam_totalscore = (
                    int(matches.get("ResultsStats").get("AwayTeam_totalscore"))
                    if matches.get("ResultsStats").get("AwayTeam_totalscore")
                    != "NOT_PUBLISHED"
                    else 0
                )
                st.session_state.AwayTeam_wickets = (
                    int(matches.get("ResultsStats").get("AwayTeam_wickets"))
                    if matches.get("ResultsStats").get("AwayTeam_wickets")
                    != "NOT_PUBLISHED"
                    else 0
                )
                st.session_state.AwayTeam_fours = (
                    int(matches.get("ResultsStats").get("AwayTeam_fours"))
                    if matches.get("ResultsStats").get("AwayTeam_fours")
                    != "NOT_PUBLISHED"
                    else 0
                )
                st.session_state.AwayTeam_sixes = (
                    int(matches.get("ResultsStats").get("AwayTeam_sixes"))
                    if matches.get("ResultsStats").get("AwayTeam_sixes")
                    != "NOT_PUBLISHED"
                    else 0
                )
                st.session_state.HomeTeam_fours = (
                    int(matches.get("ResultsStats").get("HomeTeam_fours"))
                    if matches.get("ResultsStats").get("HomeTeam_fours")
                    != "NOT_PUBLISHED"
                    else 0
                )
                st.session_state.HomeTeam_sixes = (
                    int(matches.get("ResultsStats").get("HomeTeam_sixes"))
                    if matches.get("ResultsStats").get("HomeTeam_sixes")
                    != "NOT_PUBLISHED"
                    else 0
                )
                st.session_state.HomeTeam_powerplay = (
                    int(matches.get("ResultsStats").get("HomeTeam_powerplay"))
                    if matches.get("ResultsStats").get("HomeTeam_powerplay")
                    != "NOT_PUBLISHED"
                    else 0
                )
                st.session_state.AwayTeam_powerplay = (
                    int(matches.get("ResultsStats").get("AwayTeam_powerplay"))
                    if matches.get("ResultsStats").get("AwayTeam_powerplay")
                    != "NOT_PUBLISHED"
                    else 0
                )
                st.session_state.HomeTeam_winner = (
                    matches.get("ResultsStats").get("HomeTeam_winner")
                    if matches.get("ResultsStats").get("HomeTeam_winner")
                    != "NOT_PUBLISHED"
                    else "Won"
                )
                st.session_state.AwayTeam_winner = (
                    matches.get("ResultsStats").get("AwayTeam_winner")
                    if matches.get("ResultsStats").get("AwayTeam_winner")
                    != "NOT_PUBLISHED"
                    else "Won"
                )
                st.session_state.StatsLink = (
                    matches.get("ResultsStats").get("StatsLink")
                    if matches.get("ResultsStats").get("StatsLink") != "NOT_PUBLISHED"
                    else "NOT_PUBLISHED"
                )
                break
            else:
                continue


def cleanup_previous_instance():
    for key in [
        "HomeTeam_totalscore",
        "HomeTeam_wickets",
        "AwayTeam_totalscore",
        "AwayTeam_wickets",
        "AwayTeam_fours",
        "AwayTeam_sixes",
        "HomeTeam_fours",
        "HomeTeam_sixes",
        "HomeTeam_powerplay",
        "AwayTeam_powerplay",
        "HomeTeam_winner",
        "AwayTeam_winner",
        "StatsLink",
    ]:
        if key in st.session_state:
            st.session_state.pop(key)
        else:
            continue


def create_input_form_match_details():
    cleanup_previous_instance()
    update_match_label()
    home_team, away_team = st.columns(2, gap="medium")
    st.text_input(label="StatsLink", key="StatsLink")
    st.button(label="Submit", on_click=store_match_details)
    with home_team:
        st.number_input(
            label=f"{st.session_state.home_team} Score",
            key="HomeTeam_totalscore",
            format="%u",
            min_value=0,
            max_value=300,
        )
        st.number_input(
            label=f"{st.session_state.home_team} Wickets",
            key="HomeTeam_wickets",
            format="%u",
            min_value=0,
            max_value=10,
        )
        st.number_input(
            label=f"{st.session_state.home_team} Fours",
            key="HomeTeam_fours",
            format="%u",
            min_value=0,
            max_value=50,
        )
        st.number_input(
            label=f"{st.session_state.home_team} Sixes",
            key="HomeTeam_sixes",
            format="%u",
            min_value=0,
            max_value=50,
        )
        st.number_input(
            label=f"{st.session_state.home_team} Powerplay",
            key="HomeTeam_powerplay",
            format="%u",
            min_value=0,
            max_value=150,
        )
        st.selectbox(
            label=f"{st.session_state.home_team} Result",
            key="HomeTeam_winner",
            options=["Won", "Lost"],
        )
    with away_team:
        st.number_input(
            label=f"{st.session_state.away_team} Score",
            key="AwayTeam_totalscore",
            format="%u",
            min_value=0,
            max_value=300,
        )
        st.number_input(
            label=f"{st.session_state.away_team} Wickets",
            key="AwayTeam_wickets",
            format="%u",
            min_value=0,
            max_value=10,
        )
        st.number_input(
            label=f"{st.session_state.away_team} Fours",
            key="AwayTeam_fours",
            format="%u",
            min_value=0,
            max_value=50,
        )
        st.number_input(
            label=f"{st.session_state.away_team} Sixes",
            key="AwayTeam_sixes",
            format="%u",
            min_value=0,
            max_value=50,
        )
        st.number_input(
            label=f"{st.session_state.away_team} Powerplay",
            key="AwayTeam_powerplay",
            format="%u",
            min_value=0,
            max_value=150,
        )
        st.selectbox(
            label=f"{st.session_state.home_team} Result",
            key="AwayTeam_winner",
            options=["Won", "Lost"],
        )


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


if socket.gethostname() == "MacBookPro.lan":
    st.session_state.user_name = "Gururaj Rao"
    st.subheader("Admin Page")
    st.session_state.next_matches = json.loads(get_next_match_from_json())
    if len(st.session_state.next_matches) != 0:
        st.session_state.current_match_dictionary = st.session_state.next_matches[0]
    else:
        st.session_state.current_match_dictionary = {}

    if "home_team" not in st.session_state:
        st.session_state.home_team = "HomeTeam"
    if "away_team" not in st.session_state:
        st.session_state.away_team = "AwayTeam"
    if "match_number_selected" not in st.session_state:
        st.session_state.match_number_selected = 0

    if st.session_state.user_name == "Gururaj Rao":
        with st.container():
            st.subheader("Select team and update stats")
            selections = []
            for matches in st.session_state.json_match:
                if matches.get("MatchCompletionStatus") == "Completed" or (
                    matches.get("MatchNumber")
                    == (
                        st.session_state.current_match_dictionary.get("MatchNumber") - 1
                    )
                    or matches.get("MatchNumber")
                    == (
                        st.session_state.current_match_dictionary.get("MatchNumber") - 2
                    )
                ):
                    match_number = (
                        str(matches.get("MatchNumber"))
                        if matches.get("MatchNumber") > 9
                        else f"0{matches.get("MatchNumber")}"
                    )
                    if matches.get("MatchNumber") == (
                        st.session_state.current_match_dictionary.get("MatchNumber") - 1
                    ) or matches.get("MatchNumber") == (
                        st.session_state.current_match_dictionary.get("MatchNumber") - 2
                    ):
                        if matches.get("MatchCompletionStatus") == "Completed":
                            selections.append(
                                f"{match_number} - {matches.get("HomeTeam")} vs {matches.get("AwayTeam")} ({matches.get("MatchCompletionStatus")})"
                            )
                        else:
                            selections.append(
                                f"{match_number} - {matches.get("HomeTeam")} vs {matches.get("AwayTeam")} (In Progress)"
                            )
                    else:
                        selections.append(
                            f"{match_number} - {matches.get("HomeTeam")} vs {matches.get("AwayTeam")} ({matches.get("MatchCompletionStatus")})"
                        )
            selections.sort(reverse=True)
            st.selectbox(
                "Pick The Game",
                options=selections,
                on_change=update_match_label,
                index=None,
                placeholder="Choose a match",
                key="selected_option",
                disabled=False,
            )

            create_input_form_match_details()
        st.button("Log out", on_click=st.logout)
    else:
        st.error("You are not authorized to access this page", icon="‼️")
        # st.button("Log out", on_click=st.logout)
else:
    if not st.experimental_user.is_logged_in or "name" not in st.experimental_user:
        login_screen()
    else:
        st.session_state.user_name = st.experimental_user.name
        st.subheader("Admin Page")
        st.session_state.next_matches = json.loads(get_next_match_from_json())
        if len(st.session_state.next_matches) != 0:
            st.session_state.current_match_dictionary = st.session_state.next_matches[0]
        else:
            st.session_state.current_match_dictionary = {}

        if "home_team" not in st.session_state:
            st.session_state.home_team = "HomeTeam"
        if "away_team" not in st.session_state:
            st.session_state.away_team = "AwayTeam"
        if "match_number_selected" not in st.session_state:
            st.session_state.match_number_selected = 0

        if st.session_state.user_name == "Gururaj Rao":
            with st.container():
                st.subheader("Select team and update stats")
                selections = []
                for matches in st.session_state.json_match:
                    if matches.get("MatchCompletionStatus") == "Completed" or (
                        matches.get("MatchNumber")
                        == (
                            st.session_state.current_match_dictionary.get("MatchNumber")
                            - 1
                        )
                        or matches.get("MatchNumber")
                        == (
                            st.session_state.current_match_dictionary.get("MatchNumber")
                            - 2
                        )
                    ):
                        match_number = (
                            str(matches.get("MatchNumber"))
                            if matches.get("MatchNumber") > 9
                            else f"0{matches.get("MatchNumber")}"
                        )
                        if matches.get("MatchNumber") == (
                            st.session_state.current_match_dictionary.get("MatchNumber")
                            - 1
                        ) or matches.get("MatchNumber") == (
                            st.session_state.current_match_dictionary.get("MatchNumber")
                            - 2
                        ):
                            if matches.get("MatchCompletionStatus") == "Completed":
                                selections.append(
                                    f"{match_number} - {matches.get("HomeTeam")} vs {matches.get("AwayTeam")} ({matches.get("MatchCompletionStatus")})"
                                )
                            else:
                                selections.append(
                                    f"{match_number} - {matches.get("HomeTeam")} vs {matches.get("AwayTeam")} (In Progress)"
                                )
                        else:
                            selections.append(
                                f"{match_number} - {matches.get("HomeTeam")} vs {matches.get("AwayTeam")} ({matches.get("MatchCompletionStatus")})"
                            )
                selections.sort(reverse=True)
                st.selectbox(
                    "Pick The Game",
                    options=selections,
                    on_change=update_match_label,
                    index=None,
                    placeholder="Choose a match",
                    key="selected_option",
                    disabled=False,
                )

                create_input_form_match_details()
            st.button("Log out", on_click=st.logout)
        else:
            st.error("You are not authorized to access this page", icon="‼️")
