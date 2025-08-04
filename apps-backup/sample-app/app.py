import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Sample Streamlit App",
    page_icon="🎈",
    layout="wide"
)

st.title("🎈 Sample Streamlit App")
st.write("Welcome to your Streamlit hosting platform!")

# Sidebar
st.sidebar.header("Controls")
num_points = st.sidebar.slider("Number of data points", 10, 1000, 100)
chart_type = st.sidebar.selectbox("Chart type", ["Line", "Bar", "Scatter"])

# Generate sample data
data = pd.DataFrame({
    'x': range(num_points),
    'y': np.random.randn(num_points).cumsum(),
    'category': np.random.choice(['A', 'B', 'C'], num_points)
})

# Main content
col1, col2 = st.columns(2)

with col1:
    st.subheader("Data Preview")
    st.dataframe(data.head(10))
    
    st.subheader("Summary Statistics")
    st.write(data.describe())

with col2:
    st.subheader(f"{chart_type} Chart")
    
    if chart_type == "Line":
        st.line_chart(data.set_index('x')['y'])
    elif chart_type == "Bar":
        category_counts = data['category'].value_counts()
        st.bar_chart(category_counts)
    else:  # Scatter
        fig, ax = plt.subplots()
        for cat in data['category'].unique():
            cat_data = data[data['category'] == cat]
            ax.scatter(cat_data['x'], cat_data['y'], label=cat, alpha=0.6)
        ax.legend()
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        st.pyplot(fig)

# Footer
st.markdown("---")
st.markdown("**Server Info:**")
st.write(f"- Total data points: {len(data)}")

# Handle secrets gracefully
try:
    hostname = st.secrets.general.hostname
    st.write(f"- App running on: {hostname}")
    
    # Show additional server info if available
    if "server" in st.secrets:
        st.write(f"- Server name: {st.secrets.server.name}")
        st.write(f"- Environment: {st.secrets.general.environment}")
        st.write(f"- Version: {st.secrets.general.version}")
except Exception as e:
    st.write("- App running on: Streamlit Server")
    st.write(f"- Secrets status: Not configured ({type(e).__name__})")

# Show some platform information
st.subheader("Platform Information")
st.write("This app is running on a containerized Streamlit hosting platform with:")
st.write("- **Docker** containers for isolation")
st.write("- **Nginx** reverse proxy for routing")
st.write("- **Automatic deployment** via management scripts")
st.write("- **Persistent storage** on dedicated disk")

# Interactive demo section
st.subheader("Interactive Demo")
user_name = st.text_input("Enter your name:", placeholder="Your name here...")
if user_name:
    st.success(f"Hello, {user_name}! 👋 Welcome to the Streamlit hosting platform!")
    
    # Show a personalized chart
    personal_data = pd.DataFrame({
        'day': range(1, 8),
        'value': np.random.randint(10, 100, 7)
    })
    st.write(f"Here's some sample data for {user_name}:")
    st.bar_chart(personal_data.set_index('day'))
