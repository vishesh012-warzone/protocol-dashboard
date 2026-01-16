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

# --- 2. HATOM AESTHETIC (BRUTALIST TECH) ---
st.markdown("""
<style>
    /* IMPORT FONTS (Space Grotesk for Headings, Inter for UI) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

    /* GLOBAL RESET & GRID BACKGROUND */
    .stApp {
        background-color: #050505;
        /* Hatom-style subtle technical grid */
        background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        font-family: 'Inter', sans-serif;
        color: #ffffff;
    }

    /* HIDE STREAMLIT BLOAT */
    header {visibility: hidden;}
    .block-container {
        padding-top: 3rem;
        padding-bottom: 5rem;
        max-width: 1400px; /* Ultra Wide */
    }

    /* TYPOGRAPHY - MASSIVE & INDUSTRIAL */
    h1 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 64px;
        letter-spacing: -2px;
        line-height: 1;
        text-transform: uppercase;
        margin-bottom: 0px;
        color: #fff;
    }
    .status-badge {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 12px;
        border: 1px solid #333;
        padding: 5px 10px;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #888;
        background: #000;
        display: inline-block;
        margin-bottom: 40px;
    }
    h3, h4, h5 {
        font-family: 'Space Grotesk', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 500;
        color: #666;
    }

    /* BRUTALIST CONTAINERS (SHARP EDGES, 1PX BORDERS) */
    .tech-panel {
        background: #000;
        border: 1px solid #222;
        padding: 30px;
        margin-bottom: 24px;
        /* No border radius - Hatom style */
    }
    
    /* INPUTS - MINIMALIST UNDERLINES */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #0a0a0a !important;
        border: 1px solid #333 !important; /* Sharp borders */
        border-radius: 0px !important; /* Brutalist */
        color: #fff !important;
        font-family: 'Space Grotesk', monospace !important;
        padding: 15px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #fff !important;
        background-color: #111 !important;
    }
    
    /* CHECKBOXES - CUSTOM SQUARES */
    .stCheckbox label span {
        font-family: 'Space Grotesk', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 12px;
    }

    /* TABS - INDUSTRIAL */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #222;
        gap: 0px; /* Connected tabs */
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 14px;
        text-transform: uppercase;
        color: #555;
        border-radius: 0px;
        padding: 15px 30px;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #000 !important;
        background-color: #fff !important; /* Inverted active tab */
        font-weight: 700;
    }

    /* BUTTONS - HIGH CONTRAST */
    .stButton > button {
        width: 100%;
        border-radius: 0px; /* Sharp */
        height: 55px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        background: #fff;
        color: #000;
        border: 1px solid #fff;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #000;
        color: #fff;
        border: 1px solid #fff;
    }

    /* SUCCESS MESSAGE */
    .success-ticker {
        background: #000;
        border-left: 4px solid #fff;
        color: #fff;
        font-family: 'Space Grotesk', monospace;
        padding: 15px;
        margin-bottom: 20px;
        text-transform: uppercase;
    }

    /* METRIC TYPOGRAPHY */
    .big-number {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 56px;
        font-weight: 700;
        color: #fff;
        line-height: 1;
    }
    .metric-label {
        font-family: 'Inter', sans-serif;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #444;
        margin-bottom: 5px;
    }
    .metric-sub {
        font-family: 'Space Grotesk', monospace;
        color: #666;
        font-size: 14px;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. BACKEND ---
def get_db_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("warrior_db").sheet1
    except Exception as e:
        st.error(f"SYSTEM FAILURE: {e}")
        st.stop()

def load_data():
    try:
        sheet = get_db_connection()
        data = sheet.get_all_values()
        if len(data) < 2: return pd.DataFrame()
        
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)
        df = df[df['date'].astype(bool)] 
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
            
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            for col in habits:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.upper().replace({'TRUE': '1', 'FALSE': '0', '1': '1', '0': '0'})
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            return df.sort_values('date', ascending=True)
        return df
    except:
        return pd.DataFrame()

df = load_data()

# --- 4. HEADER UI ---
c_head, c_status = st.columns([3, 1])
with c_head:
    st.markdown("<h1>PROTOCOL OS</h1>", unsafe_allow_html=True)
with c_status:
    st.markdown("<div style='text-align:right'><span class='status-badge'>SYSTEM: ONLINE v4.0</span></div>", unsafe_allow_html=True)

st.markdown("---")

# Success Handler
if 'success_msg' in st.session_state:
    st.markdown(f"<div class='success-ticker'>{st.session_state['success_msg']}</div>", unsafe_allow_html=True)
    del st.session_state['success_msg']

# --- 5. TABS ---
tab_log, tab_dash, tab_history = st.tabs(["// ENTRY_TERMINAL", "// ANALYTICS_HUB", "// ARCHIVE_EDIT"])

# ==========================================
# TAB 1: BRUTALIST ENTRY FORM
# ==========================================
with tab_log:
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    c_form_l, c_form_r = st.columns([2, 1])
    
    with c_form_l:
        st.markdown('<div class="tech-panel">', unsafe_allow_html=True)
        with st.form("new_entry"):
            st.markdown("### 01 / DATA_INPUT")
            
            last_val = 94.0
            if not df.empty: last_val = float(df['weight'].iloc[-1])
            
            c1, c2 = st.columns(2)
            d_in = c1.date_input("DATE", datetime.today())
            w_in = c2.number_input("WEIGHT (KG)", value=last_val, step=0.1, format="%.1f")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 02 / PROTOCOL_CHECK")
            
            # Industrial Grid for Checkboxes
            h1, h2, h3 = st.columns(3)
            run = h1.checkbox("[A] RUNNING")
            vac = h1.checkbox("[B] VACUUM")
            lift = h2.checkbox("[C] WORKOUT")
            diet = h2.checkbox("[D] DIET")
            cold = h3.checkbox("[E] COLD SHOWER")
            junk = h3.checkbox("[F] NO JUNK")
            
            st.markdown("<br>", unsafe_allow_html=True)
            notes = st.text_area("SYSTEM_NOTES", height=100, placeholder="> ENTER LOG DETAILS...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button(">> EXECUTE UPLOAD"):
                try:
                    if not df.empty and (df['date'] == pd.Timestamp(d_in)).any():
                        st.warning(f"⚠️ DATA EXISTS FOR {d_in}. USE ARCHIVE TO EDIT.")
                    else:
                        sheet = get_db_connection()
                        row = [d_in.strftime("%Y-%m-%d"), w_in, int(run), int(lift), int(cold), int(vac), int(diet), int(junk), 7, str(notes)]
                        sheet.append_row(row)
                        st.session_state['success_msg'] = "/// UPLOAD COMPLETE ///"
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"ERROR: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with c_form_r:
        # Decorative side panel info
        st.markdown('<div class="tech-panel">', unsafe_allow_html=True)
        st.markdown("### GUIDANCE")
        st.caption("1. MEASURE WEIGHT FASTED.")
        st.caption("2. COLD SHOWER REQUIRED.")
        st.caption("3. NO DUPLICATE ENTRIES.")
        st.markdown("<br><br>", unsafe_allow_html=True)
        if not df.empty:
             st.metric("LAST LOGGED", df['date'].iloc[-1].strftime('%b %d'))
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 2: HIGH CONTRAST ANALYTICS
# ==========================================
with tab_dash:
    if not df.empty:
        curr = df['weight'].iloc[-1]
        start = df['weight'].iloc[0]
        delta = curr - start
        
        # 1. METRICS ROW (Hatom Style: Big Numbers)
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        
        def brutal_metric(label, val, sub):
            return f"""
            <div class="tech-panel" style="padding: 20px; border-top: 4px solid #fff;">
                <div class="metric-label">{label}</div>
                <div class="big-number">{val}</div>
                <div class="metric-sub">{sub}</div>
            </div>
            """
        
        with m1: st.markdown(brutal_metric("CURRENT MASS", curr, "KG"), unsafe_allow_html=True)
        with m2: st.markdown(brutal_metric("NET CHANGE", round(delta,1), "TOTAL KG"), unsafe_allow_html=True)
        with m3: st.markdown(brutal_metric("TARGET GAP", round(curr-85,1), "TO 85.0 KG"), unsafe_allow_html=True)
        
        # Streak Calc
        streak = 0
        for i in range(len(df)-1, -1, -1):
            if df.iloc[i]['cold_shower'] == 1 and df.iloc[i]['vacuum'] == 1: streak += 1
            else: break
        with m4: st.markdown(brutal_metric("CORE STREAK", streak, "DAYS ACTIVE"), unsafe_allow_html=True)

        # 2. CHARTS (STARK BLACK & WHITE)
        g1, g2 = st.columns([2, 1])
        
        with g1:
            st.markdown('<div class="tech-panel">', unsafe_allow_html=True)
            st.markdown("### TRAJECTORY_ANALYSIS")
            fig = go.Figure()
            # Area filled with white
            fig.add_trace(go.Scatter(x=df['date'], y=df['weight'], mode='lines', fill='tozeroy', 
                                   line=dict(color='#fff', width=2), 
                                   fillcolor='rgba(255,255,255,0.1)'))
            # Goal line
            fig.add_trace(go.Scatter(x=[df['date'].min(), df['date'].max()], y=[85, 85], 
                                   mode='lines', line=dict(dash='dot', color='#444')))
            
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            margin=dict(t=30,l=0,r=0,b=0), height=350, 
                            xaxis=dict(showgrid=True, gridcolor='#222', tickfont=dict(family='Space Grotesk')), 
                            yaxis=dict(showgrid=True, gridcolor='#222', tickfont=dict(family='Space Grotesk')),
                            showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with g2:
            st.markdown('<div class="tech-panel">', unsafe_allow_html=True)
            st.markdown("### HABIT_DENSITY")
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            sums = df[habits].sum().sort_values()
            
            fig2 = go.Figure(go.Bar(x=sums.values, y=[h.replace('_done','').upper() for h in sums.index], 
                                  orientation='h', marker_color='#fff'))
            
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                             margin=dict(t=30,l=0,r=0,b=0), height=350,
                             xaxis=dict(showgrid=False), 
                             yaxis=dict(tickfont=dict(family='Space Grotesk', size=10)))
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 3: ARCHIVE & EDIT
# ==========================================
with tab_history:
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    if not df.empty:
        # HEATMAP
        st.markdown('<div class="tech-panel" style="padding:10px">', unsafe_allow_html=True)
        df['score'] = df[['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']].sum(axis=1)
        fig_cal = go.Figure(data=go.Heatmap(z=[df['score']], x=df['date'], y=[' '], colorscale='Greys', showscale=False))
        fig_cal.update_layout(template="plotly_dark", height=120, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            margin=dict(t=0,b=20), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_cal, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # EDIT INTERFACE
        c_sel, c_edit = st.columns([1, 2])
        with c_sel:
            st.markdown("### SELECT DATE")
            edit_date = st.date_input("SEARCH ARCHIVE", datetime.today())
            record = df[df['date'] == pd.Timestamp(edit_date)]
            exists = not record.empty
            if exists: st.markdown(">> LOG FOUND")
            else: st.markdown(">> NO DATA")

        with c_edit:
            st.markdown('<div class="tech-panel">', unsafe_allow_html=True)
            if exists:
                row = record.iloc[0]
                with st.form("edit_form"):
                    st.markdown(f"**EDITING: {edit_date.strftime('%Y-%m-%d')}**")
                    ew_in = st.number_input("WEIGHT", value=float(row['weight']), step=0.1)
                    
                    ec1, ec2 = st.columns(2)
                    er = ec1.checkbox("[A] RUN", value=bool(row['run_done']))
                    ev = ec1.checkbox("[B] VACUUM", value=bool(row['vacuum']))
                    el = ec1.checkbox("[C] WORKOUT", value=bool(row['workout_done']))
                    ed = ec2.checkbox("[D] DIET", value=bool(row['diet_strict']))
                    ec = ec2.checkbox("[E] COLD", value=bool(row['cold_shower']))
                    ej = ec2.checkbox("[F] NO JUNK", value=bool(row['no_junk']))
                    
                    en = st.text_area("NOTES", value=str(row['notes']), height=80)
                    
                    if st.form_submit_button(">> OVERWRITE ENTRY"):
                        try:
                            sheet = get_db_connection()
                            cell = sheet.find(edit_date.strftime("%Y-%m-%d"))
                            if cell:
                                r_idx = cell.row
                                new_vals = [edit_date.strftime("%Y-%m-%d"), ew_in, int(er), int(el), int(ec), int(ev), int(ed), int(ej), 7, str(en)]
                                sheet.update(range_name=f"A{r_idx}:J{r_idx}", values=[new_vals])
                                st.session_state['success_msg'] = "/// DATABASE UPDATED ///"
                                st.cache_data.clear()
                                st.rerun()
                        except Exception as e:
                            st.error(f"FAIL: {e}")
            else:
                st.info("NO ENTRY TO EDIT.")
            st.markdown('</div>', unsafe_allow_html=True)
