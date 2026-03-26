import streamlit as st
st.set_page_config(page_title="CodeStore AI", layout="centered")

import requests
import base64
from PyPDF2 import PdfReader
import sqlite3
import hashlib

OLLAMA_URL = "http://localhost:11434/api/generate"

# ==============================
# DATABASE
# ==============================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

# DEFAULT USER
default_user = "admin"
default_pass = hashlib.sha256("admin123".encode()).hexdigest()

c.execute("SELECT * FROM users WHERE username=?", (default_user,))
if not c.fetchone():
    c.execute("INSERT INTO users VALUES (?, ?)", (default_user, default_pass))
    conn.commit()

# ==============================
# AUTH FUNCTIONS
# ==============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup(username, password):
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except:
        return False

def login(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    return c.fetchone()

# ==============================
# SESSION STATE
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# ==============================
# LOGIN UI
# ==============================
if not st.session_state.logged_in:

    try:
        with open("codestorelogo.webp", "rb") as f:
            logo = base64.b64encode(f.read()).decode()
    except:
        logo = ""

    st.markdown(f"""
    <div style="text-align:center;">
        <img src="data:image/webp;base64,{logo}" width="140">
        <h1>🔐 CodeStore AI Login</h1>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid credentials ❌")

    with tab2:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Create Account"):
            if signup(new_user, new_pass):
                st.session_state.logged_in = True
                st.session_state.user = new_user
                st.success("Account created ✅ Logging you in...")
                st.rerun()
            else:
                st.error("User already exists ❌")

    st.info("👉 Default Login: admin / admin123")
    st.stop()

# ==============================
# HELPERS
# ==============================
def extract_pdf_text(file):
    file.seek(0)
    reader = PdfReader(file)
    return "".join(page.extract_text() or "" for page in reader.pages)[:3000]

def extract_code_text(file):
    file.seek(0)
    return file.read().decode("utf-8", errors="ignore")[:3000]

def is_greeting(text):
    return any(x in text.lower() for x in ["hi", "hello", "hey"])

def ollama_chat_stream(prompt):
    try:
        res = requests.post(
            OLLAMA_URL,
            json={"model": "deepseek-coder:latest", "prompt": prompt, "stream": False}
        )
        return res.json().get("response", "No response")
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:

    try:
        with open("codestorelogo.webp", "rb") as f:
            logo = base64.b64encode(f.read()).decode()
    except:
        logo = ""

    # LOGO + TITLE (COMPACT)
    st.markdown(f"""
    <div style="text-align:center;">
        <img src="data:image/webp;base64,{logo}" width="100">
        <h3 style="color:#38bdf8; margin-bottom:2px;">CodeStore AI</h3>
        <p style="color:#94a3b8;font-size:11px;">Internal AI System</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # BUTTONS
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.uploaded_file = None
        st.rerun()

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.uploaded_file = None
        st.rerun()

    st.markdown("### 📂 Upload File")

    uploaded_file = st.file_uploader(
        "Upload File",
        type=["png","jpg","jpeg","pdf","py","txt","js","cpp"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file

    if st.session_state.get("uploaded_file"):
        st.success(f"{st.session_state.uploaded_file.name}")

    # SMALL SPACE ONLY
    st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)

    st.markdown("---")

    # USER + LOGOUT (VISIBLE ALWAYS)
    st.markdown(f"👤 **{st.session_state.user}**")

    if st.button("🚪 Logout", key="logout_sidebar"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
# ==============================
# HEADER
# ==============================
st.title("CodeStore AI Assistant")

# ==============================
# CHAT HISTORY
# ==============================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==============================
# FILE DISPLAY
# ==============================
if st.session_state.get("uploaded_file"):
    st.info(f"📎 {st.session_state.uploaded_file.name}")

    if st.button("❌ Remove File"):
        st.session_state.uploaded_file = None
        st.rerun()

# ==============================
# MIC BUTTON
# ==============================
st.markdown("""
<script>
(function(){
const doc = window.parent.document;
function inject(){
 const w = doc.querySelector('[data-testid="stChatInput"] > div');
 if(!w || w.querySelector('.mic-btn')) return;

 const mic = doc.createElement('button');
 mic.innerHTML='🎤';
 mic.className='mic-btn';
 mic.style.position='absolute';
 mic.style.right='50px';
 mic.style.top='50%';
 mic.style.transform='translateY(-50%)';

 mic.onclick=()=>{
   const SR = window.parent.SpeechRecognition||window.parent.webkitSpeechRecognition;
   if(!SR){alert("Use Chrome"); return;}

   const r=new SR();
   r.onresult=e=>{
     const ta=doc.querySelector('textarea');
     ta.value=e.results[0][0].transcript;
     ta.dispatchEvent(new Event('input',{bubbles:true}));
   };
   r.start();
 };

 w.appendChild(mic);
}
setInterval(inject,500);
})();
</script>
""", unsafe_allow_html=True)

# ==============================
# CHAT INPUT
# ==============================
prompt = st.chat_input("Ask coding questions...")

if prompt:

    display = prompt
    if st.session_state.get("uploaded_file"):
        display = f"📎 {st.session_state.uploaded_file.name}\n\n{prompt}"

    st.session_state.messages.append({"role":"user","content":display})

    with st.chat_message("user"):
        st.markdown(display)

    file_context = ""
    if st.session_state.get("uploaded_file"):
        f = st.session_state.uploaded_file
        file_context = extract_pdf_text(f) if f.name.endswith(".pdf") else extract_code_text(f)

    if is_greeting(prompt):
        response = "Hello 👋 I'm CodeStore AI Assistant."
    else:
        response = ollama_chat_stream(f"{prompt}\n\n{file_context}")

    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({"role":"assistant","content":response})