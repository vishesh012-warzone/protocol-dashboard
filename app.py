import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PROTOCOL OS | HATOM EDITION",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. THE "LIVING NEBULA" ENGINE (CSS) ---
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&family=Inter:wght@300;400;600&display=swap');

    /* --- 1. THE MOVING BACKGROUND (The Fix) --- */
    .stApp {
        background-color: #02040a;
        /* High-Res Deep Space Texture */
        background-image: url('https://images.unsplash.com/photo-1465101162946-4377e57745c3?q=80&w=2948&auto=format&fit=crop');
        background-size: 130% 130%;
        background-position: center;
        /* The "Alive" Animation - Drifts slowly forever */
        animation: nebuladrift 60s ease-in-out infinite alternate;
    }

    @keyframes nebuladrift {
        0% { background-position: 10% 10%; transform: scale(1); }
        50% { background-position: 90% 50%; transform: scale(1.05); }
        100% { background-position: 10% 90%; transform: scale(1); }
    }

    /* --- 2. GLOBAL OVERLAYS (Texture & Glow) --- */
    /* Vignette to focus eyes on center */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: radial-gradient(circle at 50% 50%, transparent 0%, #000000 90%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Subtle Grid Overlay for Tech Feel */
    .stApp::after {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 60px 60px;
        pointer-events: none;
        z-index: 0;
    }

    /* Hide Streamlit Bloat */
    header, footer {visibility: hidden !important;}
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 1400px;
        z-index: 2; /* Sit above background */
        position: relative;
    }

    /* --- 3. GLASS CARDS (Hatom Style) --- */
    .glass-panel {
        background: rgba(13, 18, 30, 0.65); /* Darker, richer blue */
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-top: 1px solid rgba(255, 255, 255, 0.15); /* Highlight top edge */
        border-radius: 24px;
        padding: 30px;
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
        margin-bottom: 24px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .glass-panel:hover {
        transform: translateY(-5px) scale(1.01);
        border-color: rgba(6, 182, 212, 0.4); /* Cyan Glow */
        box-shadow: 0 30px 60px -12px rgba(6, 182, 212, 0.15); /* Ambient Glow */
    }

    /* --- 4. TYPOGRAPHY (Outfit Font) --- */
    h1, h2, h3 { font-family: 'Outfit', sans-serif; color: #fff; text-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    
    .hero-text {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 72px;
        background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -2px;
        line-height: 1;
        margin-bottom: 10px;
        filter: drop-shadow(0 0 30px rgba(255,255,255,0.2));
    }
    
    .sub-hero {
        font-family: 'Inter', sans-serif;
        color: #94A3B8;
        font-size: 16px;
        letter-spacing: 1px;
    }

    .label-tech {
        font-family: 'Outfit', sans-serif;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #64748B;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .label-tech::before {
        content: ""; width: 6px; height: 6px; background: #06B6D4; border-radius: 50%;
        box-shadow: 0 0 10px #06B6D4;
    }

    /* --- 5. INPUT FIELDS (Deep Glass) --- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        color: #F8FAFC !important;
        padding: 15px !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        background-color: rgba(6, 182, 212, 0.05) !important;
        border-color: #06B6D4 !important;
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.2);
    }

    /* --- 6. BUTTONS (Electric Gradient) --- */
    .stButton > button {
        width: 100%;
        height: 60px;
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
        border: none;
        border-radius: 16px;
        color: white;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 16px;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 40px rgba(6, 182, 212, 0.5); /* Massive Glow */
    }

    /* --- 7. TABS (Floating Pills) --- */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.03);
        padding: 8px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        gap: 12px;
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        color: #64748B;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        border-radius: 12px;
        padding: 10px 24px;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.1);
        color: #fff !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }

    /* --- 8. SUCCESS TOAST --- */
    .success-toast {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10B981;
        color: #10B981;
        padding: 16px;
        border-radius: 12px;
        text-align: center;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 30px;
        box-shadow: 0 0 30px rgba(16, 185, 129, 0.2);
    }

    /* METRICS STYLING */
    .metric-val { font-size: 48px; font-family: 'Outfit'; font-weight: 800; color: #fff; line-height:1; }
    .metric-lbl { font-size: 11px; font-family: 'Inter'; text-transform:uppercase; letter-spacing:2px; color:#94A3B8; margin-bottom:5px; }
</style>
""", unsafe_allow_html=True)

# --- 3. BACKEND CONNECTION ---
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

# --- 4. HERO SECTION ---
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown('<div class="hero-text">PROTOCOL OS</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-hero">ADVANCED BIOMETRIC TRACKING SYSTEM</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div style="text-align:right; padding-top:40px; font-family:Outfit; color:#94a3b8; font-size:14px; letter-spacing:1px;">STATUS: <b style="color:#4ade80; text-shadow:0 0 15px #4ade80;">● ONLINE</b></div>', unsafe_allow_html=True)

st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)

if 'success_msg' in st.session_state:
    st.markdown(f"<div class='success-toast'>{st.session_state['success_msg']}</div>", unsafe_allow_html=True)
    del st.session_state['success_msg']

# --- 5. UI TABS ---
tab_log, tab_dash, tab_history = st.tabs(["ENTRY TERMINAL", "ANALYTICS HUB", "DATA ARCHIVE"])

# ==========================================
# TAB 1: ENTRY TERMINAL
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
            notes = st.text_area("Session Notes", height=100, placeholder="Energy levels, focus, sleep quality...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("INITIATE UPLOAD"):
                try:
                    if not df.empty and (df['date'] == pd.Timestamp(d_in)).any():
                        st.warning("Data for this date already exists.")
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
# TAB 2: ANALYTICS HUB
# ==========================================
with tab_dash:
    if not df.empty:
        curr = df['weight'].iloc[-1]
        start = df['weight'].iloc[0]
        
        # METRICS GRID
        c1, c2, c3, c4 = st.columns(4)
        
        def card(lbl, val, sub):
            return f"""
            <div class="glass-panel" style="text-align:center; padding:25px; margin-bottom:0;">
                <div class="metric-lbl">{lbl}</div>
                <div class="metric-val">{val}</div>
                <div style="font-size:13px; color:#64748B; margin-top:5px; font-weight:500;">{sub}</div>
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

        # CHARTS
        g1, g2 = st.columns([2, 1])
        
        with g1:
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            st.markdown('<div class="label-tech">TRAJECTORY ANALYSIS</div>', unsafe_allow_html=True)
            fig = go.Figure()
            # Gradient Area Chart
            fig.add_trace(go.Scatter(x=df['date'], y=df['weight'], mode='lines', 
                                   fill='tozeroy', 
                                   line=dict(color='#06B6D4', width=3), # Cyan Line
                                   fillcolor='rgba(6, 182, 212, 0.1)')) # Cyan Fill
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
            fig2 = go.Figure(go.Bar(x=sums.values, y=[h.replace('_done','').replace('_',' ').upper() for h in sums.index], 
                                  orientation='h', marker=dict(color=sums.values, colorscale='Cyan')))
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                            margin=dict(t=20,l=0,r=0,b=0), height=350, xaxis=dict(showgrid=False))
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 3: DATA ARCHIVE
# ==========================================
with tab_history:
    if not df.empty:
        st.markdown('<div class="glass-panel" style="padding:20px">', unsafe_allow_html=True)
        st.markdown('<div class="label-tech">CONSISTENCY MAP</div>', unsafe_allow_html=True)
        df['score'] = df[['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']].sum(axis=1)
        fig_cal = go.Figure(data=go.Heatmap(z=[df['score']], x=df['date'], y=[' '], colorscale='Cyan', showscale=False))
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
