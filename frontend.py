import streamlit as st
import datetime as dt
import requests
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Medilink Plus | Care Coordinator Portal",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Apply Font */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Custom Header styling */
    .dashboard-header {
        background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(13, 148, 136, 0.2);
    }
    .dashboard-header h1 {
        margin: 0;
        font-size: 2.25rem;
        font-weight: 700;
    }
    .dashboard-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
    }

    /* Metric Cards */
    .metric-box {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 1.25rem;
        border-left: 5px solid #0d9488;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .metric-box:hover {
        transform: translateY(-2px);
    }
    
    /* Badge styling */
    .status-badge {
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-active {
        background-color: #d1fae5;
        color: #065f46;
    }
    .status-canceled {
        background-color: #fee2e2;
        color: #991b1b;
    }
    
    /* Appointment list row */
    .appt-row {
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar layout
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <span style="font-size: 2.5rem;">🩺</span>
            <div>
                <h2 style="margin: 0; font-size: 1.5rem; color: #0f766e;">Medilink Plus</h2>
                <small style="color: #64748b;">Care Coordinator Portal</small>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    page = st.radio(
        "Navigation",
        ["📊 Dashboard & Analytics", "📋 Appointment Directory", "📅 Schedule Appointment", "🚫 Bulk Cancellations"],
        index=0
    )
    
    st.divider()
    
    with st.expander("⚙️ Connection Settings"):
        base_url = st.text_input("Backend URL", "http://localhost:4444").rstrip("/")

# Render selected page
if page == "📊 Dashboard & Analytics":
    st.markdown("""
        <div class="dashboard-header">
            <h1>Medilink Dashboard</h1>
            <p>Real-time analytics and clinic workload management.</p>
        </div>
    """, unsafe_allow_html=True)

    # Fetch stats
    try:
        resp = requests.get(f"{base_url}/dashboard/stats", timeout=10)
        resp.raise_for_status()
        stats = resp.json()
    except Exception as e:
        st.error(f"Could not load statistics from backend. Please verify your connection settings. (Error: {e})")
        stats = None

    if stats:
        # Metrics cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Bookings", stats["total_bookings"])
        with col2:
            st.metric("Active Appointments", stats["active_bookings"])
        with col3:
            st.metric("Canceled Appointments", stats["canceled_bookings"])
        with col4:
            st.metric("Cancellation Rate", f"{stats['cancellation_rate']}%")

        st.divider()

        # Graphs and Charts
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("🩺 Appointments by Reason")
            if stats["reasons"]:
                df_reasons = pd.DataFrame(list(stats["reasons"].items()), columns=["Reason", "Count"])
                df_reasons = df_reasons.sort_values(by="Count", ascending=False)
                st.bar_chart(df_reasons.set_index("Reason"), color="#0d9488")
            else:
                st.info("No appointment reasons database yet.")

        with col_right:
            st.subheader("⏰ Peak Booking Hours")
            if stats["hourly_distribution"]:
                df_hourly = pd.DataFrame([{"Hour": f"{int(h):02d}:00", "Bookings": count} for h, count in stats["hourly_distribution"].items()])
                df_hourly = df_hourly.sort_values("Hour")
                st.bar_chart(df_hourly.set_index("Hour"), color="#0f766e")
            else:
                st.info("No hourly booking data available.")

        st.subheader("📈 Appointment Scheduling Activity")
        if stats["daily_distribution"]:
            df_daily = pd.DataFrame(list(stats["daily_distribution"].items()), columns=["Date", "Bookings"])
            df_daily = df_daily.sort_values("Date")
            st.area_chart(df_daily.set_index("Date"), color="#0d9488")
        else:
            st.info("No scheduling history available.")

        st.divider()
        
        # Today's Timeline
        st.subheader("📅 Today's Active Schedule")
        today = dt.date.today()
        try:
            today_resp = requests.get(
                f"{base_url}/dashboard/appointments",
                params={"start_date": today.isoformat(), "end_date": today.isoformat(), "include_canceled": "false"},
                timeout=10
            )
            today_resp.raise_for_status()
            today_appts = today_resp.json()
            
            if today_appts:
                for appt in today_appts:
                    t_parsed = dt.datetime.fromisoformat(appt["start_time"])
                    time_str = t_parsed.strftime("%I:%M %p")
                    st.markdown(f"**⏰ {time_str}** | 👤 {appt['patient_name']} | 💬 Reason: {appt['reason'] or 'N/A'}")
            else:
                st.info("No appointments scheduled for today.")
        except Exception as e:
            st.warning("Failed to fetch today's appointments timeline.")

elif page == "📋 Appointment Directory":
    st.markdown("""
        <div class="dashboard-header">
            <h1>Appointment Directory</h1>
            <p>Search, filter, and manage clinic patient schedules.</p>
        </div>
    """, unsafe_allow_html=True)

    # Directory Filters
    col_s1, col_s2, col_s3, col_s4 = st.columns([2, 1, 1, 1])
    with col_s1:
        search_query = st.text_input("🔍 Search Patient Name", placeholder="Type patient name to search...")
    with col_s2:
        status_filter = st.selectbox("Status", ["All", "Active Only", "Canceled Only"])
    with col_s3:
        start_date = st.date_input("Start Date", value=None)
    with col_s4:
        end_date = st.date_input("End Date", value=None)

    view_mode = st.radio("View Style", ["Interactive List", "Data Table (Exportable)"], horizontal=True)

    # Fetch and filter appointments
    params = {}
    if search_query:
        params["patient_name"] = search_query
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()

    appointments = []
    try:
        resp = requests.get(f"{base_url}/dashboard/appointments", params=params, timeout=10)
        resp.raise_for_status()
        appointments = resp.json()
        
        # Apply Status Filter in Python
        if status_filter == "Active Only":
            appointments = [a for a in appointments if not a["canceled"]]
        elif status_filter == "Canceled Only":
            appointments = [a for a in appointments if a["canceled"]]
            
    except Exception as e:
        st.error(f"Could not load directory data: {e}")

    if not appointments:
        st.info("No appointments found matching the selected search parameters.")
    else:
        st.write(f"Showing **{len(appointments)}** matches")
        
        if view_mode == "Interactive List":
            st.markdown("""
                <div style="font-weight: 600; padding: 0.5rem 1rem; background-color: #f1f5f9; border-radius: 6px; margin-bottom: 0.5rem;">
                    <div style="display: grid; grid-template-columns: 2fr 2fr 2fr 1fr 1fr; gap: 10px;">
                        <div>Patient Name</div>
                        <div>Reason / Symptoms</div>
                        <div>Date & Time</div>
                        <div>Status</div>
                        <div>Action</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            for appt in appointments:
                cols = st.columns([2, 2, 2, 1, 1])
                cols[0].markdown(f"**{appt['patient_name']}**")
                cols[1].write(appt["reason"] or "N/A")
                
                t_parsed = dt.datetime.fromisoformat(appt["start_time"])
                cols[2].write(t_parsed.strftime("%b %d, %Y - %I:%M %p"))
                
                if appt["canceled"]:
                    cols[3].markdown('<span class="status-badge status-canceled">Canceled</span>', unsafe_allow_html=True)
                    cols[4].write("")
                else:
                    cols[3].markdown('<span class="status-badge status-active">Active</span>', unsafe_allow_html=True)
                    if cols[4].button("Cancel", key=f"cancel_{appt['id']}", type="secondary"):
                        try:
                            cancel_resp = requests.post(f"{base_url}/dashboard/cancel_appointment/{appt['id']}", timeout=10)
                            cancel_resp.raise_for_status()
                            st.success(f"Canceled appointment for {appt['patient_name']}.")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Cancellation failed: {ex}")
        else:
            # Data table mode (clean Pandas DataFrame view)
            table_data = []
            for appt in appointments:
                t_parsed = dt.datetime.fromisoformat(appt["start_time"])
                table_data.append({
                    "ID": appt["id"],
                    "Patient Name": appt["patient_name"],
                    "Reason": appt["reason"] or "N/A",
                    "Appointment Time": t_parsed.strftime("%Y-%m-%d %H:%M"),
                    "Status": "Canceled" if appt["canceled"] else "Active",
                    "Booked At": dt.datetime.fromisoformat(appt["created_at"]).strftime("%Y-%m-%d %H:%M")
                })
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "📅 Schedule Appointment":
    st.markdown("""
        <div class="dashboard-header">
            <h1>Schedule Appointment</h1>
            <p>Manually book appointments for clinic walk-ins or phone calls.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("new_appointment_form", clear_on_submit=True):
        patient_name = st.text_input("Patient Name", placeholder="Enter full name of the patient")
        reason = st.text_input("Reason / Symptoms", placeholder="e.g. Fever, Annual Wellness Visit, Toothache")
        
        col_d, col_t = st.columns(2)
        with col_d:
            start_date = st.date_input("Appointment Date", value=dt.date.today() + dt.timedelta(days=1))
        with col_t:
            start_time = st.time_input("Appointment Time", value=dt.time(9, 0))
            
        submit = st.form_submit_button("Book Appointment")

        if submit:
            if not patient_name.strip():
                st.error("Patient name is required.")
            else:
                start_dt = dt.datetime.combine(start_date, start_time)
                payload = {
                    "patient_name": patient_name.strip(),
                    "reason": reason.strip() or None,
                    "start_time": start_dt.isoformat(),
                }
                try:
                    resp = requests.post(f"{base_url}/schedule_appointment/", json=payload, timeout=10)
                    resp.raise_for_status()
                    st.success(f"Appointment successfully scheduled for **{patient_name.strip()}** on {start_date} at {start_time}.")
                except Exception as exc:
                    st.error(f"Scheduling failed: {exc}")

elif page == "🚫 Bulk Cancellations":
    st.markdown("""
        <div class="dashboard-header">
            <h1>Bulk Cancellations</h1>
            <p>Admin tools to cancel all of a patient's appointments on a specific day.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.warning("⚠️ Warning: This operation will cancel ALL active appointments for the specified patient on the selected date.")

    with st.form("bulk_cancel_form"):
        cancel_name = st.text_input("Patient Name", placeholder="Patient name to match")
        cancel_date = st.date_input("Target Date", value=dt.date.today())
        
        submit = st.form_submit_button("Execute Cancellation")

        if submit:
            if not cancel_name.strip():
                st.error("Patient name is required.")
            else:
                payload = {
                    "patient_name": cancel_name.strip(),
                    "date": cancel_date.isoformat()
                }
                try:
                    resp = requests.post(f"{base_url}/cancel_appointment/", json=payload, timeout=10)
                    resp.raise_for_status()
                    data = resp.json() if resp.content else {}
                    st.success(f"Canceled **{data.get('canceled_count', 0)}** active appointment(s) matching '{cancel_name.strip()}' on {cancel_date}.")
                except Exception as exc:
                    st.error(f"Cancellation operation failed: {exc}")
