import streamlit as st
import requests
from datetime import datetime
import time

API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="EasyAI - Document Intelligence",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'show_upload' not in st.session_state:
    st.session_state.show_upload = False
if 'uploaded_documents' not in st.session_state:
    st.session_state.uploaded_documents = []
if 'current_document_context' not in st.session_state:
    st.session_state.current_document_context = None
if 'notification' not in st.session_state:
    st.session_state.notification = None
if 'is_thinking' not in st.session_state:
    st.session_state.is_thinking = False

# Modern EasyAI CSS with Brain Animation
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    div[data-testid="stToolbar"] {display: none;}
    div[data-testid="stDecoration"] {display: none;}
    div[data-testid="stStatusWidget"] {display: none;}
    
    :root {
        --bg-primary: #0f0f0f;
        --bg-secondary: #1a1a1a;
        --bg-tertiary: #252525;
        --bg-hover: #2f2f2f;
        --text-primary: #f5f5f5;
        --text-secondary: #a0a0a0;
        --text-muted: #6b6b6b;
        --accent-primary: #e85d4c;
        --accent-secondary: #ff6b5b;
        --accent-glow: rgba(232, 93, 76, 0.3);
        --border-color: #2a2a2a;
        --success: #4ade80;
        --error: #f87171;
    }
    
    .main {
        background-color: var(--bg-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main .block-container {
        padding: 1rem 1rem 6rem 1rem;
        max-width: 52rem;
    }
    
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--bg-tertiary); border-radius: 3px; }
    
    h1, h2, h3, h4, h5, h6 { color: var(--text-primary) !important; font-weight: 600 !important; }
    p, span, label, div { color: var(--text-primary); }
    
    /* BRAIN THINKING ANIMATION */
    .brain-thinking-box {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 14px;
        background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
        padding: 14px 22px;
        border-radius: 50px;
        border: 1px solid var(--border-color);
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    
    .brain-anim-wrapper {
        position: relative;
        width: 44px;
        height: 44px;
    }
    
    .brain-glow-effect {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 65px;
        height: 65px;
        background: var(--accent-glow);
        border-radius: 50%;
        filter: blur(18px);
        animation: brainGlow 2s ease-in-out infinite;
    }
    
    @keyframes brainGlow {
        0%, 100% { opacity: 0.4; transform: translate(-50%, -50%) scale(0.8); }
        50% { opacity: 0.9; transform: translate(-50%, -50%) scale(1.2); }
    }
    
    .brain-icon-container {
        position: relative;
        width: 44px;
        height: 44px;
        z-index: 2;
    }
    
    .brain-outline {
        position: absolute;
        top: 0;
        left: 0;
        width: 44px;
        height: 44px;
        font-size: 44px;
        line-height: 1;
        z-index: 3;
        filter: grayscale(100%) brightness(0.5);
    }
    
    .brain-fill-mask {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 44px;
        height: 0%;
        overflow: hidden;
        animation: liquidFill 2.2s ease-in-out infinite;
        z-index: 2;
    }
    
    .brain-fill-icon {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 44px;
        height: 44px;
        font-size: 44px;
        line-height: 1;
        filter: hue-rotate(-10deg) saturate(1.5);
    }
    
    @keyframes liquidFill {
        0% { height: 0%; }
        50% { height: 100%; }
        100% { height: 0%; }
    }
    
    .thinking-info {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    
    .thinking-title {
        color: var(--text-primary);
        font-size: 14px;
        font-weight: 600;
    }
    
    .thinking-dots {
        display: flex;
        gap: 5px;
    }
    
    .thinking-dot {
        width: 7px;
        height: 7px;
        background: var(--accent-primary);
        border-radius: 50%;
        animation: dotBounce 1.4s ease-in-out infinite;
    }
    
    .thinking-dot:nth-child(2) { animation-delay: 0.15s; }
    .thinking-dot:nth-child(3) { animation-delay: 0.3s; }
    
    @keyframes dotBounce {
        0%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
    }
    
    /* NOTIFICATION */
    .notification {
        position: fixed;
        top: 90px;
        right: 20px;
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 500;
        z-index: 9998;
        animation: notifSlide 0.3s ease-out, notifFade 0.3s ease-out 2.7s forwards;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        max-width: 320px;
    }
    
    .notification.success {
        background: linear-gradient(135deg, #065f46, #047857);
        border: 1px solid #10b981;
        color: #ecfdf5;
    }
    
    .notification.error {
        background: linear-gradient(135deg, #7f1d1d, #991b1b);
        border: 1px solid #f87171;
        color: #fef2f2;
    }
    
    .notification.info {
        background: linear-gradient(135deg, #1e3a5f, #1e40af);
        border: 1px solid #60a5fa;
        color: #eff6ff;
    }
    
    @keyframes notifSlide {
        from { transform: translateX(100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes notifFade {
        from { opacity: 1; }
        to { opacity: 0; visibility: hidden; }
    }
    
    /* AUTH LOADING */
    .auth-loading-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 35px;
        gap: 18px;
    }
    
    .auth-spin {
        width: 55px;
        height: 55px;
        border: 4px solid var(--bg-tertiary);
        border-top-color: var(--accent-primary);
        border-radius: 50%;
        animation: authSpin 0.8s linear infinite;
    }
    
    @keyframes authSpin {
        to { transform: rotate(360deg); }
    }
    
    .auth-text { color: var(--text-primary); font-size: 16px; font-weight: 600; }
    .auth-subtext { color: var(--text-muted); font-size: 13px; }
    
    /* HEADER */
    .logo-box {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .logo-icon { font-size: 30px; }
    
    .logo-text {
        font-size: 24px;
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .user-badge {
        background: var(--bg-tertiary);
        padding: 8px 14px;
        border-radius: 20px;
        font-size: 13px;
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
    }
    
    /* DOCUMENTS PANEL */
    .docs-panel {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 20px;
    }
    
    .docs-title {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 12px;
    }
    
    /* WELCOME */
    .welcome-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 45vh;
        text-align: center;
        padding: 40px 20px;
    }
    
    .welcome-icon {
        font-size: 80px;
        margin-bottom: 24px;
        animation: floatBrain 3s ease-in-out infinite;
    }
    
    @keyframes floatBrain {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-18px); }
    }
    
    .welcome-title {
        font-size: 34px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 14px;
    }
    
    .welcome-subtitle {
        font-size: 15px;
        color: var(--text-secondary);
        max-width: 440px;
        line-height: 1.7;
    }
    
    /* CHAT */
    .stChatMessage { background: transparent !important; padding: 14px 0 !important; }
    
    [data-testid="stChatMessageContent"] {
        background: transparent !important;
        color: var(--text-primary) !important;
        font-size: 15px !important;
        line-height: 1.7 !important;
    }
    
    [data-testid="stChatMessageAvatarUser"] ~ div [data-testid="stChatMessageContent"] {
        background: var(--bg-tertiary) !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 14px 18px !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .stChatInput > div {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 24px !important;
        padding: 4px 8px !important;
    }
    
    .stChatInput > div:focus-within {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }
    
    .stChatInput textarea {
        background: transparent !important;
        border: none !important;
        color: var(--text-primary) !important;
        font-size: 15px !important;
        padding: 12px 16px !important;
    }
    
    .stChatInput textarea::placeholder { color: var(--text-muted) !important; }
    
    /* BUTTONS */
    .stButton > button {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: var(--bg-hover) !important;
        border-color: var(--accent-primary) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* FILE UPLOADER */
    .stFileUploader > div {
        background: var(--bg-secondary) !important;
        border: 2px dashed var(--border-color) !important;
        border-radius: 16px !important;
        padding: 24px !important;
    }
    
    .stFileUploader > div:hover {
        border-color: var(--accent-primary) !important;
    }
    
    .stFileUploader label { color: var(--text-primary) !important; }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] { background: transparent; gap: 8px; justify-content: center; }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--bg-tertiary);
        border-radius: 10px;
        padding: 12px 32px;
        color: var(--text-secondary);
        font-weight: 500;
        border: 1px solid var(--border-color);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
        color: white !important;
        border: none !important;
    }
    
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
    
    /* INPUTS */
    .stTextInput > div > div {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
    }
    
    .stTextInput > div > div:focus-within {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }
    
    .stTextInput input { color: var(--text-primary) !important; padding: 12px 16px !important; }
    .stTextInput label { color: var(--text-secondary) !important; font-size: 13px !important; font-weight: 500 !important; }
    
    /* EXPANDER */
    .streamlit-expanderHeader {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }
    
    .streamlit-expanderContent {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }
    
    /* LOGIN */
    .login-header { text-align: center; margin-bottom: 36px; padding-top: 50px; }
    .login-logo { font-size: 64px; margin-bottom: 16px; }
    .login-title {
        font-size: 36px;
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .login-subtitle { font-size: 15px; color: var(--text-secondary); }
    
    /* PROCESSING */
    .process-box {
        text-align: center;
        padding: 45px;
    }
    
    .process-icon {
        font-size: 64px;
        animation: processPulse 1.5s ease-in-out infinite;
    }
    
    @keyframes processPulse {
        0%, 100% { transform: scale(1); opacity: 0.7; }
        50% { transform: scale(1.15); opacity: 1; }
    }
    
    .process-text { color: var(--accent-primary); font-size: 18px; font-weight: 600; margin-top: 18px; }
    .process-subtext { color: var(--text-muted); font-size: 14px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)


def show_brain_thinking():
    st.markdown("""
        <div class="brain-thinking-box">
            <div class="brain-anim-wrapper">
                <div class="brain-glow-effect"></div>
                <div class="brain-icon-container">
                    <div class="brain-outline">🧠</div>
                    <div class="brain-fill-mask">
                        <div class="brain-fill-icon">🧠</div>
                    </div>
                </div>
            </div>
            <div class="thinking-info">
                <span class="thinking-title">EasyAI is thinking</span>
                <div class="thinking-dots">
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def show_notification(message: str, ntype: str = "info"):
    icon = {"success": "✓", "error": "✕", "info": "ℹ"}.get(ntype, "ℹ")
    st.markdown(f'<div class="notification {ntype}"><span>{icon}</span><span>{message}</span></div>', unsafe_allow_html=True)


def login_user(username: str, password: str):
    try:
        resp = requests.post(f"{API_BASE_URL}/auth/login", json={"username": username, "password": password}, timeout=10)
        if resp.status_code == 200:
            st.session_state.token = resp.json().get("access_token")
            st.session_state.username = username
            return True, f"Welcome back, {username}!"
        return False, "Invalid username or password."
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server."
    except Exception as e:
        return False, str(e)


def register_user(email: str, password: str, username: str):
    try:
        resp = requests.post(f"{API_BASE_URL}/auth/register", json={"email": email, "username": username, "password": password}, timeout=10)
        if resp.status_code == 201:
            return True, "Account created! Please sign in."
        return False, resp.json().get("detail", "Registration failed")
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server."
    except Exception as e:
        return False, str(e)


def upload_document(file):
    try:
        files = {'file': (file.name, file.getvalue(), file.type or 'application/octet-stream')}
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        
        resp = requests.post(f"{API_BASE_URL}/documents/upload", files=files, headers=headers, timeout=30)
        if resp.status_code != 201:
            return False, {"error": f"Upload failed: {resp.status_code}"}
        
        doc_id = resp.json().get('id')
        
        analyze = requests.post(f"{API_BASE_URL}/documents/{doc_id}/analyze", headers=headers, timeout=60)
        
        if analyze.status_code == 200:
            data = analyze.json()
            return True, {
                "id": doc_id,
                "filename": file.name,
                "summary": data.get('ai_summary', 'Document analyzed.'),
                "insights": data.get('ai_insights', ''),
                "topics": data.get('key_topics', ''),
                "extracted_text": data.get('extracted_text', '')
            }
        return True, {"id": doc_id, "filename": file.name, "summary": "Uploaded but analysis failed.", "insights": "", "topics": "", "extracted_text": ""}
    except Exception as e:
        return False, {"error": str(e)}


def delete_document(doc_id: int):
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        return requests.delete(f"{API_BASE_URL}/documents/{doc_id}", headers=headers, timeout=10).status_code == 200
    except:
        return False


def send_ai_message(message: str, doc_context=None):
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        
        full_msg = message
        if doc_context:
            full_msg = f"""[Document: {doc_context.get('filename')}]
Summary: {doc_context.get('summary', '')}
Content: {doc_context.get('extracted_text', '')[:3000]}

Question: {message}

Answer based on the document."""
        
        resp = requests.post(f"{API_BASE_URL}/ai/chat", headers=headers, json={"message": full_msg}, timeout=60)
        
        if resp.status_code == 200:
            return resp.json().get("response", "No response.")
        return f"Error: {resp.status_code}"
    except Exception as e:
        return f"Error: {e}"


def render_login_page():
    st.markdown("""
        <div class="login-header">
            <div class="login-logo">🧠</div>
            <div class="login-title">EasyAI</div>
            <div class="login-subtitle">Intelligent Document Analysis</div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.notification:
        show_notification(*st.session_state.notification)
        st.session_state.notification = None
    
    tab1, tab2 = st.tabs(["Sign In", "Create Account"])
    
    with tab1:
        with st.form("login"):
            user = st.text_input("Username", placeholder="Enter username")
            pwd = st.text_input("Password", type="password", placeholder="Enter password")
            
            if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                if user and pwd:
                    ph = st.empty()
                    ph.markdown('<div class="auth-loading-box"><div class="auth-spin"></div><div class="auth-text">Authorizing...</div><div class="auth-subtext">Verifying credentials</div></div>', unsafe_allow_html=True)
                    time.sleep(0.8)
                    ok, msg = login_user(user, pwd)
                    ph.empty()
                    st.session_state.notification = (msg, "success" if ok else "error")
                    st.rerun()
                else:
                    st.session_state.notification = ("Fill all fields.", "error")
                    st.rerun()
    
    with tab2:
        with st.form("register"):
            new_user = st.text_input("Username", placeholder="Choose username", key="ru")
            new_email = st.text_input("Email", placeholder="your@email.com", key="re")
            new_pwd = st.text_input("Password", type="password", placeholder="Min 6 chars", key="rp")
            conf_pwd = st.text_input("Confirm", type="password", placeholder="Repeat", key="rc")
            
            if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
                if not all([new_user, new_email, new_pwd, conf_pwd]):
                    st.session_state.notification = ("Fill all fields.", "error")
                elif new_pwd != conf_pwd:
                    st.session_state.notification = ("Passwords don't match.", "error")
                elif len(new_pwd) < 6:
                    st.session_state.notification = ("Password too short.", "error")
                else:
                    ph = st.empty()
                    ph.markdown('<div class="auth-loading-box"><div class="auth-spin"></div><div class="auth-text">Creating Account...</div><div class="auth-subtext">Setting up profile</div></div>', unsafe_allow_html=True)
                    time.sleep(1)
                    ok, msg = register_user(new_email, new_pwd, new_user)
                    ph.empty()
                    st.session_state.notification = (msg, "success" if ok else "error")
                st.rerun()


def render_documents_panel():
    docs = st.session_state.uploaded_documents
    if not docs:
        return
    
    st.markdown('<div class="docs-panel"><div class="docs-title">📎 Your Documents</div></div>', unsafe_allow_html=True)
    
    cols = st.columns(min(len(docs), 3))
    for i, doc in enumerate(docs):
        with cols[i % 3]:
            active = st.session_state.current_document_context and st.session_state.current_document_context.get('id') == doc.get('id')
            name = doc['filename'][:15] + "..." if len(doc['filename']) > 15 else doc['filename']
            
            c1, c2 = st.columns([4, 1])
            with c1:
                if st.button(f"{'✓ ' if active else ''}📄 {name}", key=f"d{doc['id']}", use_container_width=True):
                    st.session_state.current_document_context = None if active else doc
                    st.rerun()
            with c2:
                if st.button("✕", key=f"x{doc['id']}"):
                    if delete_document(doc['id']):
                        st.session_state.uploaded_documents = [d for d in docs if d['id'] != doc['id']]
                        if active:
                            st.session_state.current_document_context = None
                        st.session_state.notification = ("Removed.", "success")
                        st.rerun()
    
    if st.session_state.current_document_context:
        st.info(f"🎯 **Context:** {st.session_state.current_document_context['filename']}")


def render_chat():
    if st.session_state.is_thinking:
        show_brain_thinking()
    
    c1, c2, c3 = st.columns([6, 2, 1])
    with c1:
        st.markdown('<div class="logo-box"><span class="logo-icon">🧠</span><span class="logo-text">EasyAI</span></div>', unsafe_allow_html=True)
    with c2:
        if st.session_state.username:
            st.markdown(f'<span class="user-badge">👤 {st.session_state.username}</span>', unsafe_allow_html=True)
    with c3:
        if st.button("Exit"):
            for k in ['token', 'username', 'chat_messages', 'uploaded_documents', 'current_document_context']:
                st.session_state[k] = None if k in ['token', 'username', 'current_document_context'] else []
            st.session_state.notification = ("Logged out.", "info")
            st.rerun()
    
    st.markdown("<hr style='border-color:#2a2a2a;margin:8px 0 16px'>", unsafe_allow_html=True)
    
    if st.session_state.notification:
        show_notification(*st.session_state.notification)
        st.session_state.notification = None
    
    render_documents_panel()
    
    with st.expander("📎 Upload Document", expanded=st.session_state.show_upload):
        file = st.file_uploader("Drop PDF/TXT", type=['pdf', 'txt'], label_visibility="collapsed")
        
        if file:
            st.session_state.is_thinking = True
            ph = st.empty()
            ph.markdown('<div class="process-box"><div class="process-icon">🧠</div><div class="process-text">Analyzing document...</div><div class="process-subtext">EasyAI is reading your file</div></div>', unsafe_allow_html=True)
            
            ok, res = upload_document(file)
            ph.empty()
            st.session_state.is_thinking = False
            
            if ok:
                st.session_state.uploaded_documents.append(res)
                st.session_state.current_document_context = res
                
                msg = f"""📄 **Analyzed: {res['filename']}**

---
**📝 Summary:**
{res.get('summary', 'N/A')}

{f"**🏷️ Topics:** {res.get('topics')}" if res.get('topics') else ''}

---
*Ready to answer questions about this document!*"""
                
                st.session_state.chat_messages.append({"role": "assistant", "content": msg})
                st.session_state.notification = (f"'{res['filename']}' analyzed!", "success")
                st.session_state.show_upload = False
            else:
                st.session_state.notification = (res.get('error', 'Failed'), "error")
            st.rerun()
    
    if not st.session_state.chat_messages:
        st.markdown("""
            <div class="welcome-box">
                <div class="welcome-icon">🧠</div>
                <div class="welcome-title">How can I help you?</div>
                <div class="welcome-subtitle">Upload a document for instant analysis, or just chat with me.</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📄 Upload", use_container_width=True):
                st.session_state.show_upload = True
                st.rerun()
        with c2:
            if st.button("💬 Chat", use_container_width=True):
                st.session_state.chat_messages = [
                    {"role": "user", "content": "Hello!"},
                    {"role": "assistant", "content": "Hello! 👋 I'm EasyAI. Upload a document or ask me anything!"}
                ]
                st.rerun()
        with c3:
            if st.button("❓ Help", use_container_width=True):
                st.session_state.chat_messages = [
                    {"role": "user", "content": "What can you do?"},
                    {"role": "assistant", "content": "I'm **EasyAI**:\n\n📄 **Analyze** PDFs & TXT files\n💬 **Answer** questions about documents\n🎯 **Summarize** & extract insights\n\nUpload a file or ask me anything!"}
                ]
                st.rerun()
    else:
        for m in st.session_state.chat_messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
    
    if prompt := st.chat_input("Ask EasyAI..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        st.session_state.is_thinking = True
        
        with st.chat_message("assistant"):
            ph = st.empty()
            ph.markdown('<span style="color:#a0a0a0">🧠 Thinking...</span>', unsafe_allow_html=True)
            
            resp = send_ai_message(prompt, st.session_state.current_document_context)
            
            ph.empty()
            st.session_state.is_thinking = False
            
            if st.session_state.current_document_context:
                resp = f"*📄 Based on: {st.session_state.current_document_context['filename']}*\n\n{resp}"
            
            st.markdown(resp)
        
        st.session_state.chat_messages.append({"role": "assistant", "content": resp})
        st.rerun()


def main():
    if not st.session_state.token:
        render_login_page()
    else:
        render_chat()


if __name__ == "__main__":
    main()