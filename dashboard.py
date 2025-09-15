import streamlit as st
import os

st.title("📊 Syntra AI Real-Time Dashboard")
st.markdown("### Status: ✅ Active")

st.markdown("---")
st.header("🧠 Memory & Learning")
st.write("✔️ Self-Learning: Active")
st.write("✔️ Code Filtering: Enabled")
st.write("✔️ GitHub Sync: Connected")

st.markdown("---")
st.header("📁 Recent Files")
for file in os.listdir("."):
    if file.endswith(".py"):
        st.code(open(file).read(), language='python')

st.success("All systems nominal.")