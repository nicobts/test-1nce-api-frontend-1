"""
Streamlit Frontend for 1NCE API Testing and Visualization

Run with: streamlit run streamlit_frontend.py
"""

import streamlit as st
import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="1NCE IoT Management",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
TOKEN_URL = "https://api.1nce.com/management-api/oauth/token"
BASE_URL = "https://api.1nce.com/management-api/v1"

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "token_expires_at" not in st.session_state:
    st.session_state.token_expires_at = None
if "organization_id" not in st.session_state:
    st.session_state.organization_id = None
if "username" not in st.session_state:
    st.session_state.username = os.getenv("ONCE_USERNAME", "")
if "password" not in st.session_state:
    st.session_state.password = os.getenv("ONCE_PASSWORD", "")


async def authenticate(username: str, password: str) -> Dict[str, Any]:
    """Authenticate with 1NCE API using Basic Authentication."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                TOKEN_URL,
                auth=(username, password),  # Basic Auth
                data={"grant_type": "client_credentials"},  # Required by 1NCE API
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Authentication failed: {str(e)}")


async def make_api_request(endpoint: str, token: str) -> Dict[Any, Any]:
    """Make an authenticated request to the 1NCE API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}{endpoint}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"API request failed: {str(e)}")


def check_token_validity():
    """Check if the current token is still valid."""
    if not st.session_state.token_expires_at:
        return False
    return datetime.now() < st.session_state.token_expires_at


def logout():
    """Clear authentication state."""
    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.token_expires_at = None
    st.session_state.organization_id = None


# Main UI
st.title("📡 1NCE IoT SIM Monitoring Platform - TEST")

# Sidebar for authentication
with st.sidebar:
    st.header("🔐 Login")
    
    if not st.session_state.authenticated or not check_token_validity():
        st.info("Please enter your 1nce credentials to get started")
        
        with st.form("login_form"):
            username = st.text_input("Username", value=st.session_state.username)
            password = st.text_input("Password", type="password", value=st.session_state.get("password", ""))
            submit_button = st.form_submit_button("🔓 Authenticate")
            
            if submit_button:
                if username and password:
                    with st.spinner("Authenticating..."):
                        try:
                            # Run async authentication
                            token_data = asyncio.run(authenticate(username, password))
                            
                            st.session_state.access_token = token_data.get("access_token")
                            st.session_state.username = username
                            
                            # Calculate token expiry
                            expires_in = token_data.get("expires_in", 3600)
                            st.session_state.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                            
                            # Extract organization ID
                            if "organisation" in token_data:
                                st.session_state.organization_id = token_data["organisation"].get("id")
                            elif "organization" in token_data:
                                st.session_state.organization_id = token_data["organization"].get("id")
                            
                            st.session_state.authenticated = True
                            st.success("✅ Authentication successful!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Authentication failed: {str(e)}")
                else:
                    st.warning("Please enter both username and password")
    
    else:
        st.success(f"✅ Authenticated as: **{st.session_state.username}**")
        
        if st.session_state.organization_id:
            st.info(f"🏢 Organization: `{st.session_state.organization_id}`")
        
        # Token expiry info
        time_remaining = (st.session_state.token_expires_at - datetime.now()).total_seconds()
        if time_remaining > 0:
            st.info(f"⏱️ Token expires in: {int(time_remaining/60)} minutes")
        else:
            st.warning("⚠️ Token expired - please re-authenticate")
        
        if st.button("🚪 Logout", type="secondary"):
            logout()
            st.rerun()
    
    st.divider()
    
    # Quick stats
    if st.session_state.authenticated and check_token_validity():
        st.header("📊 Quick Info")
        st.caption(f"Last login: {datetime.now().strftime('%H:%M:%S')}")

    st.divider()

    st.markdown("📚 [**API Documentation**](http://localhost:8000/docs)")


# Main content area
if not st.session_state.authenticated or not check_token_validity():
    # Welcome screen
    st.markdown("""
    ## Welcome to 1NCE IoT Management Platform
    
    This platform allows you to:
    - 🔍 View and manage your SIM cards
    - 📊 Monitor data usage and metrics
    - 📱 Track SMS usage
    - 🔔 View usage events and logs
    - 📈 Visualize trends over time
    
    **Please authenticate using the sidebar to get started** →
    """)
    
    # Show demo/info cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**SIM Management**\n\nView all your SIMs, their status, and detailed information")
    
    with col2:
        st.info("**Usage Analytics**\n\nTrack data consumption with interactive charts")
    
    with col3:
        st.info("**Real-time Logs**\n\nMonitor connection events and activity")

else:
    # Authenticated view - tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["📱 SIM Cards", "📊 Data Usage", "💬 SMS Usage", "📝 Usage Logs"])
    
    # Tab 1: SIM Cards
    with tab1:
        st.header("SIM Card Management")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("SIM Card List")
        
        with col2:
            if st.button("🔄 Refresh", key="refresh_sims"):
                st.cache_data.clear()
        
        @st.cache_data(ttl=300)
        def fetch_sims(token: str, org_id: Optional[str], page: int = 1, page_size: int = 100):
            """Fetch SIM cards from API."""
            try:
                endpoint = f"/sims?page={page}&pageSize={page_size}"
                if org_id:
                    endpoint = f"/sims?organisationId={org_id}&page={page}&pageSize={page_size}"
                
                data = asyncio.run(make_api_request(endpoint, token))
                return data
            except Exception as e:
                st.error(f"Error fetching SIMs: {str(e)}")
                return None
        
        # Pagination controls
        col_p1, col_p2, col_p3 = st.columns([1, 1, 2])
        with col_p1:
            page_num = st.number_input("Page", min_value=1, value=1, key="sim_list_page")
        with col_p2:
            page_size_sel = st.selectbox("Items per page", [10, 25, 50, 100], index=3, key="sim_list_size")
        
        sims_data = fetch_sims(
            st.session_state.access_token,
            st.session_state.organization_id,
            page=page_num,
            page_size=page_size_sel
        )

        if sims_data:
            # Handle both list and object responses
            if isinstance(sims_data, list):
                items = sims_data
                total_items = len(items)
            else:
                items = sims_data.get("items", [])
                total_items = sims_data.get("totalItems", len(items))
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate status counts
            status_counts = {}
            for sim in items:
                # Handle both nested and flat status formats
                status = sim.get("status")
                if isinstance(status, dict):
                    status = status.get("status", "unknown")
                elif not status:
                    status = "unknown"
                status_counts[status] = status_counts.get(status, 0) + 1
            
            with col1:
                st.metric("Total SIMs", total_items)
            with col2:
                st.metric("Active", status_counts.get("Enabled", 0))
            with col3:
                st.metric("Disabled", status_counts.get("Disabled", 0))
            with col4:
                st.metric("Other", sum(v for k, v in status_counts.items() if k not in ["Enabled", "Disabled"]))
            
            # Status distribution chart
            if status_counts:
                st.subheader("Status Distribution")
                fig = px.pie(
                    values=list(status_counts.values()),
                    names=list(status_counts.keys()),
                    title="SIM Card Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # SIM table
            st.subheader("SIM Details")
            
            # Convert to DataFrame for better display
            sim_list = []
            for sim in items:
                # Handle both nested and flat status formats
                status = sim.get("status")
                if isinstance(status, dict):
                    status = status.get("status", "N/A")

                sim_list.append({
                    "ICCID": sim.get("iccid", "N/A"),
                    "Status": status or "N/A",
                    "IMSI": sim.get("imsi", "N/A"),
                    "IP Address": sim.get("ip_address", "N/A"),
                    "IMEI": sim.get("imei", "N/A") if sim.get("imei") else "N/A",
                })
            
            # Quota fetching function
            async def fetch_quota(token: str, iccid: str):
                try:
                    return await make_api_request(f"/sims/{iccid}/quota", token)
                except:
                    return None

            if sim_list:
                df = pd.DataFrame(sim_list)
                st.dataframe(df, use_container_width=True, height=400)
                
                # SIM Details with Quota
                st.divider()
                st.subheader("🔍 SIM Details & Quota")
                
                selected_iccid_detail = st.selectbox("Select SIM for Details", df["ICCID"].tolist())
                
                if selected_iccid_detail:
                    col_d1, col_d2 = st.columns(2)
                    
                    with col_d1:
                        st.markdown("#### SIM Info")
                        sim_info = df[df["ICCID"] == selected_iccid_detail].iloc[0]
                        st.json(sim_info.to_dict())
                        
                    with col_d2:
                        st.markdown("#### Quota & Limits")
                        with st.spinner("Loading quota..."):
                            quota_data = asyncio.run(fetch_quota(st.session_state.access_token, selected_iccid_detail))
                            if quota_data:
                                st.json(quota_data)
                                
                                # Visualize quota if possible
                                if "volume" in quota_data and "totalVolume" in quota_data:
                                    used = quota_data.get("volume", 0)
                                    total = quota_data.get("totalVolume", 0)
                                    if total > 0:
                                        st.progress(min(used / total, 1.0), text=f"Data Usage: {used/1024/1024:.1f}MB / {total/1024/1024:.1f}MB")
                            else:
                                st.info("No quota information available")
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download SIM List (CSV)",
                    data=csv,
                    file_name=f"sims_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    # Tab 2: Data Usage
    with tab2:
        st.header("📊 SIM Usage Analytics")

        st.info("💡 Select a SIM card to view its detailed usage data")

        # Fetch SIM list for selector
        @st.cache_data(ttl=300)
        def fetch_sim_list(token: str, org_id: Optional[str]):
            """Fetch ALL SIM cards using pagination."""
            all_sims = []
            page = 1
            page_size = 100
            
            try:
                while True:
                    endpoint = f"/sims?page={page}&pageSize={page_size}"
                    if org_id:
                        endpoint = f"/sims?organisationId={org_id}&page={page}&pageSize={page_size}"
                    
                    data = asyncio.run(make_api_request(endpoint, token))
                    
                    current_items = []
                    if isinstance(data, list):
                        current_items = data
                    else:
                        current_items = data.get("items", [])
                    
                    if not current_items:
                        break
                        
                    all_sims.extend(current_items)
                    
                    # If we got fewer items than page_size, we've reached the end
                    if len(current_items) < page_size:
                        break
                        
                    page += 1
                    
                    # Safety break to prevent infinite loops (max 100 pages = 10000 SIMs)
                    if page > 100:
                        break
                        
                return all_sims
            except Exception as e:
                st.error(f"Error fetching SIM list: {str(e)}")
                return []

        sims = fetch_sim_list(st.session_state.access_token, st.session_state.organization_id)

        st.write(f"DEBUG: Found {len(sims)} SIMs")  # Debug output

        if sims:
            # SIM selector - allow single or multiple selection
            sim_options = {f"{sim.get('iccid')} ({sim.get('imsi', 'N/A')})": sim.get('iccid') for sim in sims}

            selection_mode = st.radio("Selection Mode", ["Single SIM", "Multiple SIMs"], horizontal=True)

            if selection_mode == "Single SIM":
                selected_sim_label = st.selectbox("Select SIM Card", list(sim_options.keys()))
                selected_iccids = [sim_options[selected_sim_label]]
            else:
                selected_sim_labels = st.multiselect("Select SIM Cards (up to 5)", list(sim_options.keys()), max_selections=5)
                selected_iccids = [sim_options[label] for label in selected_sim_labels]

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now() - timedelta(days=30),
                    max_value=datetime.now(),
                    key="usage_start"
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now(),
                    max_value=datetime.now(),
                    key="usage_end"
                )

            @st.cache_data(ttl=300)
            def fetch_sim_usage(token: str, iccid: str, start: str, end: str):
                """Fetch usage data for a specific SIM."""
                try:
                    endpoint = f"/sims/{iccid}/usage?startDate={start}&endDate={end}"
                    data = asyncio.run(make_api_request(endpoint, token))
                    return data
                except Exception as e:
                    st.error(f"Error fetching usage: {str(e)}")
                    return None

            if st.button("📊 Load Usage Data", type="primary"):
                if not selected_iccids:
                    st.warning("Please select at least one SIM card")
                else:
                    # Fetch usage for all selected SIMs
                    all_usage_data = []

                    for iccid in selected_iccids:
                        with st.spinner(f"Loading usage for {iccid}..."):
                            usage_data = fetch_sim_usage(
                                st.session_state.access_token,
                                iccid,
                                start_date.strftime("%Y-%m-%d"),
                                end_date.strftime("%Y-%m-%d")
                            )

                        if usage_data:
                            if isinstance(usage_data, list) and len(usage_data) > 0:
                                # Add ICCID to each record
                                for record in usage_data:
                                    record['iccid'] = iccid
                                all_usage_data.extend(usage_data)

                    if all_usage_data:
                        # Convert to DataFrame
                        df = pd.DataFrame(all_usage_data)

                        # Calculate total usage
                        total_mb = df["volume"].sum() if "volume" in df.columns else 0
                        total_gb = total_mb / 1024

                        # Metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Data Usage", f"{total_gb:.2f} GB")
                        with col2:
                            st.metric("SIMs Selected", len(selected_iccids))
                        with col3:
                            st.metric("Data Points", len(df))
                        with col4:
                            st.metric("Avg per SIM", f"{total_gb / len(selected_iccids):.2f} GB")

                        # Line chart
                        st.subheader("Data Usage Over Time")

                        if "date" in df.columns and "volume" in df.columns:
                            # Convert volume from MB to GB for better readability
                            df["volume_gb"] = df["volume"] / 1024

                            # If multiple SIMs, show comparison chart
                            if len(selected_iccids) > 1:
                                fig = px.line(
                                    df,
                                    x="date",
                                    y="volume_gb",
                                    color="iccid",
                                    title="Data Usage Comparison",
                                    labels={"volume_gb": "Data Usage (GB)", "date": "Date", "iccid": "SIM Card"},
                                    markers=True
                                )
                            else:
                                fig = px.line(
                                    df,
                                    x="date",
                                    y="volume_gb",
                                    title="Data Usage Trend",
                                    labels={"volume_gb": "Data Usage (GB)", "date": "Date"},
                                    markers=True
                                )

                            fig.update_layout(
                                hovermode="x unified",
                                xaxis_title="Date",
                                yaxis_title="Data Usage (GB)"
                            )

                            st.plotly_chart(fig, use_container_width=True)

                            # Bar chart - show per SIM comparison if multiple selected
                            st.subheader("Usage Summary")
                            if len(selected_iccids) > 1:
                                sim_totals = df.groupby("iccid")["volume_gb"].sum().reset_index()
                                fig_bar = px.bar(
                                    sim_totals,
                                    x="iccid",
                                    y="volume_gb",
                                    title="Total Usage by SIM",
                                    labels={"volume_gb": "Total Data Usage (GB)", "iccid": "SIM Card"}
                                )
                                st.plotly_chart(fig_bar, use_container_width=True)

                            # Data table
                            st.subheader("Detailed Data")
                            st.dataframe(df, use_container_width=True)

                            # Download
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Usage Data (CSV)",
                                data=csv,
                                file_name=f"data_usage_{start_date}_{end_date}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("No usage data found for the selected period")
                    else:
                        st.info("No usage data found for the selected SIMs")
        else:
            st.warning("No SIM cards available. Please check your SIM list.")
    
    # Tab 3: SMS Usage
    with tab3:
        st.header("💬 SIM SMS Messages")

        st.info("💡 Select a SIM card to view SMS messages")

        # Reuse SIM list
        if sims:
            sim_options_sms = {f"{sim.get('iccid')} ({sim.get('imsi', 'N/A')})": sim.get('iccid') for sim in sims}

            selection_mode_sms = st.radio("Selection Mode", ["Single SIM", "Multiple SIMs"], horizontal=True, key="sms_mode")

            if selection_mode_sms == "Single SIM":
                selected_sim_sms = st.selectbox("Select SIM Card", list(sim_options_sms.keys()), key="sms_sim_select")
                selected_iccids_sms = [sim_options_sms[selected_sim_sms]]
            else:
                selected_sims_sms = st.multiselect("Select SIM Cards (up to 5)", list(sim_options_sms.keys()), max_selections=5, key="sms_sim_multiselect")
                selected_iccids_sms = [sim_options_sms[label] for label in selected_sims_sms]

            col1, col2 = st.columns(2)
            with col1:
                page_sms = st.number_input("Page", min_value=1, value=1, key="sms_page")
            with col2:
                page_size_sms = st.selectbox("Messages per page", [10, 25, 50, 100], index=2, key="sms_page_size")

            @st.cache_data(ttl=300)
            def fetch_sim_sms(token: str, iccid: str, page: int, page_size: int):
                """Fetch SMS messages for a specific SIM."""
                try:
                    endpoint = f"/sims/{iccid}/sms?page={page}&pageSize={page_size}"
                    data = asyncio.run(make_api_request(endpoint, token))
                    return data
                except Exception as e:
                    st.error(f"Error fetching SMS: {str(e)}")
                    return None

            if st.button("💬 Load SMS Messages", type="primary"):
                if not selected_iccids_sms:
                    st.warning("Please select at least one SIM card")
                else:
                    # Fetch SMS for all selected SIMs
                    all_sms_data = []

                    for iccid in selected_iccids_sms:
                        with st.spinner(f"Loading SMS for {iccid}..."):
                            sms_data = fetch_sim_sms(
                                st.session_state.access_token,
                                iccid,
                                page_sms,
                                page_size_sms
                            )

                        if sms_data:
                            if isinstance(sms_data, list) and len(sms_data) > 0:
                                # Add ICCID to each record
                                for record in sms_data:
                                    record['iccid'] = iccid
                                all_sms_data.extend(sms_data)

                    if all_sms_data:
                        df = pd.DataFrame(all_sms_data)

                        # Metrics
                        total_sms = df["count"].sum() if "count" in df.columns else len(df)

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total SMS", int(total_sms))
                        with col2:
                            st.metric("SIMs Selected", len(selected_iccids_sms))
                        with col3:
                            st.metric("Avg per SIM", f"{total_sms / len(selected_iccids_sms):.1f}")

                        # Chart
                        if "date" in df.columns and "count" in df.columns:
                            # If multiple SIMs, color by ICCID
                            if len(selected_iccids_sms) > 1:
                                fig = px.bar(
                                    df,
                                    x="date",
                                    y="count",
                                    color="iccid",
                                    title="SMS Usage Comparison",
                                    labels={"count": "SMS Count", "date": "Date", "iccid": "SIM Card"}
                                )
                            else:
                                fig = px.bar(
                                    df,
                                    x="date",
                                    y="count",
                                    title="SMS Usage Over Time",
                                    labels={"count": "SMS Count", "date": "Date"}
                                )
                            st.plotly_chart(fig, use_container_width=True)

                            # Data table
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("No SMS data to display")
                    else:
                        st.info("No SMS messages found for the selected SIMs")
        else:
            st.warning("No SIM cards available. Please check your SIM list.")
    
    # Tab 4: Usage Logs
    with tab4:
        st.header("📝 SIM Events & Logs")
        st.info("💡 Select a SIM card to view diagnostic events and logs")

        # Reuse SIM list
        if sims:
            sim_options_events = {f"{sim.get('iccid')} ({sim.get('imsi', 'N/A')})": sim.get('iccid') for sim in sims}

            selection_mode_events = st.radio("Selection Mode", ["Single SIM", "Multiple SIMs"], horizontal=True, key="events_mode")

            if selection_mode_events == "Single SIM":
                selected_sim_events = st.selectbox("Select SIM Card", list(sim_options_events.keys()), key="events_sim_select")
                selected_iccids_events = [sim_options_events[selected_sim_events]]
            else:
                selected_sims_events = st.multiselect("Select SIM Cards (up to 5)", list(sim_options_events.keys()), max_selections=5, key="events_sim_multiselect")
                selected_iccids_events = [sim_options_events[label] for label in selected_sims_events]

            # Add page controls
            col1, col2 = st.columns(2)
            with col1:
                page_events = st.number_input("Page", min_value=1, value=1, key="events_page")
            with col2:
                page_size_events = st.selectbox("Events per page", [10, 25, 50, 100], index=2, key="events_page_size")

            @st.cache_data(ttl=300)
            def fetch_sim_events(token: str, iccid: str, page: int, page_size: int):
                """Fetch events for a specific SIM."""
                try:
                    endpoint = f"/sims/{iccid}/events?page={page}&pageSize={page_size}"
                    data = asyncio.run(make_api_request(endpoint, token))
                    return data
                except Exception as e:
                    st.error(f"Error fetching events: {str(e)}")
                    return None

            if st.button("📝 Load Events", type="primary"):
                if not selected_iccids_events:
                    st.warning("Please select at least one SIM card")
                else:
                    # Fetch events for all selected SIMs
                    all_events = []

                    for iccid in selected_iccids_events:
                        with st.spinner(f"Loading events for {iccid}..."):
                            events_data = fetch_sim_events(
                                st.session_state.access_token,
                                iccid,
                                page_events,
                                page_size_events
                            )

                        if events_data:
                            # Handle both list and object responses
                            if isinstance(events_data, list):
                                items = events_data
                            else:
                                items = events_data.get("items", [])

                            if items:
                                # Add ICCID to each event
                                for event in items:
                                    event['iccid'] = iccid
                                all_events.extend(items)

                    if all_events:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Events", len(all_events))
                        with col2:
                            st.metric("SIMs Selected", len(selected_iccids_events))
                        with col3:
                            st.metric("Avg per SIM", f"{len(all_events) / len(selected_iccids_events):.1f}")

                        # Convert to DataFrame
                        events_list = []
                        for event in all_events:
                            events_list.append({
                                "ICCID": event.get("iccid", "N/A"),
                                "Timestamp": event.get("timestamp", event.get("eventTime", "N/A")),
                                "Event Type": event.get("eventType", event.get("event_type", "N/A")),
                                "Description": event.get("description", event.get("message", "N/A")),
                                "Country": event.get("country", "N/A"),
                                "Network": event.get("network", "N/A"),
                                "IMEI": event.get("imei", "N/A"),
                            })

                        df = pd.DataFrame(events_list)

                        # Display table
                        st.dataframe(df, use_container_width=True, height=400)

                        # Download
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Events (CSV)",
                            data=csv,
                            file_name=f"sim_events_multi_{page_events}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No events found for the selected SIMs")
        else:
            st.warning("No SIM cards available. Please check your authentication.")

# Footer
st.divider()
st.caption("1NCE IoT Management Platform | Built with Streamlit")
