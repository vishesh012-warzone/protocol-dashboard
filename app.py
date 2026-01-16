import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="The Protocol", page_icon="⚡", layout="wide")

# --- DATABASE CONNECTION ---
def get_db_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Try loading from Streamlit Cloud Secrets first (Production)
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    # Fallback to local JSON file (Development)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    
    client = gspread.authorize(creds)
    # CRITICAL: Ensure your sheet name matches exactly
    return client.open("protocol_db").sheet1 

# --- LOAD DATA ---
def load_data():
    sheet = get_db_connection()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
    return df

# --- UI LAYOUT ---
st.title("THE PROTOCOL ⚡")

tab1, tab2 = st.tabs(["📝 Log Entry", "📊 Dashboard"])

# --- TAB 1: WRITE DATA ---
with tab1:
    st.header("Daily Log")
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date_in = st.date_input("Date", datetime.today())
            weight_in = st.number_input("Weight (kg)", 80.0, 120.0, step=0.1, format="%.1f")
            notes_in = st.text_input("Notes")
        with col2:
            st.markdown("### Habits")
            c_run = st.checkbox("Run (20m)")
            c_lift = st.checkbox("Workout")
            c_cold = st.checkbox("Cold Shower")
            c_vac = st.checkbox("Vacuum")
            c_diet = st.checkbox("Diet (Eggs/Carbs)")
            c_junk = st.checkbox("No Junk")
        
        if st.form_submit_button("💾 Save to DB"):
            try:
                sheet = get_db_connection()
                # 1 = True, 0 = False
                row = [
                    date_in.strftime("%Y-%m-%d"), weight_in,
                    int(c_run), int(c_lift), int(c_cold), 
                    int(c_vac), int(c_diet), int(c_junk), 
                    7, notes_in # Default sleep score 7
                ]
                sheet.append_row(row)
                st.success("Log Saved!")
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 2: READ DATA ---
with tab2:
    try:
        df = load_data()
        if not df.empty:
            # METRICS
            curr_w = df['weight'].iloc[-1]
            start_w = df['weight'].iloc[0]
            
            # Streak Logic (Cold + Vacuum)
            streak = 0
            for i in range(len(df)-1, -1, -1):
                if int(df.iloc[i]['cold_shower']) == 1 and int(df.iloc[i]['vacuum']) == 1:
                    streak += 1
                else: break

            m1, m2, m3 = st.columns(3)
            m1.metric("Current Weight", f"{curr_w} kg", f"{round(curr_w - start_w, 1)} kg")
            m2.metric("🔥 Core Streak", f"{streak} Days", "Cold + Vacuum")
            m3.metric("Total Logs", len(df))
            
            # CHART
            fig = px.line(df, x='date', y='weight', title="Weight Trend")
            fig.add_hline(y=85, line_dash="dash", annotation_text="Target")
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df.sort_values('date', ascending=False))
    except Exception as e:
        st.info("No data found. Add an entry in Tab 1.")