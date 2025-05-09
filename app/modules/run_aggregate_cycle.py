import boto3
import botocore
import json
import pandas as pd
import os

json_metadata = json.loads(
    open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "metadata.json"),
        "r",
        encoding="utf-8",
    ).read()
)

json_match = json.loads(
    open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "match_details.json"),
        "r",
        encoding="utf-8",
    ).read()
)


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


def get_booster_information(match_status, user_name):

    user_name = str(user_name).replace(" ", "").lower()
    match_id = match_status.get("MatchNumber")

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


def load_match_result_published() -> list:

    s3object = "aggregates/transactional.txt"
    s3 = boto3.client("s3")
    try:
        data = s3.get_object(Bucket="predictor-app-dallas-ipl2025", Key=s3object)
        contents = json.loads(data["Body"].read().decode("utf-8"))
        return contents

    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return []
        else:
            return []


def is_match_completed(match_id, user_name, contents):
    data_found = False
    for records in contents:
        if (
            records.get("MatchNumber") == match_id
            and records.get("UserName") == user_name
        ):
            data_found = True
            break
    return data_found


def get_booster_data(user_name, match_id):

    booster_data_local = {}
    s3object = f"{user_name}/{get_booster_data_file(match_id)}"
    s3 = boto3.client("s3")
    try:
        data = s3.get_object(Bucket="predictor-app-dallas-ipl2025", Key=s3object)
        contents = json.loads(data["Body"].read().decode("utf-8"))
        booster_data_local[user_name] = contents

    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            booster_data_local[user_name] = {}
        else:
            booster_data_local[user_name] = {}

    return booster_data_local


def get_individual_data_from_backend(match_id, user_name):

    ## Add headers
    # user_name = str(st.session_state.user_name).replace(" ", "").lower()

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


def update_statistics(match_status, users):

    if not match_status.get("ResultsPublished"):
        df_player = pd.DataFrame(
            {
                "Points": ["Not Available"],
            }
        )

    else:

        booster_1, booster_2, booster_3, contents_booster = get_booster_information(
            match_status, users
        )
        booster_value = 1

        for booster in contents_booster.keys():
            if contents_booster.get(booster) == int(match_status.get("MatchNumber")):
                booster_details = (
                    "5x"
                    if booster == "booster_1"
                    else "3x" if booster == "booster_2" else "2x"
                )
                # st.subheader(f"Booster Selected for this match : {booster_details}")
                booster_value = int(booster_details.replace("x", ""))
        point = []
        for question in json_metadata.get("question_list"):
            correct_selection = match_status.get("PredictionResults").get(
                question.get("q_key")
            )

            match_selection = get_individual_data_from_backend(
                match_status.get("MatchNumber"), users
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
                    * 10,
                    2,
                )

                point.append(float(percentage_deviation * booster_value))
            else:
                if correct_selection == "Tie" and user_selection != "":
                    point.append(float(question.get("points") * booster_value))
                else:
                    if user_selection == correct_selection:
                        point.append(float(question.get("points") * booster_value))
                    else:
                        point.append(float(0))

        # print(point)
        # df_player = pd.DataFrame(
        #     {
        #         "Points": point,
        #     }
        # )

    # return json.loads(
    #     df_player.agg({"Points": sum}).fillna(0).to_json(orient="records")
    # )[0]
    return sum(point)


def get_user_booster(match_id, user):

    booster_user = booster_data.get(user, None)

    if booster_user is None:
        return ""
    else:
        boosters_value = ""
        for boosters in booster_user:
            if booster_user.get(boosters) == match_id:
                boosters_value = boosters
                break
            else:
                continue

        return (
            "5x"
            if boosters_value == "booster_1"
            else (
                "3x"
                if boosters_value == "booster_2"
                else "2x" if boosters_value == "booster_3" else ""
            )
        )


s3 = boto3.resource("s3")
s3_client = boto3.client("s3")
my_bucket = s3.Bucket("predictor-app-dallas-ipl2025")
user_list = []

for my_bucket_object in my_bucket.objects.all():
    if str(my_bucket_object.key).startswith("aggregates/"):
        continue
    else:
        user_list.append(my_bucket_object.key.split("/")[0])


final_data_to_save_in_s3 = load_match_result_published()

for matches in json_match:
    print("Running for match number {}".format(matches.get("MatchNumber")))
    if matches.get("ResultsPublished") is True:
        for users in list(set(user_list)):
            match_number_long = f"{str(matches.get('MatchNumber')).zfill(2)} - {matches.get('HomeTeam')} vs {matches.get('AwayTeam')}"
            if is_match_completed(
                match_id=match_number_long,
                user_name=users,
                contents=final_data_to_save_in_s3,
            ):
                print(f"{match_number_long} already updated for user {users}")
            else:
                global booster_data
                booster_data = get_booster_data(users, matches.get("MatchNumber"))

                data_point = update_statistics(matches, users)
                print(f"{users} : {float(data_point)}")
                final_data_to_save_in_s3.append(
                    {
                        "MatchNumber": match_number_long,
                        "UserName": users,
                        "AggregatePoints": float(data_point),
                        "BoosterIndicator": str(
                            get_user_booster(matches.get("MatchNumber"), users)
                        ),
                    }
                )
    else:
        continue

# print(json.dumps(final_data_to_save_in_s3, indent=3))

s3object = "aggregates/transactional.txt"
s3 = boto3.resource("s3")
s3object = s3.Object("predictor-app-dallas-ipl2025", s3object)
s3object.put(Body=(bytes(json.dumps(final_data_to_save_in_s3).encode("UTF-8"))))


aggregate_df = pd.DataFrame(final_data_to_save_in_s3)
aggregate_df = aggregate_df[["UserName", "AggregatePoints"]]

grouped_counts = (
    aggregate_df.groupby("UserName")
    .sum()
    .sort_values(by="AggregatePoints", ascending=False)
)
grouped_counts = grouped_counts.reset_index(names="UserName")
# sum_values = grouped["AggregatePoints"].sum()
print(grouped_counts)

s3object = "aggregates/leaderboard.txt"
s3 = boto3.resource("s3")
s3object = s3.Object("predictor-app-dallas-ipl2025", s3object)
s3object.put(
    Body=(bytes(json.dumps(json.loads(grouped_counts.to_json())).encode("UTF-8")))
)
