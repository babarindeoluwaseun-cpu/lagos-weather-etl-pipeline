# Lagos Weather ETL Pipeline

## Project Overview

This project is a Python-based ETL pipeline that extracts daily weather data for Lagos, Nigeria from the Open-Meteo API, transforms and cleans the data, performs data quality validation checks, loads the processed data into PostgreSQL, and exports an analytics-ready CSV file for future use in Power BI or Plotly Dash.

## Data Source

The data is retrieved from the Open-Meteo API using Lagos coordinates:

* Latitude: 6.5244
* Longitude: 3.3792
* Timezone: Africa/Lagos

The pipeline extracts daily weather fields including temperature, precipitation, wind speed, and weather condition code.

## Pipeline Stages

The ETL pipeline includes the following stages:

1. Data extraction from the Open-Meteo API
2. Transformation of JSON response into a structured pandas DataFrame
3. Cleaning and normalization of date, numeric, and categorical fields
4. Creation of derived metrics such as temperature range, rain flag, precipitation category, and comfort category
5. Data validation and quality checks
6. Incremental loading into PostgreSQL using unique location-date records
7. Export of analytics-ready CSV output
8. Logging of pipeline execution steps and validation results

## Database Tables

The pipeline creates and populates two PostgreSQL tables:

### locations

Stores location information such as city, country, latitude, longitude, and timezone.

### weather_daily

Stores daily weather records for Lagos, including temperature, precipitation, wind speed, weather code, and derived analytics fields.

## Data Quality Checks

The script performs several validation checks, including:

* API response validation
* Row count verification
* Required column checks
* Required non-null field checks
* Duplicate weather date detection
* Temperature range validation
* Temperature minimum/maximum logic check
* Non-negative precipitation validation
* Non-negative wind speed validation

## Incremental Loading Strategy

The `weather_daily` table uses a unique constraint on `location_id` and `weather_date`. This prevents duplicate daily weather records. If the script is run again, existing records are updated instead of duplicated.

## How to Run the Project

Install the required Python packages:

```bash
python -m pip install -r requirements.txt
```

Run the ETL pipeline:

```bash
python etl_pipeline.py
```

## Output Files

After successful execution, the pipeline creates:

* `output/lagos_weather_analytics_ready.csv`
* `logs/etl_pipeline.log`

The CSV file is prepared for future dashboard development in Power BI or Plotly Dash.

## Evidence of Successful Execution

Successful execution can be verified through:

* Terminal output showing the ETL pipeline completed successfully
* PostgreSQL tables populated in pgAdmin
* The generated analytics-ready CSV file
* The generated ETL log file showing validation checks passed
