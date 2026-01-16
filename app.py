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

# --- 2. HATOM "LIQUID CYBERPUNK" DESIGN SYSTEM ---
st.markdown("""
<style>
    /* IMPORT FONTS: Inter (Clean UI) & Outfit (Headings) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Outfit:wght@400;600;800&display=swap');

    /* --- GLOBAL THEME --- */
    .stApp {
        background-color: #02040a; /* Deepest Void */
        /* Hatom-style deep radial glow */
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(37, 99, 235, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 90% 90%, rgba(6, 182, 212, 0.05) 0%, transparent 40%);
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }

    /* REMOVE STREAMLIT PADDING */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 1400px;
    }
    header {visibility: hidden;}

    /* --- GLASS CONTAINERS (The Hatom Look) --- */
    .hatom-card {
        background: rgba(15, 23, 42, 0.4); /* Dark Blue Tint */
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 30px;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5);
        margin-bottom: 24px;
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .hatom-card:hover {
        border-color: rgba(6, 182, 212, 0.3); /* Cyan Glow on Hover */
        transform: translateY(-2px);
    }

    /* --- TYPOGRAPHY --- */
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        color: #fff;
    }
    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 56px;
        background: linear-gradient(135deg, #fff 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1.5px;
        line-height: 1.1;
    }
    .section-header {
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 15px;
    }

    /* --- INPUT FIELDS (Modern & Sleek) --- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(2, 6, 23, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #fff !important;
        padding: 16px !important;
        font-family: 'Inter', sans-serif;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #3b82f6 !important; /* Blue Focus */
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
    }

    /* --- BUTTONS (Glowing Gradient) --- */
    .stButton > button {
        width: 100%;
        height: 55px;
        background: linear-gradient(90deg, #2563eb 0%, #06b6d4 100%);
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        font-family: 'Outfit', sans-serif;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        box-shadow: 0 0 30px rgba(6, 182, 212, 0.4);
        transform: scale(1.02);
    }

    /* --- TABS (Pill Style) --- */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 23, 42, 0.5);
        padding: 8px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.05);
        gap: 10px;
        display: inline-flex;
    }
    .stTabs [data-baseweb="tab"] {
        border: none;
        color: #94a3b8;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.1);
        color: #fff !important;
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none; /* Hide standard underline */
    }

    /* --- CUSTOM CHECKBOX --- */
    .stCheckbox label span {
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        color: #cbd5e1;
    }

    /* --- SUCCESS NOTIFICATION --- */
    .hatom-success {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        color: #34d399;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }

    /* --- METRICS --- */
    .metric-val {
        font-family: 'Outfit', sans-serif;
        font-size: 42px;
        font-weight: 700;
        background: linear-gradient(180deg, #fff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-lbl {
        color: #64748b;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .metric-sub {
        font-size: 13px;
        color: #3b82f6; /* Hatom Blue */
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. BACKEND CONNECTION (Unchanged Logic) ---
def get_db_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("warrior_db").sheet1
    except Exception as e:
        st.error(f"System Disconnected: {e}")
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
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown('<div class="hero-title">PROTOCOL OS</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div style="text-align:right; padding-top:15px; color:#64748b; font-family:Outfit; letter-spacing:1px;">SYSTEM: <b>ONLINE</b></div>', unsafe_allow_html=True)

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

if 'success_msg' in st.session_state:
    st.markdown(f"<div class='hatom-success'>{st.session_state['success_msg']}</div>", unsafe_allow_html=True)
    del st.session_state['success_msg']

# --- 5. TABS ---
tab_log, tab_dash, tab_history = st.tabs(["ENTRY TERMINAL", "ANALYTICS DASHBOARD", "ARCHIVE"])

# ==========================================
# TAB 1: THE INPUT CARD
# ==========================================
with tab_log:
    # Centered Layout
    c_left, c_center, c_right = st.columns([1, 2, 1])
    
    with c_center:
        st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">/// NEW DATA ENTRY</div>', unsafe_allow_html=True)
        
        with st.form("entry_form"):
            last_val = 94.0
            if not df.empty: last_val = float(df['weight'].iloc[-1])
            
            c1, c2 = st.columns(2)
            d_in = c1.date_input("Date", datetime.today())
            w_in = c2.number_input("Weight (kg)", value=last_val, step=0.1, format="%.1f")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">/// HABIT CHECKLIST</div>', unsafe_allow_html=True)
            
            h1, h2 = st.columns(2)
            with h1:
                run = st.checkbox("Running (20m)")
                vac = st.checkbox("Stomach Vacuum")
                lift = st.checkbox("Workout / Lift")
            with h2:
                diet = st.checkbox("Diet Adherence")
                cold = st.checkbox("Cold Shower")
                junk = st.checkbox("No Junk Food")
            
            st.markdown("<br>", unsafe_allow_html=True)
            notes = st.text_area("Log Notes", height=80, placeholder="Energy levels, sleep quality, etc...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("COMMIT TO DATABASE"):
                try:
                    if not df.empty and (df['date'] == pd.Timestamp(d_in)).any():
                        st.warning("Entry already exists for this date.")
                    else:
                        sheet = get_db_connection()
                        row = [d_in.strftime("%Y-%m-%d"), w_in, int(run), int(lift), int(cold), int(vac), int(diet), int(junk), 7, str(notes)]
                        sheet.append_row(row)
                        st.session_state['success_msg'] = "LOG SAVED SUCCESSFULLY"
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 2: ANALYTICS (HATOM STYLE)
# ==========================================
with tab_dash:
    if not df.empty:
        curr = df['weight'].iloc[-1]
        start = df['weight'].iloc[0]
        
        # 1. METRICS GRID
        c1, c2, c3, c4 = st.columns(4)
        
        def card(label, val, sub):
            return f"""
            <div class="hatom-card" style="padding: 20px; text-align: center;">
                <div class="metric-lbl">{label}</div>
                <div class="metric-val">{val}</div>
                <div class="metric-sub">{sub}</div>
            </div>
            """
        
        streak = 0
        for i in range(len(df)-1, -1, -1):
            if df.iloc[i]['cold_shower'] == 1 and df.iloc[i]['vacuum'] == 1: streak += 1
            else: break
            
        with c1: st.markdown(card("Current Weight", curr, f"{round(curr-start,1)} KG Total"), unsafe_allow_html=True)
        with c2: st.markdown(card("Protocol Streak", streak, "Days Active"), unsafe_allow_html=True)
        with c3: st.markdown(card("To Goal", round(curr-85,1), "KG Remaining"), unsafe_allow_html=True)
        with c4: 
            score = int(df.iloc[-1][['run_done','cold_shower','diet_strict']].mean()*100)
            st.markdown(card("Daily Score", f"{score}%", "Discipline Rating"), unsafe_allow_html=True)

        # 2. CHARTS (Glowing Gradients)
        g1, g2 = st.columns([2, 1])
        
        with g1:
            st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">WEIGHT TRAJECTORY</div>', unsafe_allow_html=True)
            fig = go.Figure()
            # Area with Gradient Fill
            fig.add_trace(go.Scatter(
                x=df['date'], y=df['weight'], mode='lines', 
                fill='tozeroy', 
                line=dict(color='#06b6d4', width=3), # Cyan Line
                name='Weight'
            ))
            # Target
            fig.add_trace(go.Scatter(
                x=[df['date'].min(), df['date'].max()], y=[85, 85], 
                mode='lines', line=dict(dash='dash', color='#475569')
            ))
            fig.update_layout(
                template="plotly_dark", 
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=20,l=0,r=0,b=0), height=350,
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with g2:
            st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">HABIT DNA</div>', unsafe_allow_html=True)
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            sums = df[habits].sum().sort_values()
            
            fig2 = go.Figure(go.Bar(
                x=sums.values, 
                y=[h.replace('_done','').replace('_',' ').upper() for h in sums.index], 
                orientation='h', 
                marker=dict(color=sums.values, colorscale='Cyan') # Hatom Cyan scale
            ))
            fig2.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=20,l=0,r=0,b=0), height=350, xaxis=dict(showgrid=False),
                yaxis=dict(tickfont=dict(size=10, family='Inter'))
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 3: HISTORY (Clean List)
# ==========================================
with tab_history:
    if not df.empty:
        # Heatmap Strip
        st.markdown('<div class="hatom-card" style="padding:15px">', unsafe_allow_html=True)
        df['score'] = df[['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']].sum(axis=1)
        fig_cal = go.Figure(data=go.Heatmap(
            z=[df['score']], x=df['date'], y=[' '], 
            colorscale=[[0, '#0f172a'], [1, '#06b6d4']], # Dark Blue to Cyan
            showscale=False
        ))
        fig_cal.update_layout(template="plotly_dark", height=100, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            margin=dict(t=0,b=20), xaxis=dict(showgrid=False))
        st.plotly_chart(fig_cal, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Editor
        c_sel, c_edit = st.columns([1, 2])
        with c_sel:
            st.markdown('<div class="hatom-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">SELECT ENTRY</div>', unsafe_allow_html=True)
            edit_date = st.date_input("Search Date", datetime.today())
            record = df[df['date'] == pd.Timestamp(edit_date)]
            if not record.empty: st.markdown(">> RECORD FOUND", unsafe_allow_html=True)
            else: st.markdown(">> NO DATA", unsafe_allow_html=True)
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
                                st.session_state['success_msg'] = "DATABASE UPDATED"
                                st.cache_data.clear()
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.info("Select a date with existing data to edit.")
            st.markdown('</div>', unsafe_allow_html=True)
