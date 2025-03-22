from datetime import datetime, timedelta
import datetime as dt
from pytz import timezone
import pandas as pd
import os


def get_current_date_time():
    current_time = datetime.now(dt.timezone.utc)
    return current_time


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
    return data_frame.to_json(orient="records", date_format="iso", date_unit="s")


if __name__ == "__main__":

    next_matches = get_next_match_from_json()
    if len(next_matches) == 0:
        print("No Matches to be played")
    else:
        print(next_matches)
