import streamlit as st
import threading
import os
import sys

# 1. FIX THE PATHS (The "Nuclear" fix we discussed)
# This allows your scripts to find 'online' and 'offline' folders
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Import your existing bot logic
# Assuming your main bot logic is in online/src/bot.py
from online.src.bot import main as run_telegram_bot

# 2. THE UI (Minimalistic)
st.set_page_config(page_title="Bot Server", page_icon="🤖")
st.title("Backend Server is Running")
st.info("This page exists to keep the Telegram bot alive on Streamlit Cloud.")

# 3. THE THREADING LOGIC
# We use a global check to make sure we don't start the bot twice
if "bot_started" not in st.session_state:
    st.session_state.bot_started = True
    
    # We run the bot in a background thread
    # This prevents the 'Signal' error and the '503 Timeout' error
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    st.success("Telegram Bot Thread started!")

st.write("Check your Telegram app to interact with the bot.")