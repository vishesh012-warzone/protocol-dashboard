import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PROTOCOL OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. THE "HATOM" PARALLAX ENGINE (JS + CSS) ---
# We inject JavaScript to track mouse movement and update CSS variables for the background shift.
st.markdown("""
<script>
    // ACCESS THE PARENT WINDOW (Streamlit runs in an iframe)
    var doc = window.parent.document;
    
    // LISTEN FOR MOUSE MOVEMENT
    doc.addEventListener('mousemove', function(e) {
        var w = window.innerWidth;
        var h = window.innerHeight;
        var mouseX = e.clientX;
        var mouseY = e.clientY;
        
        // CALCULATE MOVEMENT (Inverse direction for depth)
        var moveX = (w / 2 - mouseX) * 0.02; // Strength of horizontal shift
        var moveY = (h / 2 - mouseY) * 0.02; // Strength of vertical shift
        
        // UPDATE CSS VARIABLES ON THE APP BODY
        doc.body.style.setProperty('--bg-x', moveX + 'px');
        doc.body.style.setProperty('--bg-y', moveY + 'px');
    });
</script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;500;600&display=swap');

    /* --- GLOBAL ANIMATED BACKGROUND --- */
    .stApp {
        background-color: #02040a; /* Deep Void Base */
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }

    /* THE PARALLAX LAYER */
    .stApp::before {
        content: "";
        position: fixed;
        top: -5%;
        left: -5%;
        width: 110%;
        height: 110%;
        /* HATOM-STYLE ALIEN LANDSCAPE WALLPAPER */
        background-image: url('https://images.unsplash.com/photo-1614730341194-75c60740a270?q=80&w=2574&auto=format&fit=crop'); 
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        /* GLOWING OVERLAY */
        box-shadow: inset 0 0 200px rgba(0,0,0,0.8);
        filter: contrast(1.1) brightness(0.8) hue-rotate(240deg); /* Shift to Hatom Purple */
        z-index: -1;
        
        /* CONNECT TO JS VARIABLES */
        transform: translate(var(--bg-x, 0px), var(--bg-y, 0px));
        transition: transform 0.1s ease-out; /* Smooth lag */
    }

    /* REMOVE DEFAULT PADDING */
    .block-container {
        padding-top: 4rem;
        padding-bottom: 5rem;
        max-width: 1400px;
    }
    header {visibility: hidden;}

    /* --- HATOM GLASS CARDS --- */
    .hatom-card {
        background: rgba(13, 17, 28, 0.6); /* Semi-transparent dark blue */
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 30px;
        backdrop-filter: blur(24px); /* Heavy Blur */
        -webkit-backdrop-filter: blur(24px);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
        margin-bottom: 24px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    /* HOVER GLOW EFFECT */
    .hatom-card:hover {
        border-color: rgba(139, 92, 246, 0.4); /* Purple Glow */
        transform: translateY(-5px);
        box-shadow: 0 30px 60px rgba(139, 92, 246, 0.15);
    }
    .hatom-card::after {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    }

    /* --- TYPOGRAPHY --- */
    h1, h2, h3 { font-family: 'Outfit', sans-serif; color: #fff; }
    
    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 64px;
        background: linear-gradient(180deg, #fff 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -2px;
        text-shadow: 0 0 40px rgba(139, 92, 246, 0.3);
    }

    .section-label {
        font-family: 'Outfit', sans-serif;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #94a3b8;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-label::before {
        content: "";
        width: 8px; height: 8px;
        background: #8b5cf6;
        border-radius: 50%;
        box-shadow: 0 0 10px #8b5cf6;
    }

    /* --- INPUTS --- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #fff !important;
        padding: 16px !important;
        font-family: 'Inter', sans-serif;
        backdrop-filter: blur(10px);
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #8b5cf6 !important; /* Hatom Purple */
        background-color: rgba(139, 92, 246, 0.1) !important;
    }

    /* --- BUTTONS --- */
    .stButton > button {
        width: 100%;
        height: 56px;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); /* Indigo to Purple */
        border: none;
        border-radius: 14px;
        color: white;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s;
        box-shadow: 0 10px 30px rgba(124, 58, 237, 0.3);
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 20px 40px rgba(124, 58, 237, 0.5);
    }

    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.03);
        padding: 6px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.05);
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #64748b;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        border-radius: 12px;
        padding: 10px 20px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.1);
        color: #fff !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    /* --- METRICS --- */
    .metric-val {
        font-family: 'Outfit', sans-serif;
        font-size: 46px;
        font-weight: 700;
        color: #fff;
        text-shadow: 0 0 20px rgba(255,255,255,0.2);
    }
    .metric-lbl {
        color: #94a3b8;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 5px;
    }

    /* --- SUCCESS --- */
    .hatom-success {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #6ee7b7;
        padding: 16px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        letter-spacing: 0.5px;
        backdrop-filter: blur(10px);
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
        st.error(f"⚠️ DISCONNECTED: {e}")
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
    st.markdown('<div class="hero-title">PROTOCOL OS</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div style="text-align:right; padding-top:20px; font-family:Outfit; color:#94a3b8; letter-spacing:1px;">SYSTEM STATUS: <span style="color:#4ade80; text-shadow:0 0 10px #4ade80;">● ONLINE</span></div>', unsafe_allow_html=True)

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

if 'success_msg' in st.session_state:
    st.markdown(f"<div class='hatom-success'>{st.session_state['success_msg']}</div>", unsafe_allow_html=True)
    del st.session_state['success_msg']

# --- 5. INTERFACE ---
tab_log, tab_dash, tab_history = st.tabs(["ENTRY TERMINAL", "ANALYTICS HUB", "DATA ARCHIVE"])

# ==========================================
# TAB 1: ENTRY TERMINAL
# ==========================================
with tab_log:
    c_pad_l, c_main, c_pad_r = st.columns([1, 2, 1])
    
    with c_main:
        st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">NEW DATA LOG</div>', unsafe_allow_html=True)
        
        with st.form("entry_form"):
            last_val = 94.0
            if not df.empty: last_val = float(df['weight'].iloc[-1])
            
            c1, c2 = st.columns(2)
            d_in = c1.date_input("Date", datetime.today())
            w_in = c2.number_input("Weight (kg)", value=last_val, step=0.1, format="%.1f")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-label">PROTOCOL CHECKLIST</div>', unsafe_allow_html=True)
            
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
            notes = st.text_area("Session Notes", height=80, placeholder="Details on energy, mood, and performance...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("INITIATE UPLOAD"):
                try:
                    if not df.empty and (df['date'] == pd.Timestamp(d_in)).any():
                        st.warning("Data for this date already exists.")
                    else:
                        sheet = get_db_connection()
                        row = [d_in.strftime("%Y-%m-%d"), w_in, int(run), int(lift), int(cold), int(vac), int(diet), int(junk), 7, str(notes)]
                        sheet.append_row(row)
                        st.session_state['success_msg'] = "/// UPLOAD SUCCESSFUL"
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
        
        # METRICS
        c1, c2, c3, c4 = st.columns(4)
        
        def metric_card(lbl, val, sub):
            return f"""
            <div class="hatom-card" style="padding: 20px; text-align:center;">
                <div class="metric-lbl">{lbl}</div>
                <div class="metric-val">{val}</div>
                <div style="font-size:12px; color:#64748b;">{sub}</div>
            </div>
            """
            
        streak = 0
        for i in range(len(df)-1, -1, -1):
            if df.iloc[i]['cold_shower'] == 1 and df.iloc[i]['vacuum'] == 1: streak += 1
            else: break
            
        with c1: st.markdown(metric_card("CURRENT MASS", f"{curr}", f"{round(curr-start,1)} KG CHANGE"), unsafe_allow_html=True)
        with c2: st.markdown(metric_card("PROTOCOL STREAK", f"{streak}", "DAYS UNBROKEN"), unsafe_allow_html=True)
        with c3: st.markdown(metric_card("TARGET DELTA", f"{round(curr-85,1)}", "KG TO GOAL"), unsafe_allow_html=True)
        with c4: 
            score = int(df.iloc[-1][['run_done','cold_shower','diet_strict']].mean()*100)
            st.markdown(metric_card("EFFICIENCY", f"{score}%", "DAILY RATING"), unsafe_allow_html=True)
            
        # CHARTS
        g1, g2 = st.columns([2, 1])
        
        with g1:
            st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">WEIGHT TRAJECTORY</div>', unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['date'], y=df['weight'], mode='lines', 
                fill='tozeroy', 
                line=dict(color='#8b5cf6', width=3), # Purple Line
                fillcolor='rgba(139, 92, 246, 0.1)',
                name='Weight'
            ))
            fig.add_trace(go.Scatter(x=[df['date'].min(), df['date'].max()], y=[85, 85], mode='lines', line=dict(dash='dash', color='#475569')))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                            margin=dict(t=20,l=0,r=0,b=0), height=350, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with g2:
            st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">HABIT DENSITY</div>', unsafe_allow_html=True)
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            sums = df[habits].sum().sort_values()
            fig2 = go.Figure(go.Bar(
                x=sums.values, y=[h.replace('_done','').replace('_',' ').upper() for h in sums.index], 
                orientation='h', marker=dict(color=sums.values, colorscale='Purples')
            ))
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                            margin=dict(t=20,l=0,r=0,b=0), height=350, xaxis=dict(showgrid=False))
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 3: DATA ARCHIVE
# ==========================================
with tab_history:
    if not df.empty:
        # HEATMAP
        st.markdown('<div class="hatom-card" style="padding:15px">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">CONSISTENCY MAP</div>', unsafe_allow_html=True)
        df['score'] = df[['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']].sum(axis=1)
        fig_cal = go.Figure(data=go.Heatmap(z=[df['score']], x=df['date'], y=[' '], colorscale='Purples', showscale=False))
        fig_cal.update_layout(template="plotly_dark", height=120, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=0,b=20), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_cal, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # EDITOR
        c_sel, c_edit = st.columns([1, 2])
        with c_sel:
            st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">SEARCH ARCHIVE</div>', unsafe_allow_html=True)
            edit_date = st.date_input("Select Date", datetime.today())
            record = df[df['date'] == pd.Timestamp(edit_date)]
            if not record.empty: st.markdown("<div style='color:#4ade80; font-weight:bold; margin-top:10px;'>● RECORD FOUND</div>", unsafe_allow_html=True)
            else: st.markdown("<div style='color:#64748b; font-weight:bold; margin-top:10px;'>○ NO DATA</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with c_edit:
            st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
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
                st.info("Select a valid date to edit.")
            st.markdown('</div>', unsafe_allow_html=True)
