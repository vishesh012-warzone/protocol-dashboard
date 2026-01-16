import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PROTOCOL_V1", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. THE "CURSOR" AESTHETIC (CUSTOM CSS) ---
st.markdown("""
<style>
    /* 1. MAIN BACKGROUND - Deep IDE Grey */
    .stApp {
        background-color: #09090b; /* Very dark grey, almost black */
    }
    
    /* 2. REMOVE STREAMLIT PADDING */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* 3. CARDS & CONTAINERS - Thin Borders, No Shadows (Flat Look) */
    div[data-testid="stMetric"], div[data-testid="stForm"] {
        background-color: #121212;
        border: 1px solid #27272a;
        border-radius: 6px; /* Tighter radius for tech feel */
        padding: 20px;
    }
    
    /* 4. TYPOGRAPHY - Monospace Headers */
    h1, h2, h3, .stMetricLabel {
        font-family: 'SF Mono', 'Courier New', monospace !important;
        letter-spacing: -0.5px;
        color: #e4e4e7 !important;
    }
    
    /* 5. INPUTS - Dark & Minimal */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
        background-color: #18181b !important;
        color: #e4e4e7 !important;
        border: 1px solid #27272a !important;
        border-radius: 4px;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #22d3ee !important; /* Cyan glow on focus */
    }

    /* 6. BUTTONS - Subtle Glow */
    .stButton > button {
        background-color: #e4e4e7;
        color: #09090b;
        border: none;
        border-radius: 4px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #22d3ee; /* Cyan hover */
        box-shadow: 0 0 10px rgba(34, 211, 238, 0.4);
    }
    
    /* 7. TABS - Minimalist */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #27272a;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #71717a;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        color: #22d3ee !important;
        border-bottom: 2px solid #22d3ee;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---
def get_db_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("warrior_db").sheet1
    except Exception as e:
        st.error(f"Database Connection Failed: {e}")
        st.stop()

def load_data():
    try:
        sheet = get_db_connection()
        data = sheet.get_all_values() # Get raw values to handle empty rows better
        if len(data) < 2: return pd.DataFrame()
        
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)
        
        # FILTER: Drop rows where Date is empty (Fixes the 1000 row bug)
        df = df[df['date'].astype(bool)] 
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
            
            # Clean Habits
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            for col in habits:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.upper().replace({'TRUE': '1', 'FALSE': '0', '1': '1', '0': '0'})
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            return df.sort_values('date', ascending=True) # Sort Oldest -> Newest for Charts
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# --- 4. UI: HEADER ---
st.title("PROTOCOL_V1")
st.markdown("`STATUS: ACTIVE` &nbsp; `USER: ADMIN`", unsafe_allow_html=True)
st.markdown("---")

# --- 5. TABS ---
tab_log, tab_dash = st.tabs(["// LOG_ENTRY", "// ANALYTICS_DASHBOARD"])

# ==========================================
# TAB 1: THE INPUT TERMINAL
# ==========================================
with tab_log:
    col_main, col_padding = st.columns([1, 1]) # Limit width for better aesthetics
    
    with col_main:
        with st.form("entry_form", clear_on_submit=False):
            st.markdown("### NEW_ENTRY")
            
            # Smart Default Weight
            default_weight = 94.0
            if not df.empty:
                default_weight = float(df['weight'].iloc[-1])

            c1, c2 = st.columns(2)
            with c1:
                date_in = st.date_input("DATE", datetime.today())
            with c2:
                weight_in = st.number_input("WEIGHT (KG)", value=default_weight, step=0.1, format="%.1f")
            
            st.markdown("#### HABIT_CHECKLIST")
            # Custom Checkbox Layout
            ch1, ch2 = st.columns(2)
            with ch1:
                run = st.checkbox("[ ] MORNING_RUN")
                lift = st.checkbox("[ ] WORKOUT_LIFT")
                cold = st.checkbox("[ ] COLD_SHOWER")
            with ch2:
                vac = st.checkbox("[ ] STOMACH_VACUUM")
                diet = st.checkbox("[ ] DIET_ADHERENCE")
                junk = st.checkbox("[ ] NO_JUNK_FOOD")
                
            notes = st.text_area("LOG_NOTES", height=80, placeholder="> System note: Energy levels...")
            
            submitted = st.form_submit_button(">> COMMIT_DATA")

            if submitted:
                try:
                    sheet = get_db_connection()
                    # Check for duplicates locally first
                    if not df.empty and (df['date'] == pd.Timestamp(date_in)).any():
                        st.warning("⚠️ ERROR: ENTRY_EXISTS_FOR_DATE")
                    else:
                        row_data = [
                            date_in.strftime("%Y-%m-%d"), weight_in,
                            int(run), int(lift), int(cold), int(vac), int(diet), int(junk), 
                            7, str(notes)
                        ]
                        sheet.append_row(row_data)
                        st.success("SUCCESS: DATA_UPLOADED")
                        st.cache_data.clear()
                except Exception as e:
                    st.error(f"SYSTEM_ERROR: {e}")

# ==========================================
# TAB 2: THE DASHBOARD (CHART OVERHAUL)
# ==========================================
with tab_dash:
    if not df.empty:
        # --- METRICS ROW ---
        curr_w = df['weight'].iloc[-1]
        start_w = df['weight'].iloc[0]
        streak = 0
        # Calculate streak from the end (most recent) backwards
        # Note: df is sorted Oldest -> Newest, so we reverse it for streak calc
        for i in range(len(df)-1, -1, -1):
            if df.iloc[i]['cold_shower'] == 1 and df.iloc[i]['vacuum'] == 1:
                streak += 1
            else:
                break

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("CURRENT_WEIGHT", f"{curr_w} kg", f"{round(curr_w - start_w, 1)} kg")
        m2.metric("CORE_STREAK", f"{streak} DAYS", "COLD + VAC")
        m3.metric("TO_GOAL", f"{round(curr_w - 85.0, 1)} kg", "TARGET: 85.0")
        m4.metric("TOTAL_LOGS", len(df), "ENTRIES")

        st.markdown("<br>", unsafe_allow_html=True) # Spacer

        # --- CHART 1: NEON AREA CHART (WEIGHT) ---
        col_chart, col_habit = st.columns([2, 1])
        
        with col_chart:
            st.markdown("##### WEIGHT_TRAJECTORY")
            
            fig = go.Figure()
            
            # 1. Target Line
            fig.add_trace(go.Scatter(
                x=[df['date'].min(), df['date'].max() + timedelta(days=5)], 
                y=[85, 85],
                mode='lines',
                line=dict(color='rgba(255, 255, 255, 0.2)', width=1, dash='dash'),
                name='TARGET'
            ))

            # 2. Weight Line (Area Gradient)
            fig.add_trace(go.Scatter(
                x=df['date'], y=df['weight'],
                mode='lines+markers',
                fill='tozeroy', # Fill area below
                line=dict(color='#22d3ee', width=3), # Cyan Neon
                marker=dict(size=8, color='#09090b', line=dict(width=2, color='#22d3ee')),
                name='WEIGHT'
            ))

            # CHART STYLING (The "Better Charts" Part)
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', # Transparent
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent
                margin=dict(l=0, r=0, t=20, b=0),
                height=350,
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=True, gridcolor='#27272a', range=[80, max(df['weight'])+2]), # Custom grid color
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_habit:
            st.markdown("##### HABIT_CONSISTENCY")
            
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            habit_sums = df[habits].sum().sort_values(ascending=True)
            
            # Clean Labels for Chart
            clean_labels = [h.replace('_done', '').replace('_', ' ').upper() for h in habit_sums.index]
            
            fig_bar = go.Figure(go.Bar(
                x=habit_sums.values,
                y=clean_labels,
                orientation='h',
                marker=dict(
                    color=habit_sums.values,
                    colorscale='Tealgrn', # Dark Green to Teal gradient
                )
            ))
            
            fig_bar.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=20, b=0),
                height=350,
                xaxis=dict(showgrid=False, showticklabels=False), # Minimalist
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.info("AWAITING_DATA... PLEASE LOG FIRST ENTRY.")
