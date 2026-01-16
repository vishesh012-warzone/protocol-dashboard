import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="The Protocol", page_icon="⚡", layout="wide")

# --- DATABASE CONNECTION (MODERN AUTH) ---
def get_db_connection():
    # 1. Define the correct permissions (Scopes)
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        # 2. Authenticate using Streamlit Secrets
        # (This reads the [gcp_service_account] section from your Streamlit Cloud settings)
        credentials_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # 3. Open the specific Google Sheet
        # Make sure your actual Google Sheet file in Drive is named "warrior_db" exactly.
        return client.open("warrior_db").sheet1 
        
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        st.info("Check your Streamlit Secrets or ensure your Google Sheet is named 'warrior_db'.")
        st.stop()

# --- LOAD DATA FUNCTION (FIXED) ---
def load_data():
    try:
        sheet = get_db_connection()
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty:
            # 1. Fix Date Format
            df['date'] = pd.to_datetime(df['date'])
            
            # 2. Fix Weight (Force to number)
            df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
            
            # 3. FIX HABIT COLUMNS (The Crash Fix)
            # Google Sheets sometimes sends "TRUE"/"FALSE" as text. We must force them to 1/0.
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            for col in habits:
                if col in df.columns:
                    # Convert everything to string first, uppercase it, then map to 1/0
                    df[col] = df[col].astype(str).str.upper()
                    df[col] = df[col].replace({'TRUE': '1', 'FALSE': '0', '1': '1', '0': '0'})
                    # Finally, force to numeric
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    
        return df
    except Exception as e:
        # If error, return empty dataframe so app doesn't crash
        return pd.DataFrame()

# --- UI LAYOUT ---
st.title("THE PROTOCOL ⚡")

# Two tabs: One for entering data, one for viewing results
tab1, tab2 = st.tabs(["📝 Log Entry", "📊 Analytics"])

# ==========================================
# TAB 1: DATA ENTRY (Write to Sheet)
# ==========================================
with tab1:
    st.header("Daily Log")
    
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date_in = st.date_input("Date", datetime.today())
            weight_in = st.number_input("Weight (kg)", min_value=70.0, max_value=150.0, step=0.1, format="%.1f")
            notes_in = st.text_input("Notes", placeholder="How did the run feel?")
            
        with col2:
            st.markdown("### Habits")
            c_run = st.checkbox("Run (20m)")
            c_lift = st.checkbox("Workout (Pushups)")
            c_cold = st.checkbox("Cold Shower")
            c_vac = st.checkbox("Vacuum")
            c_diet = st.checkbox("Diet (Eggs/Carbs)")
            c_junk = st.checkbox("No Junk Food")
        
        submitted = st.form_submit_button("💾 Save Log")

        if submitted:
            try:
                sheet = get_db_connection()
                
                # Format the data for Google Sheets
                # (1 = Checked, 0 = Unchecked)
                row_data = [
                    date_in.strftime("%Y-%m-%d"), 
                    weight_in,
                    int(c_run), 
                    int(c_lift), 
                    int(c_cold), 
                    int(c_vac), 
                    int(c_diet), 
                    int(c_junk), 
                    7, # Default sleep score placeholder
                    str(notes_in)
                ]
                
                # Append row to the Google Sheet
                sheet.append_row(row_data)
                
                st.success("✅ Log Saved Successfully!")
                st.cache_data.clear() # Reset cache so analytics update immediately
                
            except Exception as e:
                st.error(f"Error saving data: {e}")

# ==========================================
# TAB 2: ANALYTICS (Read from Sheet)
# ==========================================
with tab2:
    df = load_data()
    
    if not df.empty:
        # --- CALCULATIONS ---
        curr_w = df['weight'].iloc[-1]
        start_w = df['weight'].iloc[0]
        
        # Calculate Streak (Cold Shower + Vacuum)
        streak = 0
        for i in range(len(df)-1, -1, -1):
            # Check if both columns exist and are true (1)
            try:
                cold = int(df.iloc[i]['cold_shower'])
                vac = int(df.iloc[i]['vacuum'])
                if cold == 1 and vac == 1:
                    streak += 1
                else:
                    break
            except:
                break

        # --- KEY METRICS ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Current Weight", f"{curr_w} kg", f"{round(curr_w - start_w, 1)} kg", delta_color="inverse")
        m2.metric("🔥 Core Streak", f"{streak} Days", "Cold + Vacuum")
        m3.metric("Total Logs", len(df))
        
        st.divider()
        
        # --- CHARTS ---
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("Weight Trend")
            fig = px.line(df, x='date', y='weight', markers=True)
            # Add a goal line at 85kg
            fig.add_hline(y=85, line_dash="dash", line_color="green", annotation_text="Goal: 85kg")
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.subheader("Habit Consistency")
            # Calculate sums of all habits
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            # Ensure columns exist before summing
            existing_habits = [h for h in habits if h in df.columns]
            if existing_habits:
                sums = df[existing_habits].sum().sort_values()
                st.bar_chart(sums)

        # --- DATA TABLE ---
        with st.expander("📂 View Raw Data"):
            st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)
            
    else:
        st.info("No data found yet. Go to 'Log Entry' tab to add your first day!")

