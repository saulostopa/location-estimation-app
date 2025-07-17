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

# Function to load data
def load_data(data_file, is_url=False):
    if is_url:
        df = pd.read_json(data_file)
    else:
        df = pd.read_csv(data_file)

    df = df[(df['Latitude'] != 0) &
            (df['Longitude'] != 0) &
            (df['State'].notnull()) &
            (df['UTCDateTime'].notnull())].copy()
    df['UTCDateTime'] = pd.to_datetime(df['UTCDateTime'], errors='coerce')
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

    df['DistanceKM'] = df.apply(lambda row: geodesic(
        (row['Latitude'], row['Longitude']),
        (row['PrevLat'], row['PrevLon'])).km if pd.notnull(row['PrevLat']) else 0, axis=1)

    df['TimeDeltaH'] = df.index.to_series().diff().dt.total_seconds() / 3600
    df['SpeedKPH'] = df['DistanceKM'] / df['TimeDeltaH']
    df['SpeedKPH'] = df['SpeedKPH'].replace([np.inf, -np.inf], np.nan).fillna(0)
    df['Anomaly'] = df['SpeedKPH'] > 300

    # df['SmoothedState'] = (
    #     df['State']
    #     .rolling(window=smoothing_window, center=True)
    #     .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan)
    # )
    df['SmoothedState'] = rolling_mode(df['State'], smoothing_window)

    df['Stable'] = (df['State'] == df['SmoothedState']).astype(int)
    df['ConfidenceRefined (%)'] = df['Stable'] * 90
    return df

# Function to generate report
def generate_report(df, interval):
    grouped = df.groupby(pd.Grouper(freq=interval))
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

# Map display
def show_map(filtered_df):
    map_df = filtered_df[['Latitude', 'Longitude']].dropna().rename(columns={
        'Latitude': 'latitude',
        'Longitude': 'longitude'
    })
    st.map(map_df, zoom=8)

# Line chart comparison with both confidence metrics
def line_chart(filtered_df):
    fig, ax = plt.subplots()
    for state in filtered_df['State'].unique():
        state_df = filtered_df[filtered_df['State'] == state]
        ax.plot(state_df['Start'], state_df['Confidence (%)'], marker='o', label=f"{state} - Raw")
        ax.plot(state_df['Start'], state_df['ConfidenceRefined (%)'], marker='x', linestyle='--', label=f"{state} - Refined")
    ax.set_title('Confidence by Time Interval')
    ax.set_xlabel('Interval Start')
    ax.set_ylabel('Confidence (%)')
    ax.legend(fontsize='small')
    ax.grid(True)
    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    st.download_button("Download line chart as PNG", buf.getvalue(), "line_chart_confidence.png", "image/png")

# Histogram

def confidence_histogram(filtered_df):
    fig, ax = plt.subplots()
    filtered_df['Confidence (%)'].plot(kind='hist', bins=20, alpha=0.5, label='Raw', ax=ax)
    filtered_df['ConfidenceRefined (%)'].plot(kind='hist', bins=20, alpha=0.5, label='Refined', ax=ax)
    ax.set_title('Confidence (%) Distribution')
    ax.set_xlabel('Confidence (%)')
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(fontsize='small')
    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    st.download_button("Download histogram as PNG", buf.getvalue(), "confidence_histogram.png", "image/png")

# State bar chart
def state_bar_chart(filtered_df):
    fig, ax = plt.subplots()
    filtered_df['State'].value_counts().plot(kind='bar', ax=ax, title='Occurrences per State')
    ax.set_xlabel('State')
    ax.set_ylabel('Number of Occurrences')
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
        page_title="📍 Estimated Location by Time Interval",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📍 Estimated Location by Time Interval")
    st.sidebar.header("📂 Data Source")

    df = None
    input_method = st.sidebar.radio("Select data source:", ["Upload CSV", "Use JSON URL"])

    if input_method == "Upload CSV":
        data_file = st.sidebar.file_uploader("Upload the CSV file", type=["csv"])
        if data_file is not None:
            df = load_data(data_file)

    elif input_method == "Use JSON URL":
        json_url = st.sidebar.text_input("Enter the JSON URL:")
        if json_url:
            try:
                df = load_data(json_url, is_url=True)
            except Exception as e:
                st.error(f"Error loading JSON from URL: {e}")
                return

    interval = st.sidebar.selectbox(
        "Select time interval:",
        options=["15min", "30min", "1H", "2H", "4H"],
        index=2
    )

    if df is not None:
        df = refine_state_confidence(df)
        report_df = generate_report(df, interval)

        available_states = sorted(report_df['State'].dropna().unique())
        selected_states = st.sidebar.multiselect("Filter by state:", available_states, default=available_states)
        filtered_df = report_df[report_df['State'].isin(selected_states)]

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