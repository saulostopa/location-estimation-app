# The app allows users to upload a CSV file, process the data, and visualize it in various ways
# The app also provides options to download the generated reports and visualizations
# The app is designed to be user-friendly and interactive, leveraging Streamlit's capabilities
# The app includes features like filtering by state, grouping data by time intervals,
# and generating various types of visualizations such as maps, line charts, histograms, and bar charts
# The app is structured to handle data loading, processing, visualization, and exporting in a clean and efficient manner
# The app uses pandas for data manipulation, matplotlib for plotting,
# and Streamlit for the web interface
# The app is modular, with functions defined for each major task,
# making it easy to maintain and extend in the future
# The app is designed to be run in a Streamlit environment, which provides an interactive web interface
# for users to interact with the data and visualizations
# The app is suitable for analyzing location data over time,
# providing insights into the distribution of occurrences across different states
# and the confidence levels associated with those occurrences
# The app is a useful tool for anyone needing to analyze and visualize location data
# The app is built to be responsive and user-friendly, ensuring a smooth experience for users

import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
from collections import Counter
from matplotlib import pyplot as plt
import io
from geopy.distance import geodesic
import numpy as np

# --- CONFIGURATION CONSTANTS ---
# Chart Sizes (Width, Height in inches)
CHART_FIGSIZE_LINE = (10, 3)
CHART_FIGSIZE_HIST = (5, 2)
CHART_FIGSIZE_BAR = (5, 2)

# Map Settings
MAP_ZOOM = 8

# Font Sizes
FONT_SIZE_TITLE = 12
FONT_SIZE_LABEL = 8
FONT_SIZE_TICK = 6
FONT_SIZE_LEGEND = 6

# Function to calculate distance using vectorized Haversine formula
def haversine_np(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    return km

# Function to load data
def load_data(data_file, is_url=False):
    if is_url:
        df = pd.read_json(data_file)
    else:
        df = pd.read_csv(data_file, low_memory=False)

    df = df[(df['Latitude'] != 0) &
            (df['Longitude'] != 0) &
            (df['State'].notnull()) &
            (df['UTCDateTime'].notnull())].copy()
    df['UTCDateTime'] = pd.to_datetime(df['UTCDateTime'], format='mixed', errors='coerce')
    df = df[df['UTCDateTime'].notnull()]
    df.set_index('UTCDateTime', inplace=True)
    df.sort_index(inplace=True)
    return df

def rolling_mode(series, window):
    padded = [None] * (window // 2) + list(series) + [None] * (window // 2)
    result = []
    for i in range(len(series)):
        window_slice = padded[i:i+window]
        counter = Counter([x for x in window_slice if pd.notnull(x)])
        if counter:
            mode = counter.most_common(1)[0][0]
        else:
            mode = np.nan
        result.append(mode)
    return result

# Function to refine confidence analysis
def refine_state_confidence(df, smoothing_window=3):
    df = df.copy()
    df = df.sort_index()
    df['PrevLat'] = df['Latitude'].shift(1)
    df['PrevLon'] = df['Longitude'].shift(1)

    # Use vectorized Haversine instead of slow geodesic apply
    df['DistanceKM'] = haversine_np(df['Longitude'], df['Latitude'], df['PrevLon'], df['PrevLat'])
    df['DistanceKM'] = df['DistanceKM'].fillna(0)

    df['TimeDeltaH'] = df.index.to_series().diff().dt.total_seconds() / 3600
    df['SpeedKPH'] = df['DistanceKM'] / df['TimeDeltaH']
    df['SpeedKPH'] = df['SpeedKPH'].replace([np.inf, -np.inf], np.nan).fillna(0)
    df['Anomaly'] = df['SpeedKPH'] > 300

    df['SmoothedState'] = rolling_mode(df['State'], smoothing_window)

    df['Stable'] = (df['State'] == df['SmoothedState']).astype(int)
    df['ConfidenceRefined (%)'] = df['Stable'] * 90
    return df

# Function to generate report
def generate_report(df, interval):
    # Normalize interval name to avoid deprecation warnings (e.g. '1H' -> '1h')
    normalized_interval = interval.replace('H', 'h')
    grouped = df.groupby(pd.Grouper(freq=normalized_interval))
    report = []
    for start_time, group in grouped:
        if group.empty:
            continue
        end_time = group.index.max()
        state_counts = group['State'].value_counts()
        most_common_state = state_counts.idxmax()
        confidence = (state_counts.max() / state_counts.sum()) * 100
        confidence_refined = group['ConfidenceRefined (%)'].mean()

        report.append({
            'Start': start_time,
            'End': end_time,
            'State': most_common_state,
            'Confidence (%)': round(confidence, 2),
            'ConfidenceRefined (%)': round(confidence_refined, 2),
            'Records': len(group),
            'Latitude': group['Latitude'].mean(),
            'Longitude': group['Longitude'].mean()
        })

    return pd.DataFrame(report)

# Caching wrappers to avoid hashing Pandas DataFrames (hash the file source/url/interval instead)
@st.cache_data
def get_processed_data(data_file, is_url=False):
    df = load_data(data_file, is_url)
    df = refine_state_confidence(df)
    return df

@st.cache_data
def get_report_data(data_file, is_url, interval):
    df = get_processed_data(data_file, is_url)
    return generate_report(df, interval)


# Map display
def show_map(filtered_df):
    map_df = filtered_df[['Latitude', 'Longitude']].dropna().rename(columns={
        'Latitude': 'latitude',
        'Longitude': 'longitude'
    })
    st.map(map_df, zoom=MAP_ZOOM)

# Line chart comparison with both confidence metrics
def line_chart(filtered_df):
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE_LINE)
    for state in filtered_df['State'].unique():
        state_df = filtered_df[filtered_df['State'] == state]
        ax.plot(state_df['Start'], state_df['Confidence (%)'], marker='o', label=f"{state} - Raw")
        ax.plot(state_df['Start'], state_df['ConfidenceRefined (%)'], marker='x', linestyle='--', label=f"{state} - Refined")
    ax.set_title('Confidence by Time Interval', fontsize=FONT_SIZE_TITLE)
    ax.set_xlabel('Interval Start', fontsize=FONT_SIZE_LABEL)
    ax.set_ylabel('Confidence (%)', fontsize=FONT_SIZE_LABEL)
    ax.tick_params(axis='both', which='major', labelsize=FONT_SIZE_TICK)
    ax.legend(fontsize=FONT_SIZE_LEGEND)
    ax.grid(True)
    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    st.download_button("Download line chart as PNG", buf.getvalue(), "line_chart_confidence.png", "image/png")

# Histogram

def confidence_histogram(filtered_df):
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE_HIST)
    filtered_df['Confidence (%)'].plot(kind='hist', bins=20, alpha=0.5, label='Raw', ax=ax)
    filtered_df['ConfidenceRefined (%)'].plot(kind='hist', bins=20, alpha=0.5, label='Refined', ax=ax)
    ax.set_title('Confidence (%) Distribution', fontsize=FONT_SIZE_TITLE)
    ax.set_xlabel('Confidence (%)', fontsize=FONT_SIZE_LABEL)
    ax.tick_params(axis='both', which='major', labelsize=FONT_SIZE_TICK)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(fontsize=FONT_SIZE_LEGEND)
    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    st.download_button("Download histogram as PNG", buf.getvalue(), "confidence_histogram.png", "image/png")

# State bar chart
def state_bar_chart(filtered_df):
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE_BAR)
    filtered_df['State'].value_counts().plot(kind='bar', ax=ax, title='Occurrences per State')
    ax.set_title('Occurrences per State', fontsize=FONT_SIZE_TITLE)
    ax.set_xlabel('State', fontsize=FONT_SIZE_LABEL)
    ax.set_ylabel('Number of Occurrences', fontsize=FONT_SIZE_LABEL)
    ax.tick_params(axis='both', which='major', labelsize=FONT_SIZE_TICK)
    ax.spines[['top', 'right']].set_visible(False)
    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    st.download_button("Download bar chart as PNG", buf.getvalue(), "state_bar_chart.png", "image/png")

# CSV export
def export_csv(filtered_df):
    csv = filtered_df.drop(columns=['Latitude', 'Longitude']).to_csv(index=False).encode('utf-8')
    st.download_button("Download Report as CSV", csv, "location_report.csv", "text/csv")

# Main app

def main():
    st.set_page_config(
        page_title="Cell Tower Triangulation & Geolocation Analyzer",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📍 Cell Tower Triangulation & Geolocation Analyzer")
    st.write("Developed a Python-driven data science application designed to ingest and parse millions of rows of mobile subscriber location data. Implemented triangulation algorithms to estimate geographic presence across specific time intervals, calculating automated confidence levels per location.")
    st.sidebar.header("📂 Data Source")

    df = None
    report_df = None
    source = None
    is_url = False

    input_method = st.sidebar.radio("Select data source:", ["Upload CSV", "Use JSON URL"])

    if input_method == "Upload CSV":
        source = st.sidebar.file_uploader("Upload the CSV file", type=["csv"])
    elif input_method == "Use JSON URL":
        source = st.sidebar.text_input("Enter the JSON URL:")
        is_url = True

    interval = st.sidebar.selectbox(
        "Select time interval:",
        options=["15min", "30min", "1H", "2H", "4H"],
        index=2
    )

    if source:
        try:
            df = get_processed_data(source, is_url)
            report_df = get_report_data(source, is_url, interval)
        except Exception as e:
            st.error(f"Error loading or processing data: {e}")
            return

        available_states = sorted(report_df['State'].dropna().unique())

        # Keep selected states in session state between interval changes
        prev_selection = st.session_state.get('selected_states', [])
        valid_defaults = [s for s in prev_selection if s in available_states]
        if not valid_defaults:
            valid_defaults = available_states

        selected_states = st.sidebar.multiselect("Filter by state:", available_states, default=valid_defaults)
        st.session_state['selected_states'] = selected_states

        filtered_df = report_df[report_df['State'].isin(selected_states)]

        if filtered_df.empty:
            st.warning("⚠️ No data available for the selected states.")
            return

        st.subheader("📄 Estimated Location Report")
        st.dataframe(filtered_df.drop(columns=['Latitude', 'Longitude']), use_container_width=True)

        st.subheader("🗺️ Geographic Visualization")
        show_map(filtered_df)

        st.subheader("📈 Confidence by Interval")
        line_chart(filtered_df)

        st.subheader("📊 Confidence (%) Distribution")
        confidence_histogram(filtered_df)

        st.subheader("📍 Occurrences per State")
        state_bar_chart(filtered_df)

        export_csv(filtered_df)
    else:
        st.info(
            "Please provide a valid dataset ([CSV upload](https://raw.githubusercontent.com/saulostopa/location-estimation-app/refs/heads/main/dataset.csv) or [API URL](https://raw.githubusercontent.com/saulostopa/location-estimation-app/refs/heads/main/dataset.json))."
        )

if __name__ == "__main__":
    main()