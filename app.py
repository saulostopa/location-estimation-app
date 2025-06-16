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
import altair as alt
from matplotlib import pyplot as plt
import io

def load_data(data_file):
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

        report.append({
            'Start': start_time,
            'End': end_time,
            'State': most_common_state,
            'Confidence (%)': round(confidence, 2),
            'Records': len(group),
            'Latitude': group['Latitude'].mean(),
            'Longitude': group['Longitude'].mean()
        })

    return pd.DataFrame(report)

def show_map(filtered_df):
    map_df = filtered_df[['Latitude', 'Longitude']].dropna().rename(columns={
        'Latitude': 'latitude',
        'Longitude': 'longitude'
    })
    st.map(map_df, zoom=8)

def line_chart(filtered_df):
    fig, ax = plt.subplots()
    for state in filtered_df['State'].unique():
        state_df = filtered_df[filtered_df['State'] == state]
        ax.plot(state_df['Start'], state_df['Confidence (%)'], marker='o', label=state)
    ax.set_title('Confidence by Time Interval', fontsize=10)
    ax.set_xlabel('Interval Start', fontsize=8)
    ax.set_ylabel('Confidence (%)', fontsize=8)
    ax.legend(fontsize=6)
    ax.tick_params(axis='x', labelsize=6)
    ax.tick_params(axis='y', labelsize=6)
    ax.grid(True)
    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    st.download_button("Download line chart as PNG", buf.getvalue(), "line_chart_confidence.png", "image/png")

def confidence_histogram(filtered_df):
    fig, ax = plt.subplots()
    filtered_df['Confidence (%)'].plot(kind='hist', bins=20, title='Confidence (%)', ax=ax)
    
    ax.set_title('Confidence (%)', fontsize=10)
    ax.set_xlabel('Confidence (%)', fontsize=10)
    ax.tick_params(axis='x', labelsize=6)
    ax.tick_params(axis='y', labelsize=6)
    ax.spines[['top', 'right']].set_visible(False)
    
    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    st.download_button("Download histogram as PNG", buf.getvalue(), "confidence_histogram.png", "image/png")


def state_bar_chart(filtered_df):
    fig, ax = plt.subplots()
    filtered_df['State'].value_counts().plot(kind='bar', ax=ax)
    
    ax.set_title('Occurrences per State', fontsize=10)
    ax.set_xlabel('State', fontsize=10)
    ax.set_ylabel('Number of Occurrences', fontsize=10)
    ax.tick_params(axis='x', labelsize=6)
    ax.tick_params(axis='y', labelsize=6)
    ax.spines[['top', 'right']].set_visible(False)
    
    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    st.download_button("Download bar chart as PNG", buf.getvalue(), "state_bar_chart.png", "image/png")


def export_csv(filtered_df):
    csv = filtered_df.drop(columns=['Latitude', 'Longitude']).to_csv(index=False).encode('utf-8')
    st.download_button("Download Report as CSV", csv, "location_report.csv", "text/csv")

def main():
    st.title("Estimated Location by Time Interval")

    data_file = st.file_uploader("Upload the CSV file with location data", type=["csv"])

    if data_file is not None:
        df = load_data(data_file)
        interval = st.selectbox("Select the time interval to group data:",
                                 options=["15min", "30min", "1H", "2H", "4H"], index=2)

        report_df = generate_report(df, interval)
        available_states = sorted(report_df['State'].dropna().unique())
        selected_states = st.multiselect("Filter by state:", available_states, default=available_states)
        filtered_df = report_df[report_df['State'].isin(selected_states)]

        st.subheader("Estimated Location Report")
        st.dataframe(filtered_df.drop(columns=['Latitude', 'Longitude']), use_container_width=True)

        st.subheader("Geographic Visualization")
        show_map(filtered_df)

        st.subheader("Confidence by Interval")
        line_chart(filtered_df)

        st.subheader("Confidence (%) Distribution")
        confidence_histogram(filtered_df)

        st.subheader("Occurrences per State")
        state_bar_chart(filtered_df)

        export_csv(filtered_df)

if __name__ == "__main__":
    main()