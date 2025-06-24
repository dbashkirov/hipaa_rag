import os
import requests 
import streamlit as st
from dotenv import load_dotenv 

load_dotenv()

API = os.getenv("API_URL", "http://nginx/api/chat")

st.set_page_config(page_title="HIPAA-RAG", page_icon="⚖️")
st.title("⚖️ HIPAA RAG")

if "chat" not in st.session_state: st.session_state.chat = []

for m in st.session_state.chat:
    with st.chat_message(m["role"]): st.markdown(m["text"])

if q := st.chat_input("Спросите о HIPAA…"):
    st.session_state.chat.append({"role": "user", "text": q})
    with st.chat_message("user"): st.markdown(q)

    with st.spinner("Думаю…"):
        r = requests.post(API, json={"question": q}, timeout=120).json()

    st.session_state.chat.append({"role": "assistant", "text": r["answer"]})
    with st.chat_message("assistant"):
        st.markdown(r["answer"])
        st.caption("🔍 Retrieval used" if r["used_retrieval"] else "⚡ No retrieval")
        print(r)
        if r["sources"]:
            with st.expander("Источники"):
                for s in r["sources"]:
                    p = s["metadata"].get("page")
                    st.markdown(f"**стр.{p}** — {s['page_content'][:400]}…")
