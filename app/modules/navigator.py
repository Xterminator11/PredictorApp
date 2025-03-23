import streamlit as st


def Navbar():
    # st.set_option("client.showSidebarNavigation", False)
    with st.sidebar:
        st.page_link("main.py", label="Predictor Home Page", icon="🔥")
        st.page_link("pages/stats.py", label="Statistics", icon="🛡️")
        st.page_link("pages/leaderboard.py", label="Leader Board", icon="🐐")
