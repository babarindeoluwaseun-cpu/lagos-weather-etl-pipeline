# Lagos Weather Data Pipeline and Dash Analytics Dashboard

## Project Overview

This project is an end-to-end weather analytics project for Lagos, Nigeria. It includes a Python-based ETL pipeline and an interactive Dash dashboard connected to a PostgreSQL database.

The ETL pipeline extracts daily weather data from the Open-Meteo API, cleans and transforms the data, performs data quality validation checks, loads the processed records into PostgreSQL, and exports an analytics-ready CSV file. The Dash application then connects to PostgreSQL and presents interactive weather insights through KPI cards, filters, and visualizations.

## Project Purpose

The purpose of this project is to demonstrate a complete data engineering workflow from data extraction to analytics application development. The dashboard is designed to help users understand short-term weather trends in Lagos, including temperature patterns, rainfall intensity, rainy-day frequency, and wind conditions.

These insights can support planning for transportation, outdoor activities, public health awareness, and local operations affected by weather conditions.

## Data Source

The data is retrieved from the Open-Meteo API using Lagos coordinates:

* Latitude: 6.5244
* Longitude: 3.3792
* Timezone: West Africa/Lagos

The extracted daily weather fields include:

* Weather date
* Weather code
* Maximum temperature
* Minimum temperature
* Mean temperature
* Precipitation sum
* Maximum wind speed

## Database

The project uses PostgreSQL as the relational database.

Database name:

```text
lagos_weather_etl
```

The database contains two main tables:

### locations

Stores location information such as city, country, latitude, longitude, and timezone.

### weather_daily

Stores daily weather records and derived analytics fields, including temperature range, rain flag, precipitation category, and comfort category.

## ETL Pipeline

The ETL pipeline is contained in:

```text
etl_pipeline.py
```

The pipeline performs the following stages:

1. Connects to PostgreSQL
2. Creates the database and required tables if they do not already exist
3. Extracts weather data from the Open-Meteo API
4. Converts the API JSON response into a pandas DataFrame
5. Cleans and standardizes fields
6. Converts dates and numeric columns to appropriate data types
7. Creates derived metrics
8. Performs data quality validation checks
9. Loads the processed data into PostgreSQL
10. Exports an analytics-ready CSV file

## Transformation and Derived Metrics

The pipeline creates several derived metrics to support analytics:

* `temperature_range`: Difference between maximum and minimum daily temperature
* `rain_flag`: Indicates whether precipitation occurred on a given day
* `precipitation_category`: Classifies precipitation as No Rain, Light Rain, Moderate Rain, or Heavy Rain
* `comfort_category`: Classifies daily temperature conditions as Cool, Mild, Warm, or Hot

## Data Quality Checks

The ETL script performs multiple validation checks, including:

* API response validation
* Row count verification
* Required column validation
* Required non-null field checks
* Duplicate weather date detection
* Temperature range validation
* Temperature minimum and maximum logic check
* Non-negative precipitation validation
* Non-negative wind speed validation

Validation messages are written to the terminal and to the log file.

## Incremental Loading Strategy

The `weather_daily` table uses a unique constraint on `location_id` and `weather_date`.

This prevents duplicate weather records for the same location and date. If the ETL script is run again, existing records are updated instead of duplicated. This supports an incremental loading strategy suitable for recurring pipeline execution.

## Dash Application

The Dash application is contained in:

```text
app.py
```

The application connects directly to the PostgreSQL database and pulls the processed weather records for visualization.

The dashboard includes:

* KPI cards for average temperature, total precipitation, rainy days, and average wind speed
* Date range filter
* Precipitation category dropdown filter
* Temperature trend chart
* Daily precipitation chart
* Rain category distribution chart
* Wind speed vs. temperature scatter plot
* Business insight summary

## Dashboard Features

The dashboard satisfies the MVP requirements by providing:

* PostgreSQL database connectivity
* Multiple visualizations
* Interactive filters
* KPI summary metrics
* Dynamic chart updates
* Professional layout and readable labels
* Business insight explanation

## Project Files

```text
lagos_weather_pipeline/
│
├── etl_pipeline.py
├── app.py
├── requirements.txt
├── README.md
├── output/
│   └── lagos_weather_analytics_ready.csv
├── logs/
│   └── etl_pipeline.log
└── screenshots/
    ├── dashboard_full_view.png
    ├── dashboard_lower_view.png
    ├── dashboard_filtered_date_range.png
    ├── terminal_success_1.png
    ├── terminal_success_2.png
    ├── terminal_success_3.png
    ├── pgadmin_locations.png
    └── pgadmin_weather_daily.png
```

## Requirements

Install the required Python packages using:

```bash
python -m pip install -r requirements.txt
```

The main packages used are:

* requests
* pandas
* SQLAlchemy
* psycopg2-binary
* dash
* plotly

## Environment Variable Setup

For security, the PostgreSQL password is not hardcoded in the Python files. The password is read from an environment variable named `POSTGRES_PASSWORD`.

In Windows PowerShell, set the password before running the ETL pipeline or Dash app:

```powershell
$env:POSTGRES_PASSWORD="your_postgresql_password"
```

## How to Run the ETL Pipeline

Run the ETL pipeline with:

```bash
python etl_pipeline.py
```

After successful execution, the pipeline creates or updates the PostgreSQL tables and exports:

```text
output/lagos_weather_analytics_ready.csv
```

## How to Run the Dash App

After setting the PostgreSQL password environment variable, run:

```bash
python app.py
```

The terminal will display a local Dash URL:

```text
http://127.0.0.1:8050/
```

Open this link in a web browser to view the dashboard.

## Business Insights

The dashboard shows that Lagos weather during the forecast period is generally warm, with frequent rainy days and varying rainfall intensity. The KPI cards summarize overall weather conditions, while the charts show how temperature, precipitation, and wind patterns change over time.

The interactive date range and precipitation category filters allow users to focus on specific weather periods or rainfall conditions without restarting the application.

## Evidence of Successful Execution

Successful execution is documented through:

* Terminal output screenshots
* PostgreSQL table screenshots in pgAdmin
* Generated CSV output
* ETL log file showing validation checks passed
* Dash dashboard screenshots showing full and filtered views

