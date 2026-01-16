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

# --- 2. THE PARALLAX ENGINE (FIXED) ---
# We inject a specific HTML container for the background and move IT, not the body.
st.markdown("""
<style>
    /* 1. HIDE DEFAULT STREAMLIT BACKGROUNDS */
    .stApp {
        background: transparent !important;
    }
    header, footer {visibility: hidden !important;}
    
    /* 2. THE PARALLAX WRAPPER */
    #parallax-bg {
        position: fixed;
        top: -10%;
        left: -10%;
        width: 120%;
        height: 120%;
        z-index: -1;
        background-image: url('https://images.unsplash.com/photo-1534796636912-3b95b3ab5980?q=80&w=2672&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        filter: brightness(0.7) contrast(1.2) hue-rotate(10deg);
        transition: transform 0.1s ease-out;
        pointer-events: none;
    }
    
    /* 3. VIGNETTE OVERLAY (To make text readable) */
    #overlay {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: radial-gradient(circle at center, transparent 0%, #02040a 90%);
        z-index: -1;
        pointer-events: none;
    }

    /* 4. HATOM UI SYSTEM */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;500;600&display=swap');
    
    .block-container {
        padding-top: 4rem;
        max-width: 1400px;
    }

    /* GLASS CARDS */
    .hatom-card {
        background: rgba(13, 17, 28, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 30px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        margin-bottom: 24px;
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .hatom-card:hover {
        border-color: rgba(139, 92, 246, 0.5);
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }

    /* TYPOGRAPHY */
    h1, h2, h3 { font-family: 'Outfit', sans-serif; color: #fff; }
    
    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 72px;
        background: linear-gradient(180deg, #fff 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -3px;
        line-height: 1;
        text-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    /* INPUTS */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #fff !important;
        padding: 15px !important;
        backdrop-filter: blur(5px);
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #8b5cf6 !important;
        background-color: rgba(139, 92, 246, 0.1) !important;
    }

    /* BUTTONS */
    .stButton > button {
        width: 100%;
        height: 60px;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        border: none;
        border-radius: 16px;
        color: white;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 30px rgba(139, 92, 246, 0.6);
    }

    /* SUCCESS BOX */
    .hatom-success {
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #6ee7b7;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
        font-weight: 600;
    }
    
    /* METRICS */
    .metric-val {
        font-family: 'Outfit', sans-serif;
        font-size: 48px;
        font-weight: 700;
        color: #fff;
    }
    .metric-lbl {
        color: #94a3b8;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
</style>

<div id="parallax-bg"></div>
<div id="overlay"></div>

<script>
    // TRACK MOUSE MOVEMENT AND MOVE THE #parallax-bg ELEMENT
    document.addEventListener('mousemove', function(e) {
        const bg = document.getElementById('parallax-bg');
        const x = (window.innerWidth - e.pageX * 2) / 50; // Strength of movement
        const y = (window.innerHeight - e.pageY * 2) / 50;
        
        bg.style.transform = `translateX(${x}px) translateY(${y}px) scale(1.1)`;
    });
</script>
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

# --- 4. HEADER ---
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown('<div class="hero-title">PROTOCOL OS</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div style="text-align:right; padding-top:30px; color:#94a3b8; letter-spacing:1px; font-family:Outfit">SYSTEM: <b style="color:#4ade80">ONLINE</b></div>', unsafe_allow_html=True)

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

if 'success_msg' in st.session_state:
    st.markdown(f"<div class='hatom-success'>{st.session_state['success_msg']}</div>", unsafe_allow_html=True)
    del st.session_state['success_msg']

# --- 5. TABS ---
tab_log, tab_dash, tab_history = st.tabs(["ENTRY TERMINAL", "ANALYTICS HUB", "DATA ARCHIVE"])

# ==========================================
# TAB 1: ENTRY
# ==========================================
with tab_log:
    c_pad_l, c_main, c_pad_r = st.columns([1, 2, 1])
    with c_main:
        st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
        with st.form("entry_form"):
            last_val = 94.0
            if not df.empty: last_val = float(df['weight'].iloc[-1])
            
            st.markdown("### NEW ENTRY LOG")
            c1, c2 = st.columns(2)
            d_in = c1.date_input("Date", datetime.today())
            w_in = c2.number_input("Weight (kg)", value=last_val, step=0.1, format="%.1f")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### PROTOCOLS")
            
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
            notes = st.text_area("Notes", height=80, placeholder="Session details...")
            
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
# TAB 2: ANALYTICS
# ==========================================
with tab_dash:
    if not df.empty:
        curr = df['weight'].iloc[-1]
        start = df['weight'].iloc[0]
        
        c1, c2, c3, c4 = st.columns(4)
        
        def card(lbl, val, sub):
            return f"""
            <div class="hatom-card" style="text-align:center; padding:20px;">
                <div class="metric-lbl">{lbl}</div>
                <div class="metric-val">{val}</div>
                <div style="font-size:12px; color:#64748b;">{sub}</div>
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
            
        # CHARTS
        g1, g2 = st.columns([2, 1])
        
        with g1:
            st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
            st.markdown("### TRAJECTORY")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['weight'], mode='lines', fill='tozeroy', 
                                   line=dict(color='#8b5cf6', width=3), 
                                   fillcolor='rgba(139, 92, 246, 0.1)'))
            fig.add_trace(go.Scatter(x=[df['date'].min(), df['date'].max()], y=[85, 85], mode='lines', line=dict(dash='dash', color='#64748b')))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                            margin=dict(t=20,l=0,r=0,b=0), height=350, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with g2:
            st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
            st.markdown("### HABITS")
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            sums = df[habits].sum().sort_values()
            fig2 = go.Figure(go.Bar(x=sums.values, y=[h.replace('_done','').replace('_',' ').upper() for h in sums.index], 
                                  orientation='h', marker=dict(color=sums.values, colorscale='Purples')))
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                            margin=dict(t=20,l=0,r=0,b=0), height=350, xaxis=dict(showgrid=False))
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 3: ARCHIVE
# ==========================================
with tab_history:
    if not df.empty:
        # HEATMAP
        st.markdown('<div class="hatom-card" style="padding:15px">', unsafe_allow_html=True)
        df['score'] = df[['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']].sum(axis=1)
        fig_cal = go.Figure(data=go.Heatmap(z=[df['score']], x=df['date'], y=[' '], colorscale='Purples', showscale=False))
        fig_cal.update_layout(template="plotly_dark", height=100, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=0,b=20), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_cal, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # EDITOR
        c_sel, c_edit = st.columns([1, 2])
        with c_sel:
            st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
            st.markdown("### SEARCH")
            edit_date = st.date_input("Select Date", datetime.today())
            record = df[df['date'] == pd.Timestamp(edit_date)]
            if not record.empty: st.markdown("<b style='color:#4ade80'>● RECORD FOUND</b>", unsafe_allow_html=True)
            else: st.markdown("<b style='color:#64748b'>○ NO DATA</b>", unsafe_allow_html=True)
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
                st.info("Select a date to edit.")
            st.markdown('</div>', unsafe_allow_html=True)
