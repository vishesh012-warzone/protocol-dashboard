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

# --- 2. DEEP SPACE UI (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    /* BLACK VOID THEME */
    .stApp {
        background-color: #000000;
        background-image: radial-gradient(circle at 50% 0%, #111 0%, #000 70%);
        font-family: 'Inter', sans-serif;
        color: #ffffff;
    }

    /* HIDE BLOAT */
    header {visibility: hidden;}
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 1200px;
    }

    /* GLASS CONTAINERS */
    .glass-container {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 24px;
        backdrop-filter: blur(12px);
        margin-bottom: 24px;
    }

    /* TYPOGRAPHY */
    h1 {
        font-weight: 200;
        font-size: 42px;
        letter-spacing: -2px;
        text-align: center;
        background: linear-gradient(180deg, #fff, #666);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        color: #444;
        font-size: 12px;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: -10px;
        margin-bottom: 40px;
    }

    /* INPUTS */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #0a0a0a !important;
        border: 1px solid #222 !important;
        color: #fff !important;
        border-radius: 8px !important;
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #222;
        gap: 30px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        color: #555;
    }
    .stTabs [aria-selected="true"] {
        color: #fff !important;
        border-bottom: 2px solid #fff;
    }

    /* SUCCESS BOX */
    .success-box {
        background: rgba(0, 255, 0, 0.05);
        border: 1px solid rgba(0, 255, 0, 0.2);
        color: #4ade80;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 20px;
        font-size: 14px;
    }
    
    /* BUTTONS */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 45px;
        font-weight: 600;
        background: #fff;
        color: #000;
        border: none;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.01);
        box-shadow: 0 0 20px rgba(255,255,255,0.2);
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
        st.error(f"🔌 Database Error: {e}")
        st.stop()

def load_data():
    try:
        sheet = get_db_connection()
        data = sheet.get_all_values()
        if len(data) < 2: return pd.DataFrame()
        
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)
        df = df[df['date'].astype(bool)] # Remove empty dates
        
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
st.markdown("<h1>PROTOCOL OS</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>System Status: Online</p>", unsafe_allow_html=True)

# Success Message Handler
if 'success_msg' in st.session_state:
    st.markdown(f"<div class='success-box'>{st.session_state['success_msg']}</div>", unsafe_allow_html=True)
    del st.session_state['success_msg']

# --- 5. TABS ---
tab_log, tab_dash, tab_history = st.tabs(["ENTRY LOG", "ANALYTICS", "HISTORY & EDIT"])

# ==========================================
# TAB 1: NEW ENTRY
# ==========================================
with tab_log:
    c_pad_l, c_main, c_pad_r = st.columns([1, 2, 1])
    with c_main:
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        with st.form("new_entry"):
            st.markdown("### NEW LOG")
            
            last_val = 94.0
            if not df.empty: last_val = float(df['weight'].iloc[-1])
            
            c1, c2 = st.columns(2)
            d_in = c1.date_input("Date", datetime.today())
            w_in = c2.number_input("Weight", value=last_val, step=0.1, format="%.1f")
            
            st.markdown("<br><b>HABITS</b>", unsafe_allow_html=True)
            h1, h2, h3 = st.columns(3)
            run = h1.checkbox("Running")
            vac = h1.checkbox("Vacuum")
            lift = h2.checkbox("Workout")
            diet = h2.checkbox("Diet")
            cold = h3.checkbox("Cold Shower")
            junk = h3.checkbox("No Junk")
            
            notes = st.text_area("Notes", height=80)
            
            if st.form_submit_button("COMMIT ENTRY"):
                try:
                    # DUPLICATE CHECK
                    if not df.empty and (df['date'] == pd.Timestamp(d_in)).any():
                        st.warning(f"⚠️ Data for {d_in} already exists. Go to 'HISTORY' to edit it.")
                    else:
                        sheet = get_db_connection()
                        row = [d_in.strftime("%Y-%m-%d"), w_in, int(run), int(lift), int(cold), int(vac), int(diet), int(junk), 7, str(notes)]
                        sheet.append_row(row)
                        st.session_state['success_msg'] = "✅ ENTRY SAVED"
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
        
        # HTML Metrics
        st.markdown('<div class="glass-container" style="padding:15px; display:flex; justify-content:space-around;">', unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center'><div style='color:#666; font-size:10px'>CURRENT</div><div style='font-size:24px; font-weight:bold'>{curr}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center'><div style='color:#666; font-size:10px'>TOTAL LOSS</div><div style='font-size:24px; font-weight:bold; color:#4ade80'>{round(curr-start,1)}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center'><div style='color:#666; font-size:10px'>TARGET</div><div style='font-size:24px; font-weight:bold; color:#666'>{round(curr-85,1)}</div></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['weight'], fill='tozeroy', line=dict(color='white', width=2), name='Weight'))
            fig.add_trace(go.Scatter(x=[df['date'].min(), df['date'].max()], y=[85, 85], line=dict(dash='dash', color='#444'), name='Goal'))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=0,l=0,r=0,b=0), height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with c2:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            sums = df[habits].sum().sort_values()
            fig2 = go.Figure(go.Bar(x=sums.values, y=[h.replace('_done','').upper() for h in sums.index], orientation='h', marker_color='white'))
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=0,l=0,r=0,b=0), height=300, xaxis=dict(showgrid=False))
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 3: HISTORY & EDIT (NEW!)
# ==========================================
with tab_history:
    if not df.empty:
        # 1. VISUAL CALENDAR (HEATMAP)
        st.markdown("##### 🗓️ LOG CALENDAR")
        
        # Prepare data for heatmap
        df['score'] = df[['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']].sum(axis=1)
        
        fig_cal = go.Figure(data=go.Heatmap(
            z=[df['score']],
            x=df['date'],
            y=['Intensity'],
            colorscale='Greys', # Deep space style
            showscale=False
        ))
        fig_cal.update_layout(
            template="plotly_dark", height=150, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=False, showticklabels=False), margin=dict(t=0,b=20)
        )
        st.plotly_chart(fig_cal, use_container_width=True)
        
        st.markdown("---")
        
        # 2. SELECT & EDIT INTERFACE
        c_sel, c_edit = st.columns([1, 2])
        
        with c_sel:
            st.markdown("##### 🖊️ SELECT ENTRY")
            # Select Date to Edit
            edit_date = st.date_input("Pick a date to view/edit", datetime.today())
            
            # Check if exists
            record = df[df['date'] == pd.Timestamp(edit_date)]
            exists = not record.empty
            
            if exists:
                st.markdown(f"<div style='color:#4ade80; margin-top:10px'>● LOG FOUND</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='color:#666; margin-top:10px'>○ NO DATA</div>", unsafe_allow_html=True)

        with c_edit:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            
            if exists:
                # PRE-FILL FORM WITH EXISTING DATA
                row = record.iloc[0]
                with st.form("edit_form"):
                    st.markdown(f"**EDITING: {edit_date.strftime('%b %d, %Y')}**")
                    
                    ew_in = st.number_input("Weight", value=float(row['weight']), step=0.1, format="%.1f")
                    
                    ec1, ec2, ec3 = st.columns(3)
                    er = ec1.checkbox("Running", value=bool(row['run_done']))
                    ev = ec1.checkbox("Vacuum", value=bool(row['vacuum']))
                    el = ec2.checkbox("Workout", value=bool(row['workout_done']))
                    ed = ec2.checkbox("Diet", value=bool(row['diet_strict']))
                    ec = ec3.checkbox("Cold Shower", value=bool(row['cold_shower']))
                    ej = ec3.checkbox("No Junk", value=bool(row['no_junk']))
                    
                    en = st.text_area("Notes", value=str(row['notes']), height=80)
                    
                    if st.form_submit_button("UPDATE ENTRY"):
                        try:
                            sheet = get_db_connection()
                            # FIND ROW TO UPDATE (Crucial Step)
                            # We search for the date string in the first column
                            cell = sheet.find(edit_date.strftime("%Y-%m-%d"))
                            if cell:
                                r_idx = cell.row
                                new_vals = [
                                    edit_date.strftime("%Y-%m-%d"), ew_in, 
                                    int(er), int(el), int(ec), int(ev), int(ed), int(ej), 7, str(en)
                                ]
                                # Update that specific range
                                sheet.update(range_name=f"A{r_idx}:J{r_idx}", values=[new_vals])
                                st.session_state['success_msg'] = f"✅ UPDATED {edit_date}"
                                st.cache_data.clear()
                                st.rerun()
                        except Exception as e:
                            st.error(f"Update failed: {e}")
            else:
                st.info(f"No entry exists for {edit_date}. Go to 'ENTRY LOG' to create one.")
                
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("No data available.")
