import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PROTOCOL OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. HIGH-PERFORMANCE VISUAL ENGINE (CSS) ---
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    /* --- OPTIMIZED BACKGROUND (CSS PLASMA) --- */
    /* Instead of a heavy image, we use gradients that move. Zero lag. */
    .stApp {
        background-color: #02040a;
        background-image: 
            radial-gradient(at 0% 0%, rgba(6, 182, 212, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(37, 99, 235, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.15) 0px, transparent 50%),
            radial-gradient(at 0% 100%, rgba(6, 182, 212, 0.1) 0px, transparent 50%);
        background-size: 200% 200%;
        animation: plasma 15s ease infinite alternate;
    }

    @keyframes plasma {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* GRID OVERLAY (Static) */
    .stApp::after {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: 0;
    }

    /* REMOVE BLOAT */
    header, footer {visibility: hidden !important;}
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 1400px;
        z-index: 1;
    }

    /* --- OPTIMIZED GLASS CARDS --- */
    /* Reduced blur radius for better performance */
    .glass-panel {
        background: rgba(13, 17, 28, 0.7); 
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 24px;
        backdrop-filter: blur(12px); /* Lower blur = Higher FPS */
        -webkit-backdrop-filter: blur(12px);
        margin-bottom: 20px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-panel:hover {
        border-color: rgba(6, 182, 212, 0.5);
        transform: translateY(-2px);
    }

    /* --- TYPOGRAPHY --- */
    h1, h2, h3 { font-family: 'Outfit', sans-serif; color: #fff; }
    
    .hero-text {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 64px;
        background: linear-gradient(135deg, #fff 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -2px;
        line-height: 1;
        margin-bottom: 5px;
    }
    
    .label-tech {
        font-family: 'Outfit', sans-serif;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #64748B;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .label-tech::before {
        content: ""; width: 6px; height: 6px; background: #06B6D4; border-radius: 50%;
        box-shadow: 0 0 8px #06B6D4;
    }

    /* --- INPUTS & BUTTONS --- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: #fff !important;
        padding: 12px !important;
        font-family: 'Inter', sans-serif;
    }
    
    .stButton > button {
        width: 100%;
        height: 50px;
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
        border: none;
        border-radius: 12px;
        color: white;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton > button:hover {
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.4);
    }

    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.03);
        padding: 6px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        border-radius: 10px;
        padding: 8px 20px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.1);
        color: #fff !important;
    }

    /* --- METRICS & ALERTS --- */
    .metric-val { font-size: 42px; font-family: 'Outfit'; font-weight: 800; color: #fff; }
    .metric-lbl { font-size: 11px; font-family: 'Inter'; text-transform:uppercase; letter-spacing:1px; color:#94A3B8; }
    
    .success-toast {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid #10B981;
        color: #10B981;
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. OPTIMIZED BACKEND ---
def get_db_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("warrior_db").sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        st.stop()

# CACHING ENABLED: Prevents re-loading data on every click (Reduces Lag)
@st.cache_data(ttl=10) 
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

# --- 4. HEADER ---
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown('<div class="hero-text">PROTOCOL OS</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div style="text-align:right; padding-top:30px; font-family:Outfit; color:#94a3b8; font-size:14px; letter-spacing:1px;">SYSTEM: <b style="color:#4ade80;">● ONLINE</b></div>', unsafe_allow_html=True)

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

if 'success_msg' in st.session_state:
    st.markdown(f"<div class='success-toast'>{st.session_state['success_msg']}</div>", unsafe_allow_html=True)
    del st.session_state['success_msg']

# --- 5. TABS ---
tab_log, tab_dash, tab_history = st.tabs(["ENTRY TERMINAL", "ANALYTICS HUB", "DATA ARCHIVE"])

# ==========================================
# TAB 1: ENTRY
# ==========================================
with tab_log:
    c_pad_l, c_main, c_pad_r = st.columns([1, 2, 1])
    with c_main:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        with st.form("entry_form"):
            last_val = 94.0
            if not df.empty: last_val = float(df['weight'].iloc[-1])
            
            st.markdown('<div class="label-tech">NEW DATA LOG</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            d_in = c1.date_input("Date", datetime.today())
            w_in = c2.number_input("Weight (kg)", value=last_val, step=0.1, format="%.1f")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="label-tech">PROTOCOL CHECKLIST</div>', unsafe_allow_html=True)
            
            h1, h2 = st.columns(2)
            with h1:
                run = st.checkbox("Running (20m)")
                vac = st.checkbox("Stomach Vacuum")
                lift = st.checkbox("Heavy Lift")
            with h2:
                cold = st.checkbox("Cold Shower")
                diet = st.checkbox("Diet Adherence")
                junk = st.checkbox("No Junk Food")
            
            st.markdown("<br>", unsafe_allow_html=True)
            notes = st.text_area("Session Notes", height=80, placeholder="Details...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("INITIATE UPLOAD"):
                try:
                    if not df.empty and (df['date'] == pd.Timestamp(d_in)).any():
                        st.warning("Date exists.")
                    else:
                        sheet = get_db_connection()
                        row = [d_in.strftime("%Y-%m-%d"), w_in, int(run), int(lift), int(cold), int(vac), int(diet), int(junk), 7, str(notes)]
                        sheet.append_row(row)
                        st.session_state['success_msg'] = "/// UPLOAD COMPLETE"
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 2: ANALYTICS (FIXED COLORSCALE)
# ==========================================
with tab_dash:
    if not df.empty:
        curr = df['weight'].iloc[-1]
        start = df['weight'].iloc[0]
        
        c1, c2, c3, c4 = st.columns(4)
        
        def card(lbl, val, sub):
            return f"""
            <div class="glass-panel" style="text-align:center; padding:20px; margin-bottom:0;">
                <div class="metric-lbl">{lbl}</div>
                <div class="metric-val">{val}</div>
                <div style="font-size:12px; color:#64748B; margin-top:5px;">{sub}</div>
            </div>
            """
            
        streak = 0
        for i in range(len(df)-1, -1, -1):
            if df.iloc[i]['cold_shower'] == 1 and df.iloc[i]['vacuum'] == 1: streak += 1
            else: break
            
        with c1: st.markdown(card("CURRENT MASS", curr, f"{round(curr-start,1)} KG CHANGE"), unsafe_allow_html=True)
        with c2: st.markdown(card("STREAK", streak, "DAYS ACTIVE"), unsafe_allow_html=True)
        with c3: st.markdown(card("TO GOAL", round(curr-85,1), "KG REMAINING"), unsafe_allow_html=True)
        with c4: 
            score = int(df.iloc[-1][['run_done','cold_shower','diet_strict']].mean()*100)
            st.markdown(card("SCORE", f"{score}%", "DAILY RATING"), unsafe_allow_html=True)
            
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        g1, g2 = st.columns([2, 1])
        
        with g1:
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            st.markdown('<div class="label-tech">TRAJECTORY</div>', unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['weight'], mode='lines', 
                                   fill='tozeroy', 
                                   line=dict(color='#06B6D4', width=3), 
                                   fillcolor='rgba(6, 182, 212, 0.1)'))
            fig.add_trace(go.Scatter(x=[df['date'].min(), df['date'].max()], y=[85, 85], mode='lines', line=dict(dash='dash', color='#64748B')))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                            margin=dict(t=20,l=0,r=0,b=0), height=350, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with g2:
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            st.markdown('<div class="label-tech">HABIT DENSITY</div>', unsafe_allow_html=True)
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            sums = df[habits].sum().sort_values()
            
            # --- THE FIX: CUSTOM COLORSCALE (NO MORE CRASH) ---
            # We use a manual list of colors instead of the name "Cyan"
            cyan_scale = [[0, 'rgba(6, 182, 212, 0.3)'], [1, '#06B6D4']]
            
            fig2 = go.Figure(go.Bar(
                x=sums.values, 
                y=[h.replace('_done','').replace('_',' ').upper() for h in sums.index], 
                orientation='h', 
                marker=dict(color=sums.values, colorscale=cyan_scale)
            ))
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                            margin=dict(t=20,l=0,r=0,b=0), height=350, xaxis=dict(showgrid=False))
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 3: ARCHIVE
# ==========================================
with tab_history:
    if not df.empty:
        st.markdown('<div class="glass-panel" style="padding:20px">', unsafe_allow_html=True)
        st.markdown('<div class="label-tech">CONSISTENCY MAP</div>', unsafe_allow_html=True)
        df['score'] = df[['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']].sum(axis=1)
        
        # Fixed colorscale here too
        cyan_scale = [[0, '#0F172A'], [1, '#06B6D4']]
        
        fig_cal = go.Figure(data=go.Heatmap(z=[df['score']], x=df['date'], y=[' '], colorscale=cyan_scale, showscale=False))
        fig_cal.update_layout(template="plotly_dark", height=120, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=0,b=20), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_cal, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        c_sel, c_edit = st.columns([1, 2])
        with c_sel:
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            st.markdown('<div class="label-tech">SEARCH ARCHIVE</div>', unsafe_allow_html=True)
            edit_date = st.date_input("Select Date", datetime.today())
            record = df[df['date'] == pd.Timestamp(edit_date)]
            if not record.empty: st.markdown("<b style='color:#4ade80'>● RECORD FOUND</b>", unsafe_allow_html=True)
            else: st.markdown("<b style='color:#64748B'>○ NO DATA</b>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with c_edit:
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            if not record.empty:
                row = record.iloc[0]
                with st.form("edit_form"):
                    st.markdown(f"**EDITING: {edit_date.strftime('%Y-%m-%d')}**")
                    ew_in = st.number_input("Weight", value=float(row['weight']), step=0.1)
                    ec1, ec2 = st.columns(2)
                    er = ec1.checkbox("Run", value=bool(row['run_done']))
                    el = ec1.checkbox("Lift", value=bool(row['workout_done']))
                    ec = ec1.checkbox("Cold", value=bool(row['cold_shower']))
                    ev = ec2.checkbox("Vacuum", value=bool(row['vacuum']))
                    ed = ec2.checkbox("Diet", value=bool(row['diet_strict']))
                    ej = ec2.checkbox("No Junk", value=bool(row['no_junk']))
                    en = st.text_area("Notes", value=str(row['notes']))
                    
                    if st.form_submit_button("UPDATE ENTRY"):
                        try:
                            sheet = get_db_connection()
                            cell = sheet.find(edit_date.strftime("%Y-%m-%d"))
                            if cell:
                                r_idx = cell.row
                                new_vals = [edit_date.strftime("%Y-%m-%d"), ew_in, int(er), int(el), int(ec), int(ev), int(ed), int(ej), 7, str(en)]
                                sheet.update(range_name=f"A{r_idx}:J{r_idx}", values=[new_vals])
                                st.session_state['success_msg'] = "/// UPDATE COMPLETE"
                                st.cache_data.clear()
                                st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
            else:
                st.info("Select a date to edit.")
            st.markdown('</div>', unsafe_allow_html=True)
