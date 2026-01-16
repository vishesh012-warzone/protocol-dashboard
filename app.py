import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PROTOCOL_OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. THE "21ST CENTURY" UI ENGINE (CSS) ---
st.markdown("""
<style>
    /* IMPORT FONT (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* GLOBAL RESET */
    .stApp {
        background-color: #050505; /* True Black */
        background-image: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #050505 60%);
        font-family: 'Inter', sans-serif;
    }

    /* REMOVE STREAMLIT BLOAT */
    header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 5rem;}

    /* GLASS CARDS */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-card:hover {
        border-color: rgba(60, 200, 255, 0.3);
        transform: translateY(-2px);
    }

    /* METRIC TEXT STYLING */
    .metric-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #888;
        font-weight: 600;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(90deg, #fff, #bbb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-delta {
        font-size: 14px;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 6px;
    }
    .delta-pos { color: #4ade80; background: rgba(74, 222, 128, 0.1); }
    .delta-neg { color: #f87171; background: rgba(248, 113, 113, 0.1); }
    .delta-neu { color: #60a5fa; background: rgba(96, 165, 250, 0.1); }

    /* INPUT FIELDS (Modern) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
        background-color: #0A0A0A !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
        color: #fff !important;
        padding: 12px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }

    /* BUTTONS (Gradient) */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: opacity 0.2s;
    }
    .stButton > button:hover {
        opacity: 0.9;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #333;
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #666;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #fff !important;
        border-bottom: 2px solid #3b82f6;
    }
    
    /* CHECKBOXES */
    .stCheckbox label span {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. BACKEND: CONNECTION & LOGIC ---
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

# --- 4. HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("<h1 style='font-size: 42px; margin-bottom: 0;'>PROTOCOL_OS <span style='color:#3b82f6; font-size:24px;'>v2.0</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666; margin-top: -10px;'>System Status: Optimized</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. INTERFACE TABS ---
tab_log, tab_dash = st.tabs(["ENTRY_TERMINAL", "ANALYTICS_HUB"])

# ==========================================
# TAB 1: THE INPUT TERMINAL
# ==========================================
with tab_log:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    with st.form("entry_form", clear_on_submit=False):
        # 1. SMART DEFAULT
        last_weight = 94.0
        if not df.empty:
            last_weight = float(df['weight'].iloc[-1])
            
        # 2. INPUT GRID
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("##### 📅 DATE SELECTOR")
            date_in = st.date_input("Select Date", datetime.today(), label_visibility="collapsed")
        with c2:
            st.markdown("##### ⚖️ WEIGHT (KG)")
            weight_in = st.number_input("Weight", value=last_weight, step=0.1, format="%.1f", label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown("##### ✅ DAILY PROTOCOLS")
        
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
            
        st.markdown("---")
        notes = st.text_area("Notes", placeholder="Add context: Energy levels, sleep quality...", height=80)
        
        # 3. ACTION BUTTON
        submitted = st.form_submit_button("COMMIT ENTRY ➔")

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
                    st.success("✅ Protocol Logged.")
                    # AUTO REFRESH MAGIC
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
        col1, col2, col3, col4 = st.columns(4)
        
        def metric_card(label, value, delta_text, color_class):
            return f"""
            <div class="glass-card" style="padding: 15px; margin-bottom: 0px;">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-delta {color_class}">{delta_text}</div>
            </div>
            """
        
        with col1:
            st.markdown(metric_card("Current Weight", f"{curr}", f"{round(delta, 1)} KG Since Start", "delta-pos" if delta < 0 else "delta-neg"), unsafe_allow_html=True)
        with col2:
            st.markdown(metric_card("Protocol Streak", f"{streak}", "Cold + Vacuum", "delta-neu"), unsafe_allow_html=True)
        with col3:
            st.markdown(metric_card("To Target", f"{round(curr - 85.0, 1)}", "Goal: 85.0 KG", "delta-neu"), unsafe_allow_html=True)
        with col4:
            st.markdown(metric_card("Discipline Score", f"{int(df.iloc[-1][['run_done','cold_shower','diet_strict']].mean()*100)}%", "Today's Rating", "delta-pos"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- B. CHARTS ENGINE (Plotly Pro) ---
        c_chart, c_cons = st.columns([2, 1])
        
        with c_chart:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("##### 📉 WEIGHT TRAJECTORY", unsafe_allow_html=True)
            
            fig = go.Figure()
            
            # Area Chart with Gradient
            fig.add_trace(go.Scatter(
                x=df['date'], y=df['weight'],
                mode='lines',
                fill='tozeroy',
                line=dict(color='#3b82f6', width=3),
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
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("##### 🧬 HABIT DNA", unsafe_allow_html=True)
            
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            sums = df[habits].sum().sort_values()
            
            # Clean names
            labels = [h.replace('_done','').replace('_',' ').upper() for h in sums.index]
            
            fig_bar = go.Figure(go.Bar(
                x=sums.values,
                y=labels,
                orientation='h',
                marker=dict(
                    color=sums.values,
                    colorscale='Bluered' # Gradient from Blue to Purple/Red
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
