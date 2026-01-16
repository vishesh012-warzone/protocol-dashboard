import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PROTOCOL_OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. THE "DEEP SPACE" AESTHETIC (Reference Image Style) ---
st.markdown("""
<style>
    /* IMPORT FONT (Inter/Roboto) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    /* GLOBAL RESET */
    .stApp {
        background-color: #000000; /* Pitch Black */
        /* Subtle radial glow like the globe image */
        background-image: radial-gradient(circle at 50% 10%, #1a1a2e 0%, #000000 50%);
        font-family: 'Inter', sans-serif;
        color: #ffffff;
    }

    /* HIDE STREAMLIT ELEMENTS */
    header {visibility: hidden;}
    .block-container {
        padding-top: 3rem;
        padding-bottom: 5rem;
        max-width: 1200px;
    }

    /* GLASS CONTAINERS (Like the search bar in image) */
    .glass-container {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 30px;
        backdrop-filter: blur(20px);
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    
    /* TYPOGRAPHY */
    h1 {
        font-weight: 300;
        font-size: 48px;
        letter-spacing: -1px;
        background: linear-gradient(180deg, #fff, #888);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
    }
    p.subtitle {
        text-align: center;
        color: #666;
        font-size: 14px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 40px;
    }
    h3, h4, h5 {
        color: #e5e5e5;
        font-weight: 500;
        letter-spacing: -0.5px;
    }

    /* CUSTOM METRIC CARDS */
    .metric-box {
        text-align: center;
        padding: 15px;
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    .metric-box:last-child { border-right: none; }
    .metric-label {
        color: #666;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #fff;
    }
    .metric-sub {
        font-size: 12px;
        color: #888;
    }

    /* INPUT FIELDS (Stealth Mode) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        color: #fff !important;
        padding: 15px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #fff !important;
        background-color: rgba(255,255,255,0.1) !important;
    }

    /* BUTTONS (The "pill" look) */
    .stButton > button {
        width: 100%;
        background-color: #ffffff;
        color: #000000;
        border: none;
        padding: 14px 28px;
        border-radius: 30px; /* Pill shape */
        font-weight: 600;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(255,255,255,0.4);
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #666;
        font-size: 14px;
    }
    .stTabs [aria-selected="true"] {
        color: #fff !important;
        border-bottom: 2px solid #fff;
    }
    
    /* SUCCESS MESSAGE */
    .success-box {
        background: rgba(74, 222, 128, 0.1);
        border: 1px solid rgba(74, 222, 128, 0.3);
        color: #4ade80;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. BACKEND & LOGIC ---
def get_db_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("warrior_db").sheet1
    except Exception as e:
        st.error(f"🔌 Database Disconnected: {e}")
        st.stop()

def load_data():
    try:
        sheet = get_db_connection()
        data = sheet.get_all_values()
        
        if len(data) < 2: return pd.DataFrame()
        
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)
        
        # FILTER: Remove empty rows based on Date
        df = df[df['date'].astype(bool)]
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
            
            # Clean Habits (Convert "TRUE"/"FALSE" -> 1/0)
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            for col in habits:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.upper().replace({'TRUE': '1', 'FALSE': '0', '1': '1', '0': '0'})
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            return df.sort_values('date', ascending=True)
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# --- 4. UI: HEADER ---
st.markdown("<h1>PROTOCOL OS</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>System Status: Optimized • User: Admin</p>", unsafe_allow_html=True)

# --- 5. SUCCESS MESSAGE HANDLER (The Fix) ---
if 'success_msg' in st.session_state:
    st.markdown(f"<div class='success-box'>{st.session_state['success_msg']}</div>", unsafe_allow_html=True)
    # Clear it so it doesn't stay forever (optional, usually good to leave for one view)
    del st.session_state['success_msg']

# --- 6. INTERFACE TABS ---
tab_log, tab_dash = st.tabs(["ENTRY TERMINAL", "ANALYTICS HUB"])

# ==========================================
# TAB 1: THE INPUT TERMINAL
# ==========================================
with tab_log:
    # Use a centered column layout for the form to look like the "Search Bar"
    c_pad_l, c_main, c_pad_r = st.columns([1, 2, 1])
    
    with c_main:
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        
        with st.form("entry_form", clear_on_submit=False):
            # 1. SMART DEFAULT
            last_weight = 94.0
            if not df.empty:
                last_weight = float(df['weight'].iloc[-1])
            
            st.markdown("### NEW LOG")
            
            # 2. INPUT GRID
            c1, c2 = st.columns([1, 1])
            with c1:
                date_in = st.date_input("Date", datetime.today(), label_visibility="collapsed")
            with c2:
                weight_in = st.number_input("Weight", value=last_weight, step=0.1, format="%.1f", label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### DAILY PROTOCOLS")
            
            # Habits Grid
            h1, h2, h3 = st.columns(3)
            with h1:
                run = st.checkbox("Running (20m)")
                vac = st.checkbox("Stomach Vacuum")
            with h2:
                lift = st.checkbox("Heavy Lift / Calisthenics")
                diet = st.checkbox("Diet Adherence")
            with h3:
                cold = st.checkbox("Cold Shower")
                junk = st.checkbox("Zero Junk Food")
                
            st.markdown("<br>", unsafe_allow_html=True)
            notes = st.text_area("Notes", placeholder="Add context: Energy levels, sleep quality...", height=80, label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            # 3. ACTION BUTTON
            submitted = st.form_submit_button("COMMIT ENTRY")

            if submitted:
                try:
                    sheet = get_db_connection()
                    # Check duplicate
                    if not df.empty and (df['date'] == pd.Timestamp(date_in)).any():
                        st.warning("⚠️ Entry for this date already exists.")
                    else:
                        row_data = [
                            date_in.strftime("%Y-%m-%d"), weight_in,
                            int(run), int(lift), int(cold), int(vac), int(diet), int(junk), 
                            7, str(notes)
                        ]
                        sheet.append_row(row_data)
                        
                        # --- THE FIX: USE SESSION STATE ---
                        st.session_state['success_msg'] = f"✅ ENTRY LOGGED FOR {date_in.strftime('%Y-%m-%d')}"
                        st.cache_data.clear()
                        st.rerun() 
                        
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 2: THE DASHBOARD
# ==========================================
with tab_dash:
    if not df.empty:
        # --- A. METRICS ENGINE ---
        curr = df['weight'].iloc[-1]
        start = df['weight'].iloc[0]
        delta = curr - start
        
        # Streak Calc
        streak = 0
        for i in range(len(df)-1, -1, -1):
            if df.iloc[i]['cold_shower'] == 1 and df.iloc[i]['vacuum'] == 1:
                streak += 1
            else: break
            
        # Custom HTML Metrics
        st.markdown('<div class="glass-container" style="padding: 0;">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""<div class="metric-box"><div class="metric-label">Current Weight</div><div class="metric-value">{curr}</div><div class="metric-sub">{round(delta, 1)} KG Total</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-box"><div class="metric-label">Protocol Streak</div><div class="metric-value">{streak}</div><div class="metric-sub">Days Active</div></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="metric-box"><div class="metric-label">Target</div><div class="metric-value">{round(curr - 85.0, 1)}</div><div class="metric-sub">KG Remaining</div></div>""", unsafe_allow_html=True)
        with col4:
            score = int(df.iloc[-1][['run_done','cold_shower','diet_strict']].mean()*100)
            st.markdown(f"""<div class="metric-box"><div class="metric-label">Discipline</div><div class="metric-value">{score}%</div><div class="metric-sub">Daily Score</div></div>""", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # --- B. CHARTS ENGINE (Plotly Pro) ---
        c_chart, c_cons = st.columns([2, 1])
        
        with c_chart:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            st.markdown("<h5>WEIGHT TRAJECTORY</h5>", unsafe_allow_html=True)
            
            fig = go.Figure()
            
            # Area Chart with Gradient
            fig.add_trace(go.Scatter(
                x=df['date'], y=df['weight'],
                mode='lines',
                fill='tozeroy',
                line=dict(color='#ffffff', width=2), # White Line
                fillcolor='rgba(255, 255, 255, 0.1)', # Subtle white fill
                name='Weight'
            ))
            
            # Goal Line
            fig.add_trace(go.Scatter(
                x=[df['date'].min(), df['date'].max() + timedelta(days=7)],
                y=[85, 85], mode='lines',
                line=dict(color='rgba(255,255,255,0.3)', dash='dash'),
                name='Goal'
            ))

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=20, l=0, r=0, b=0),
                height=300,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c_cons:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            st.markdown("<h5>HABIT DNA</h5>", unsafe_allow_html=True)
            
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            sums = df[habits].sum().sort_values()
            
            # Clean names
            labels = [h.replace('_done','').replace('_',' ').upper() for h in sums.index]
            
            fig_bar = go.Figure(go.Bar(
                x=sums.values,
                y=labels,
                orientation='h',
                marker=dict(
                    color='#ffffff',
                    opacity=0.8
                )
            ))
            
            fig_bar.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=10, l=0, r=0, b=0),
                height=310,
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("System Ready. Please log your first entry.")
