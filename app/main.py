import streamlit as st
import json
import os 

# st.markdown(
#     """
#     <style>
#         div[data-testid="column"]:nth-of-type(1)
#         {
#             border:1px solid red;
#         } 

#         div[data-testid="column"]:nth-of-type(2)
#         {
#             border:1px solid blue;
#             text-align: end;
#         } 
#     </style>
#     """,unsafe_allow_html=True
# )

def login_screen():
    st.header("Welcome to Predictor App for IPL 2025")
    st.subheader("Please log in.")
    st.button("Log in with Google", on_click=st.login)

def body_rendering():
    ## Now lets add match details.

    match_details = json.loads(open(os.path.join(os.path.dirname(__file__),"match_details.json"),"r").read())


    ## Add headers 

    left, middle , right = st.columns(3, border=True,vertical_alignment="center")

    left.image(match_details.get("matches").get("home_image"))
    left.text(match_details.get("matches").get("home"))

    right.image(match_details.get("matches").get("away_image"))
    right.text(match_details.get("matches").get("away"))

    middle.text("{} On {} at {}".format(match_details.get("matches").get("venue"),match_details.get("matches").get("date"),match_details.get("matches").get("start_time")))
    middle.image("https://www.creativefabrica.com/wp-content/uploads/2021/11/09/Versus-Vs-Vector-Transparent-Background-Graphics-19913250-2-580x386.png")

    


    ## Add Questions 

    with st.container():
        st.radio(label="Who Will win the game? (5 pts)",options=[match_details.get("matches").get("home"),match_details.get("matches").get("away")],key="winner")
        st.radio(label="Which team will score most sixes? (10 pts)",options=[match_details.get("matches").get("home"),match_details.get("matches").get("away")],key="sixes")
        st.radio(label="Which team will score most fours? (10 pts)",options=[match_details.get("matches").get("home"),match_details.get("matches").get("away")],key="fours")
        st.radio(label="Which team will take most wickets? (10 pts)",options=[match_details.get("matches").get("home"),match_details.get("matches").get("away")],key="wickets")
        st.radio(label="Will there be a century in this game? (5 pts)",options=["Yes", "No"],key="century")
        st.text_input(label="What will be the score posted by {}?".format(match_details.get("matches").get("home")),key="score_home")
        st.text_input(label="What will be the score posted by {}?".format(match_details.get("matches").get("away")),key="score_away")






    st.button("Log out", on_click=st.logout)   

if not st.experimental_user.is_logged_in:
    login_screen()
else:
    st.header(f"Welcome, {st.experimental_user.name}!")
    body_rendering()
    


