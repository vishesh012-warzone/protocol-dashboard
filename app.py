import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & CUSTOM CSS (THE "AMAZON" LOOK) ---
st.set_page_config(page_title="THE PROTOCOL | PRO", page_icon="⚡", layout="wide")

# Custom CSS for "Cyberpunk/Professional" Look
st.markdown("""
<style>
    /* Main Background & Text */
    .stApp {
        background-color: #0e1117;
        color: #FAFAFA;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: scale(1.02);
        border-color: #00FFAA;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        background-color: #262730;
        color: white;
        border-radius: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1E1E1E;
        border-radius: 8px;
        color: white;
        border: 1px solid #333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00FFAA !important;
        color: black !important;
        font-weight: bold;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: black;
        font-weight: bold;
        border: none;
        height: 50px;
        border-radius: 8px;
    }
    .stButton > button:hover {
        box-shadow: 0 0 15px #00FFAA;
        color: black;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. ROBUST DATABASE CONNECTION ---
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

# --- 3. DATA LOADER (SMART CACHING) ---
def load_data():
    try:
        sheet = get_db_connection()
        # Get all records ensures we don't get empty rows if the sheet is clean
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
            
            # Clean Boolean Columns
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            for col in habits:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.upper().replace({'TRUE': '1', 'FALSE': '0', '1': '1', '0': '0'})
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Sort by date descending (Newest first)
            df = df.sort_values('date', ascending=False)
        return df
    except Exception as e:
        return pd.DataFrame()

# Load Data Once
df = load_data()

# --- 4. UI LAYOUT ---
st.title("THE PROTOCOL ⚡")

# Tabs for Navigation
tab_log, tab_analytics, tab_history = st.tabs(["📝 Daily Log", "📈 Analytics Hub", "📅 History & Edit"])

# ==========================================
# TAB 1: SMART LOGGING (Fixes "Default 70kg")
# ==========================================
with tab_log:
    st.markdown("### 🚀 Log Today's Battle")
    
    # Get Last Weight for Smart Default
    last_weight = 94.0 # Fallback
    if not df.empty:
        last_weight = float(df['weight'].iloc[0]) # Get the most recent weight

    with st.form("entry_form", clear_on_submit=False):
        c1, c2, c3 = st.columns([1,1,2])
        
        with c1:
            date_in = st.date_input("Date", datetime.today())
            # FIX: Default value is now your LAST logged weight
            weight_in = st.number_input("Weight (kg)", value=last_weight, step=0.1, format="%.1f")
        
        with c2:
            st.markdown("#### 🛡️ Morning")
            run = st.checkbox("Run (20m)")
            lift = st.checkbox("Workout")
            cold = st.checkbox("Cold Shower")
            vac = st.checkbox("Vacuum")
        
        with c3:
            st.markdown("#### 🍗 Nutrition")
            diet = st.checkbox("Protein Target Hit")
            junk = st.checkbox("No Junk Food")
            notes = st.text_area("Notes", placeholder="How was the energy?", height=68)

        # Huge Save Button
        submit_btn = st.form_submit_button("💾 COMMIT LOG")

        if submit_btn:
            try:
                sheet = get_db_connection()
                row_data = [
                    date_in.strftime("%Y-%m-%d"), weight_in,
                    int(run), int(lift), int(cold), int(vac), int(diet), int(junk), 
                    7, str(notes)
                ]
                
                # Check if entry exists for this date (Prevents duplicates)
                if not df.empty and (df['date'] == pd.Timestamp(date_in)).any():
                    st.warning("⚠️ You already logged for this date. Go to 'History' to edit.")
                else:
                    sheet.append_row(row_data)
                    st.success("✅ Data Secured.")
                    st.cache_data.clear() # Refresh data
            except Exception as e:
                st.error(f"Error: {e}")

# ==========================================
# TAB 2: PRO ANALYTICS (Filters & Calendar)
# ==========================================
with tab_analytics:
    if not df.empty:
        # --- TIME FILTER ---
        st.markdown("### 📊 Performance Center")
        time_range = st.selectbox("Select Timeframe", ["Last 7 Days", "Last 30 Days", "All Time"], index=1)
        
        # Filter Logic
        df_filtered = df.copy()
        if time_range == "Last 7 Days":
            df_filtered = df[df['date'] >= (datetime.now() - timedelta(days=7))]
        elif time_range == "Last 30 Days":
            df_filtered = df[df['date'] >= (datetime.now() - timedelta(days=30))]

        # --- KPI ROW ---
        # Calculate Metrics
        curr_w = df_filtered['weight'].iloc[0]
        start_w = df_filtered['weight'].iloc[-1]
        delta = curr_w - start_w
        
        # Streak (Cold + Vacuum)
        streak = 0
        for i in range(len(df)):
            if df.iloc[i]['cold_shower'] == 1 and df.iloc[i]['vacuum'] == 1:
                streak += 1
            else:
                break

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Current Weight", f"{curr_w} kg", f"{round(delta, 1)} kg", delta_color="inverse")
        k2.metric("Protocol Streak", f"{streak} Days", "Cold + Vacuum")
        k3.metric("Goal Distance", f"{round(curr_w - 85.0, 1)} kg", "Target: 85kg")
        k4.metric("Days Tracked", len(df), "Total Logs")

        st.divider()

        # --- CHARTS ---
        g1, g2 = st.columns([2,1])
        
        with g1:
            # 1. WEIGHT TREND (Plotly Dark Template)
            fig_w = go.Figure()
            fig_w.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['weight'], 
                                     mode='lines+markers', name='Weight',
                                     line=dict(color='#00FFAA', width=4)))
            fig_w.add_hline(y=85, line_dash="dash", line_color="white", annotation_text="Target 85kg")
            fig_w.update_layout(title="Weight Trajectory", template="plotly_dark", 
                              paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400)
            st.plotly_chart(fig_w, use_container_width=True)

        with g2:
            # 2. HABIT RADAR (Consistency)
            habits = ['run_done', 'workout_done', 'cold_shower', 'vacuum', 'diet_strict', 'no_junk']
            habit_sums = df_filtered[habits].sum()
            
            fig_h = px.bar(x=habit_sums.values, y=habit_sums.index, orientation='h',
                         color=habit_sums.values, color_continuous_scale='Teal')
            fig_h.update_layout(title="Habit Consistency", template="plotly_dark",
                              paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                              xaxis_title=None, yaxis_title=None, height=400)
            st.plotly_chart(fig_h, use_container_width=True)

        # 3. CALENDAR HEATMAP (The "Calendar Form" you asked for)
        st.subheader("🗓️ Consistency Calendar")
        # Creating a simple heatmap
        df_cal = df.copy()
        df_cal['score'] = df_cal[habits].mean(axis=1)
        
        fig_cal = px.scatter(df_cal, x='date', y='score', color='score', 
                           size='score', color_continuous_scale='Greens',
                           title="Daily Discipline Score (Bubble Chart)")
        fig_cal.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_cal, use_container_width=True)

    else:
        st.info("No data yet. Go to 'Daily Log' to start.")

# ==========================================
# TAB 3: DATA EDITOR (Edit Past Entries)
# ==========================================
with tab_history:
    st.markdown("### 🗂️ Manage Your Data")
    st.markdown("To edit, double click a cell below. **Changes in this table are visual only for now.** To permanently delete rows, use Google Sheets.")
    
    if not df.empty:
        # Streamlit Data Editor - Interactive Table
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            column_config={
                "weight": st.column_config.NumberColumn("Weight", format="%.1f kg"),
                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "run_done": st.column_config.CheckboxColumn("Run"),
                "workout_done": st.column_config.CheckboxColumn("Lift"),
            },
            use_container_width=True,
            height=600
        )
        st.caption("Note: For deep editing (deleting rows), use the database directly.")
