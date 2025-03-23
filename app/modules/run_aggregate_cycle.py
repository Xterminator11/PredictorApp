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

                point.append(str(percentage_deviation))
            else:
                if user_selection == correct_selection:
                    point.append(str(question.get("points")))
                else:
                    point.append(str(0))

        df_player = pd.DataFrame(
            {
                "Points": point,
            }
        )

    return json.loads(
        df_player.agg({"Points": ["sum"]}).fillna(0).to_json(orient="records")
    )[0]


s3 = boto3.resource("s3")
s3_client = boto3.client("s3")
my_bucket = s3.Bucket("predictor-app-dallas-ipl2025")
user_list = []

for my_bucket_object in my_bucket.objects.all():
    if str(my_bucket_object.key).startswith("aggregates/"):
        continue
    else:
        user_list.append(my_bucket_object.key.split("/")[0])

final_data_to_save_in_s3 = []

for matches in json_match:
    if matches.get("ResultsPublished") is True:
        for users in list(set(user_list)):
            data_point = update_statistics(matches, users)
            final_data_to_save_in_s3.append(
                {
                    "MatchNumber": f"{matches.get('MatchNumber')} - {matches.get('HomeTeam')} vs {matches.get('AwayTeam')}",
                    "UserName": users,
                    "AggregatePoints": float(data_point.get("Points")),
                }
            )
    else:
        continue

print(json.dumps(final_data_to_save_in_s3, indent=3))

s3object = "aggregates/transactional.txt"
s3 = boto3.resource("s3")
s3object = s3.Object("predictor-app-dallas-ipl2025", s3object)
s3object.put(Body=(bytes(json.dumps(final_data_to_save_in_s3).encode("UTF-8"))))


aggregate_df = pd.DataFrame(final_data_to_save_in_s3)

sum_values = aggregate_df.groupby("UserName")
# sum_values = grouped["AggregatePoints"].sum()
print(sum_values)

s3object = "aggregates/leaderboard.txt"
s3 = boto3.resource("s3")
s3object = s3.Object("predictor-app-dallas-ipl2025", s3object)
s3object.put(Body=(bytes(json.dumps(json.loads(sum_values.to_json())).encode("UTF-8"))))
