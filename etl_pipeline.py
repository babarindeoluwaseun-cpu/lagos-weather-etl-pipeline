"""
Week 3 Assignment: ETL Pipeline & Data Quality Engineering
Project: Weather Data Pipeline for Lagos, Nigeria using Open-Meteo API

This script:
1. Extracts weather forecast data from Open-Meteo API
2. Cleans and transforms the data
3. Performs data quality validation checks
4. Loads the processed data into PostgreSQL
5. Exports an analytics-ready CSV for Power BI or Plotly Dash
"""

import logging
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# -------------------------------------------------------
# 1. CONFIGURATION
# -------------------------------------------------------

DB_USER = "postgres"
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "your_password_here")   # Replace with your PostgreSQL password
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "lagos_weather_etl"

LOCATION_NAME = "Lagos"
COUNTRY = "Nigeria"
LATITUDE = 6.5244
LONGITUDE = 3.3792
TIMEZONE = "Africa/Lagos"

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

CSV_OUTPUT_PATH = OUTPUT_DIR / "lagos_weather_analytics_ready.csv"
LOG_FILE_PATH = LOG_DIR / "etl_pipeline.log"


# -------------------------------------------------------
# 2. LOGGING SETUP
# -------------------------------------------------------

def setup_logging():
    """
    Configure logging so pipeline messages are written to both:
    1. The terminal
    2. A log file in the logs folder
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE_PATH),
            logging.StreamHandler()
        ]
    )


# -------------------------------------------------------
# 3. DATABASE CONNECTION HELPERS
# -------------------------------------------------------

def get_default_engine():
    """
    Connects to the default PostgreSQL database.
    This is used first so we can create our project database if it does not exist.
    """
    connection_url = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@"
        f"{DB_HOST}:{DB_PORT}/postgres"
    )
    return create_engine(connection_url)


def get_project_engine():
    """
    Connects to the project database.
    """
    connection_url = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    return create_engine(connection_url)


def create_database_if_not_exists():
    """
    Creates the PostgreSQL database if it does not already exist.
    """
    logging.info("Checking whether database exists...")

    default_engine = get_default_engine()

    with default_engine.connect() as connection:
        connection = connection.execution_options(isolation_level="AUTOCOMMIT")

        result = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": DB_NAME}
        )

        database_exists = result.scalar()

        if database_exists:
            logging.info("Database '%s' already exists.", DB_NAME)
        else:
            connection.execute(text(f"CREATE DATABASE {DB_NAME}"))
            logging.info("Database '%s' created successfully.", DB_NAME)


def create_tables_if_not_exist(engine):
    """
    Creates locations and weather_daily tables if they do not already exist.
    """

    logging.info("Creating database tables if they do not already exist...")

    create_locations_table = """
        CREATE TABLE IF NOT EXISTS locations (
            location_id SERIAL PRIMARY KEY,
            city VARCHAR(100) NOT NULL,
            country VARCHAR(100) NOT NULL,
            latitude NUMERIC(9,6) NOT NULL,
            longitude NUMERIC(9,6) NOT NULL,
            timezone VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(city, country)
        );
    """

    create_weather_table = """
        CREATE TABLE IF NOT EXISTS weather_daily (
            weather_id SERIAL PRIMARY KEY,
            location_id INTEGER NOT NULL,
            weather_date DATE NOT NULL,
            temperature_max NUMERIC(5,2),
            temperature_min NUMERIC(5,2),
            temperature_mean NUMERIC(5,2),
            temperature_range NUMERIC(5,2),
            precipitation_sum NUMERIC(6,2),
            rain_flag BOOLEAN,
            precipitation_category VARCHAR(50),
            wind_speed_max NUMERIC(6,2),
            weather_code INTEGER,
            comfort_category VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_location
                FOREIGN KEY (location_id)
                REFERENCES locations(location_id),

            CONSTRAINT unique_location_date
                UNIQUE (location_id, weather_date)
        );
    """

    with engine.connect() as connection:
        connection.execute(text(create_locations_table))
        connection.execute(text(create_weather_table))
        connection.commit()

    logging.info("Tables are ready.")


# -------------------------------------------------------
# 4. EXTRACT
# -------------------------------------------------------

def extract_weather_data():
    """
    Extracts daily weather forecast data from Open-Meteo API.
    The API returns JSON, which will later be converted into a pandas DataFrame.
    """

    logging.info("Extracting weather data from Open-Meteo API...")

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_max"
        ],
        "timezone": TIMEZONE,
        "forecast_days": 16
    }

    response = requests.get(url, params=params, timeout=30)

    if response.status_code != 200:
        raise ValueError(
            f"API request failed. Status code: {response.status_code}. "
            f"Response: {response.text}"
        )

    data = response.json()

    if "daily" not in data:
        raise ValueError("API response does not contain expected 'daily' section.")

    logging.info("API extraction successful.")
    return data


# -------------------------------------------------------
# 5. TRANSFORM AND CLEAN
# -------------------------------------------------------

def transform_weather_data(raw_data):
    """
    Converts raw API JSON into a clean analytics-ready DataFrame.
    """

    logging.info("Transforming and cleaning weather data...")

    daily_data = raw_data["daily"]

    df = pd.DataFrame({
        "weather_date": daily_data.get("time"),
        "weather_code": daily_data.get("weather_code"),
        "temperature_max": daily_data.get("temperature_2m_max"),
        "temperature_min": daily_data.get("temperature_2m_min"),
        "temperature_mean": daily_data.get("temperature_2m_mean"),
        "precipitation_sum": daily_data.get("precipitation_sum"),
        "wind_speed_max": daily_data.get("wind_speed_10m_max")
    })

    # Convert date field to proper date format
    df["weather_date"] = pd.to_datetime(df["weather_date"]).dt.date

    # Convert numeric columns
    numeric_columns = [
        "temperature_max",
        "temperature_min",
        "temperature_mean",
        "precipitation_sum",
        "wind_speed_max"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["weather_code"] = pd.to_numeric(df["weather_code"], errors="coerce").astype("Int64")

    # Remove duplicate dates from API response if any
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["weather_date"])
    after_dedup = len(df)

    logging.info("Removed %s duplicate weather-date rows.", before_dedup - after_dedup)

    # Derived metric 1: temperature range
    df["temperature_range"] = df["temperature_max"] - df["temperature_min"]

    # Derived metric 2: rain flag
    df["rain_flag"] = df["precipitation_sum"].fillna(0) > 0

    # Derived metric 3: precipitation category
    df["precipitation_category"] = df["precipitation_sum"].apply(categorize_precipitation)

    # Derived metric 4: comfort category
    df["comfort_category"] = df["temperature_mean"].apply(categorize_temperature)

    # Add location information for analytics export
    df["city"] = LOCATION_NAME
    df["country"] = COUNTRY
    df["latitude"] = LATITUDE
    df["longitude"] = LONGITUDE
    df["timezone"] = TIMEZONE

    # Sort by date
    df = df.sort_values("weather_date").reset_index(drop=True)

    logging.info("Transformation and cleaning completed. Rows prepared: %s", len(df))
    return df


def categorize_precipitation(value):
    """
    Classifies precipitation into simple analytics categories.
    """
    if pd.isna(value):
        return "Unknown"
    if value == 0:
        return "No Rain"
    if value < 2.5:
        return "Light Rain"
    if value < 10:
        return "Moderate Rain"
    return "Heavy Rain"


def categorize_temperature(value):
    """
    Classifies average daily temperature into simple comfort categories.
    Temperature is in Celsius because Open-Meteo returns Celsius by default.
    """
    if pd.isna(value):
        return "Unknown"
    if value >= 30:
        return "Hot"
    if value >= 25:
        return "Warm"
    if value >= 20:
        return "Mild"
    return "Cool"


# -------------------------------------------------------
# 6. VALIDATION
# -------------------------------------------------------

def validate_weather_data(df):
    """
    Performs multiple data quality checks.
    Raises an error if a critical validation check fails.
    """

    logging.info("Starting data quality validation checks...")

    required_columns = [
        "weather_date",
        "weather_code",
        "temperature_max",
        "temperature_min",
        "temperature_mean",
        "temperature_range",
        "precipitation_sum",
        "rain_flag",
        "precipitation_category",
        "wind_speed_max",
        "comfort_category"
    ]

    # Check 1: Row count
    if len(df) == 0:
        raise ValueError("Validation failed: transformed dataset has zero rows.")
    logging.info("PASSED: Row count check. Rows = %s", len(df))

    # Check 2: Required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Validation failed: missing required columns: {missing_columns}")
    logging.info("PASSED: Required columns check.")

    # Check 3: Required fields should not be null
    required_non_null = ["weather_date"]
    null_counts = df[required_non_null].isnull().sum()
    if null_counts.sum() > 0:
        raise ValueError(f"Validation failed: null values found: {null_counts.to_dict()}")
    logging.info("PASSED: Required non-null fields check.")

    # Check 4: Duplicate dates
    duplicate_count = df.duplicated(subset=["weather_date"]).sum()
    if duplicate_count > 0:
        raise ValueError(f"Validation failed: {duplicate_count} duplicate weather dates found.")
    logging.info("PASSED: Duplicate date check.")

    # Check 5: Temperature range validation
    if ((df["temperature_max"] < -50) | (df["temperature_max"] > 60)).any():
        raise ValueError("Validation failed: temperature_max outside reasonable Celsius range.")
    if ((df["temperature_min"] < -50) | (df["temperature_min"] > 60)).any():
        raise ValueError("Validation failed: temperature_min outside reasonable Celsius range.")
    logging.info("PASSED: Temperature range validation.")

    # Check 6: Logical temperature validation
    if (df["temperature_min"] > df["temperature_max"]).any():
        raise ValueError("Validation failed: temperature_min is greater than temperature_max.")
    logging.info("PASSED: Temperature min/max logic check.")

    # Check 7: Precipitation cannot be negative
    if (df["precipitation_sum"] < 0).any():
        raise ValueError("Validation failed: precipitation_sum contains negative values.")
    logging.info("PASSED: Precipitation non-negative check.")

    # Check 8: Wind speed cannot be negative
    if (df["wind_speed_max"] < 0).any():
        raise ValueError("Validation failed: wind_speed_max contains negative values.")
    logging.info("PASSED: Wind speed non-negative check.")

    logging.info("All data quality validation checks passed.")


# -------------------------------------------------------
# 7. LOAD
# -------------------------------------------------------

def load_location(engine):
    """
    Inserts Lagos into the locations table if it does not already exist.
    Returns the location_id for Lagos.
    """

    logging.info("Loading location record...")

    with engine.connect() as connection:
        connection.execute(text("""
            INSERT INTO locations (city, country, latitude, longitude, timezone)
            VALUES (:city, :country, :latitude, :longitude, :timezone)
            ON CONFLICT (city, country) DO UPDATE
            SET latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                timezone = EXCLUDED.timezone;
        """), {
            "city": LOCATION_NAME,
            "country": COUNTRY,
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "timezone": TIMEZONE
        })

        result = connection.execute(text("""
            SELECT location_id
            FROM locations
            WHERE city = :city AND country = :country;
        """), {
            "city": LOCATION_NAME,
            "country": COUNTRY
        })

        location_id = result.scalar()
        connection.commit()

    logging.info("Location loaded successfully. location_id = %s", location_id)
    return location_id


def load_weather_data(engine, df, location_id):
    """
    Loads transformed weather data into PostgreSQL.

    Incremental loading strategy:
    The table has a unique constraint on (location_id, weather_date).
    If the script runs again, existing records are updated instead of duplicated.
    """

    logging.info("Loading weather records into PostgreSQL...")

    rows_loaded = 0

    insert_sql = text("""
        INSERT INTO weather_daily (
            location_id,
            weather_date,
            temperature_max,
            temperature_min,
            temperature_mean,
            temperature_range,
            precipitation_sum,
            rain_flag,
            precipitation_category,
            wind_speed_max,
            weather_code,
            comfort_category,
            updated_at
        )
        VALUES (
            :location_id,
            :weather_date,
            :temperature_max,
            :temperature_min,
            :temperature_mean,
            :temperature_range,
            :precipitation_sum,
            :rain_flag,
            :precipitation_category,
            :wind_speed_max,
            :weather_code,
            :comfort_category,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (location_id, weather_date) DO UPDATE
        SET temperature_max = EXCLUDED.temperature_max,
            temperature_min = EXCLUDED.temperature_min,
            temperature_mean = EXCLUDED.temperature_mean,
            temperature_range = EXCLUDED.temperature_range,
            precipitation_sum = EXCLUDED.precipitation_sum,
            rain_flag = EXCLUDED.rain_flag,
            precipitation_category = EXCLUDED.precipitation_category,
            wind_speed_max = EXCLUDED.wind_speed_max,
            weather_code = EXCLUDED.weather_code,
            comfort_category = EXCLUDED.comfort_category,
            updated_at = CURRENT_TIMESTAMP;
    """)

    with engine.connect() as connection:
        for _, row in df.iterrows():
            connection.execute(insert_sql, {
                "location_id": location_id,
                "weather_date": row["weather_date"],
                "temperature_max": row["temperature_max"],
                "temperature_min": row["temperature_min"],
                "temperature_mean": row["temperature_mean"],
                "temperature_range": row["temperature_range"],
                "precipitation_sum": row["precipitation_sum"],
                "rain_flag": bool(row["rain_flag"]),
                "precipitation_category": row["precipitation_category"],
                "wind_speed_max": row["wind_speed_max"],
                "weather_code": None if pd.isna(row["weather_code"]) else int(row["weather_code"]),
                "comfort_category": row["comfort_category"]
            })
            rows_loaded += 1

        connection.commit()

    logging.info("Weather loading completed. Rows inserted/updated: %s", rows_loaded)


# -------------------------------------------------------
# 8. ANALYTICS EXPORT
# -------------------------------------------------------

def export_analytics_dataset(df):
    """
    Exports cleaned and transformed data to CSV for Power BI or Plotly Dash.
    """

    logging.info("Exporting analytics-ready dataset to CSV...")

    df.to_csv(CSV_OUTPUT_PATH, index=False)

    logging.info("CSV exported successfully: %s", CSV_OUTPUT_PATH)


# -------------------------------------------------------
# 9. MAIN PIPELINE
# -------------------------------------------------------

def main():
    """
    Runs the full ETL pipeline from start to finish.
    """

    setup_logging()

    logging.info("=======================================")
    logging.info("Starting Week 3 ETL pipeline.")
    logging.info("Run timestamp: %s", datetime.now())
    logging.info("=======================================")

    try:
        create_database_if_not_exists()
        engine = get_project_engine()

        create_tables_if_not_exist(engine)

        raw_data = extract_weather_data()
        transformed_df = transform_weather_data(raw_data)

        validate_weather_data(transformed_df)

        location_id = load_location(engine)
        load_weather_data(engine, transformed_df, location_id)

        export_analytics_dataset(transformed_df)

        logging.info("ETL pipeline completed successfully.")

    except (SQLAlchemyError, requests.RequestException, ValueError, KeyError) as error:
        logging.error("ETL pipeline failed: %s", error)
        raise

    finally:
        logging.info("Pipeline execution finished.")


if __name__ == "__main__":
    main()