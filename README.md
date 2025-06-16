# 📍 Location Estimation App

This is a Python application built with [Streamlit](https://streamlit.io/) to analyze and visualize mobile location data based on cell tower triangulation. It estimates the most probable state (e.g., NY or CT) a person was in during specific time intervals and calculates a confidence level for each estimate.

## 🔧 Features

- Upload a CSV file containing geolocation data
- Generate time-interval-based reports estimating the most likely state
- Display confidence percentages for each estimate
- Interactive map visualization
- Filter report by selected states
- Export results to CSV
- Download charts (line, histogram, bar) as PNG images

## 📊 Sample Visuals

- Time-based line charts of confidence levels
- Histograms of confidence distribution
- State frequency bar charts
- Interactive maps with estimated positions

## 🧪 Project Structure

```
├── app.py               # Main application
├── requirements.txt     # Python dependencies
├── .gitignore           # Git ignored files
├── dataset.csv          # CSV Dataset
└── README.md            # Documentation
```

## 📝 License
- This project is licensed under the MIT License.

## 📦 Dependencies

- Python (3.13)
- Streamlit (>=1.32.0)
- pandas (>=2.2.0)
- matplotlib (>=3.8.0)
- altair (>=5.1.0)

## 📁 Input File Format

The uploaded CSV file should contain at least the following columns:

- `UTCDateTime` (timestamp in UTC)
- `Latitude`
- `Longitude`
- `State`

Example rows:

```csv
UTCDateTime,Latitude,Longitude,State
2021-01-05T10:15:00Z,41.123,-73.456,NY
2021-01-05T10:30:00Z,41.124,-73.457,CT
```


## 🚀 Getting Started

#### 1. Clone the Repository

```
git clone https://github.com/saulostopa/location-estimation-app.git
cd location-estimation-app
```

#### 2. Install Requirements

We recommend using a virtual environment:

```
python3.13 -m venv venv
```

```
source venv/bin/activate
```

On Windows:

```
venv\\Scripts\\activate
```

Install requirements

```
pip install -r requirements.txt
```

#### 3. Run the App

```
streamlit run app.py
```

#### 4. Open in Browser
- Streamlit will automatically open the application in your default browser at http://localhost:8501


#### 5. Deploy on Streamlit Cloud

- Go to https://streamlit.io/cloud
- Log in with your GitHub account
- Click “New app”
- Select the repository and the main branch
- Set app.py as the main file
- Click “Deploy”