"""
Lead Management Dashboard - Streamlit Web Interface
A beautiful and interactive dashboard for managing leads and viewing analytics.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
st.set_page_config(
    page_title="Lead Management AI System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.25rem solid #1f77b4;
    }
    .status-new { color: #ffa500; }
    .status-qualified { color: #1f77b4; }
    .status-converted { color: #28a745; }
    .status-lost { color: #dc3545; }
</style>
""", unsafe_allow_html=True)


def get_api_data(endpoint: str):
    """Fetch data from API with error handling."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data from API: {str(e)}")
        return None


def main():
    """Main dashboard function."""

    # Header
    st.markdown('<h1 class="main-header">🎯 Lead Management AI System</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("📊 Dashboard Navigation")

        page = st.selectbox(
            "Choose a section:",
            ["Overview", "Leads Management", "Analytics", "Agent Performance", "Settings"]
        )

        st.markdown("---")
        st.markdown("### System Status")

        # Health check
        health_data = get_api_data("/health")
        if health_data:
            status_color = "🟢" if health_data.get("status") == "healthy" else "🔴"
            st.write(f"{status_color} API Status: {health_data.get('status', 'unknown').title()}")
        else:
            st.write("🔴 API Status: Unavailable")

    # Main content based on selected page
    if page == "Overview":
        show_overview()
    elif page == "Leads Management":
        show_leads_management()
    elif page == "Analytics":
        show_analytics()
    elif page == "Agent Performance":
        show_agent_performance()
    elif page == "Settings":
        show_settings()


def show_overview():
    """Show dashboard overview with key metrics."""

    st.header("📈 Overview")

    # Get dashboard data
    dashboard_data = get_api_data("/api/v1/analytics/dashboard")

    if not dashboard_data:
        st.error("Unable to load dashboard data")
        return

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    summary = dashboard_data.get("summary", {})

    with col1:
        st.metric("Total Leads", summary.get("total_leads", 0))

    with col2:
        st.metric("Active Leads", summary.get("active_leads", 0))

    with col3:
        st.metric("Qualified Leads", summary.get("qualified_leads", 0))

    with col4:
        st.metric("Conversion Rate", f"{summary.get('conversion_rate', 0):.1f}%")

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Leads Over Time")
        trends = dashboard_data.get("performance_trends", {})
        if trends.get("leads_over_time"):
            fig = px.line(
                x=trends.get("periods", []),
                y=trends.get("leads_over_time", []),
                title="Leads Generation Trend",
                labels={"x": "Period", "y": "Number of Leads"}
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎯 Conversion Rate Trend")
        if trends.get("conversion_over_time"):
            fig = px.bar(
                x=trends.get("periods", []),
                y=trends.get("conversion_over_time", []),
                title="Conversion Rate by Period",
                labels={"x": "Period", "y": "Conversion Rate (%)"}
            )
            st.plotly_chart(fig, use_container_width=True)

    # Recent activity
    st.subheader("🔔 Recent Activity")
    activities = dashboard_data.get("recent_activity", [])

    for activity in activities[:5]:  # Show last 5 activities
        timestamp = datetime.fromtimestamp(activity.get("timestamp", 0))
        st.write(f"• **{activity.get('type', 'Unknown').replace('_', ' ').title()}**: {activity.get('description', '')}")
        st.caption(f"🕒 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


def show_leads_management():
    """Show leads management interface."""

    st.header("👥 Leads Management")

    tab1, tab2, tab3 = st.tabs(["📋 All Leads", "➕ Add New Lead", "🔍 Search & Filter"])

    with tab1:
        # Get leads data
        leads_data = get_api_data("/api/v1/leads")

        if leads_data and leads_data.get("leads"):
            leads_df = pd.DataFrame(leads_data["leads"])

            # Display leads table
            st.dataframe(leads_df, use_container_width=True)

            # Lead actions
            if not leads_df.empty:
                selected_lead = st.selectbox(
                    "Select a lead to process:",
                    options=leads_df["id"].tolist(),
                    format_func=lambda x: f"{x} - {leads_df[leads_df['id'] == x]['name'].iloc[0]}"
                )

                if st.button("🚀 Process Lead with AI"):
                    with st.spinner("Processing lead through AI agents..."):
                        result = requests.post(f"{API_BASE_URL}/api/v1/leads/{selected_lead}/process")
                        if result.status_code == 200:
                            st.success("✅ Lead processed successfully!")
                            st.json(result.json())
                        else:
                            st.error("❌ Failed to process lead")
        else:
            st.info("No leads found. Add your first lead using the 'Add New Lead' tab.")

    with tab2:
        st.subheader("Add New Lead")

        with st.form("new_lead_form"):
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="john@example.com")
            phone = st.text_input("Phone", placeholder="+1 (555) 123-4567")
            company = st.text_input("Company", placeholder="Tech Corp")
            source = st.selectbox("Lead Source", ["website", "social_media", "referral", "cold_call", "email"])
            budget = st.number_input("Budget ($)", min_value=0, step=1000)
            timeline = st.text_input("Timeline", placeholder="3 months")
            notes = st.text_area("Notes", placeholder="Additional information...")

            submitted = st.form_submit_button("➕ Create Lead")

            if submitted:
                lead_data = {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "company": company,
                    "source": source,
                    "budget": budget if budget > 0 else None,
                    "timeline": timeline,
                    "notes": notes
                }

                response = requests.post(f"{API_BASE_URL}/api/v1/leads/", json=lead_data)

                if response.status_code == 200:
                    st.success("✅ Lead created successfully!")
                    st.json(response.json())
                else:
                    st.error(f"❌ Failed to create lead: {response.text}")

    with tab3:
        st.subheader("Search & Filter Leads")

        col1, col2, col3 = st.columns(3)

        with col1:
            search_name = st.text_input("Search by name", placeholder="Enter name...")

        with col2:
            filter_status = st.selectbox("Filter by status", ["all", "new", "qualified", "nurturing", "converted", "lost"])

        with col3:
            filter_source = st.selectbox("Filter by source", ["all", "website", "social_media", "referral", "cold_call", "email"])

        if st.button("🔍 Search"):
            # Implement search logic
            st.info("Search functionality will be implemented with backend filtering")


def show_analytics():
    """Show detailed analytics."""

    st.header("📊 Detailed Analytics")

    # Get analytics data
    analytics_data = get_api_data("/api/v1/analytics/leads")

    if not analytics_data:
        st.error("Unable to load analytics data")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Leads", analytics_data.get("total_leads", 0))

    with col2:
        st.metric("Qualified Leads", analytics_data.get("qualified_leads", 0))

    with col3:
        st.metric("Conversion Rate", f"{analytics_data.get('conversion_rate', 0):.1f}%")

    with col4:
        st.metric("Average Score", f"{analytics_data.get('average_score', 0):.1f}")

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Leads by Source")
        source_data = analytics_data.get("leads_by_source", {})
        if source_data:
            fig = px.pie(
                values=list(source_data.values()),
                names=list(source_data.keys()),
                title="Lead Sources Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 Leads by Status")
        status_data = analytics_data.get("leads_by_status", {})
        if status_data:
            fig = px.bar(
                x=list(status_data.keys()),
                y=list(status_data.values()),
                title="Lead Status Distribution",
                labels={"x": "Status", "y": "Count"}
            )
            st.plotly_chart(fig, use_container_width=True)

    # Performance metrics
    st.subheader("⚡ Performance Metrics")
    perf_metrics = analytics_data.get("performance_metrics", {})

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric("Avg Response Time", f"{perf_metrics.get('response_time_avg', 0):.1f}h")

    with metric_col2:
        st.metric("Avg Qualification Time", f"{perf_metrics.get('qualification_time_avg', 0):.1f} days")

    with metric_col3:
        st.metric("Avg Conversion Time", f"{perf_metrics.get('conversion_time_avg', 0):.1f} days")


def show_agent_performance():
    """Show AI agent performance metrics."""

    st.header("🤖 AI Agent Performance")

    # Get agent analytics
    agent_data = get_api_data("/api/v1/analytics/agents")

    if not agent_data:
        st.error("Unable to load agent performance data")
        return

    # Agent performance cards
    agents = list(agent_data.keys())

    for i in range(0, len(agents), 2):
        col1, col2 = st.columns(2)

        for j, col in enumerate([col1, col2]):
            if i + j < len(agents):
                agent_name = agents[i + j]
                agent_info = agent_data[agent_name]

                with col:
                    with st.container():
                        st.subheader(f"🎯 {agent_name.replace('_', ' ').title()}")

                        metric1, metric2 = st.columns(2)

                        with metric1:
                            st.metric("Success Rate", f"{agent_info.get('success_rate', 0):.1f}%")

                        with metric2:
                            st.metric("Processed", agent_info.get('leads_processed', 0))

                        if 'average_processing_time' in agent_info:
                            st.metric("Avg Processing Time", f"{agent_info['average_processing_time']:.1f}s")

                        if 'accuracy_rate' in agent_info:
                            st.metric("Accuracy Rate", f"{agent_info.get('accuracy_rate', 0):.1f}%")


def show_settings():
    """Show settings and configuration."""

    st.header("⚙️ Settings")

    st.subheader("API Configuration")
    st.text_input("API Base URL", value=API_BASE_URL, disabled=True)
    st.info("⚠️ Settings are managed through environment variables in production.")

    st.subheader("System Information")
    st.write("**Version:** 1.0.0")
    st.write("**Framework:** FastAPI + Streamlit")
    st.write("**AI Engine:** Agno + xAI Grok-4")

    if st.button("🔄 Refresh Dashboard"):
        st.rerun()


if __name__ == "__main__":
    main()