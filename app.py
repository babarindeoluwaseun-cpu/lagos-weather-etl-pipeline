"""
Week 4 Assignment: Dash Application MVP
Project: Lagos Weather Analytics Dashboard

This Dash app connects to the PostgreSQL database created in Week 3,
pulls engineered weather data, and presents interactive analytics.
"""

import os

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


# -------------------------------------------------------
# 1. DATABASE CONFIGURATION
# -------------------------------------------------------

DB_USER = "postgres"
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "your_password_here")
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "lagos_weather_etl"


def get_database_engine():
    """
    Creates a SQLAlchemy engine for connecting to PostgreSQL.
    Password is read from the POSTGRES_PASSWORD environment variable.
    """

    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )

    return create_engine(database_url)


def load_weather_data():
    """
    Pulls weather data from PostgreSQL by joining locations and weather_daily.
    """

    engine = get_database_engine()

    query = """
        SELECT
            w.weather_id,
            w.weather_date,
            w.temperature_max,
            w.temperature_min,
            w.temperature_mean,
            w.temperature_range,
            w.precipitation_sum,
            w.rain_flag,
            w.precipitation_category,
            w.wind_speed_max,
            w.weather_code,
            w.comfort_category,
            l.city,
            l.country,
            l.latitude,
            l.longitude,
            l.timezone
        FROM weather_daily w
        JOIN locations l
            ON w.location_id = l.location_id
        ORDER BY w.weather_date;
    """

    df = pd.read_sql_query(query, engine)
    df["weather_date"] = pd.to_datetime(df["weather_date"])

    numeric_columns = [
        "temperature_max",
        "temperature_min",
        "temperature_mean",
        "temperature_range",
        "precipitation_sum",
        "wind_speed_max"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["precipitation_sum"] = df["precipitation_sum"].fillna(0)
    df["temperature_max"] = df["temperature_max"].fillna(df["temperature_mean"])
    df["temperature_min"] = df["temperature_min"].fillna(df["temperature_mean"])
    df["temperature_range"] = df["temperature_range"].fillna(
        df["temperature_max"] - df["temperature_min"]
    )
    df["wind_speed_max"] = df["wind_speed_max"].fillna(0)

    df["rain_flag"] = df["rain_flag"].astype(bool)

    return df

# -------------------------------------------------------
# 2. LOAD DATA
# -------------------------------------------------------

weather_df = load_weather_data()

min_date = weather_df["weather_date"].min()
max_date = weather_df["weather_date"].max()

precipitation_options = sorted(weather_df["precipitation_category"].dropna().unique())

# -------------------------------------------------------
# 3. DASH APP SETUP
# -------------------------------------------------------

app = Dash(__name__)

app.title = "Lagos Weather Analytics Dashboard"


# -------------------------------------------------------
# 4. APP LAYOUT
# -------------------------------------------------------

app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#f4f6f8",
        "padding": "25px"
    },
    children=[
        html.Div(
            style={
                "backgroundColor": "#1f4e79",
                "color": "white",
                "padding": "25px",
                "borderRadius": "10px",
                "marginBottom": "25px"
            },
            children=[
                html.H1(
                    "Lagos Weather Analytics Dashboard",
                    style={"marginBottom": "5px"}
                ),
                html.P(
                    "Interactive Dash MVP connected to PostgreSQL weather data engineered from the Open-Meteo API.",
                    style={"fontSize": "16px"}
                )
            ]
        ),

        html.Div(
            style={
                "display": "flex",
                "gap": "20px",
                "marginBottom": "25px",
                "flexWrap": "wrap"
            },
            children=[
                html.Div(
                    style={
                        "backgroundColor": "white",
                        "padding": "15px",
                        "borderRadius": "10px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                        "flex": "1"
                    },
                    children=[
                        html.Label("Select Date Range", style={"fontWeight": "bold"}),
                        dcc.DatePickerRange(
                            id="date-range-filter",
                            min_date_allowed=min_date,
                            max_date_allowed=max_date,
                            start_date=min_date,
                            end_date=max_date,
                            display_format="YYYY-MM-DD",
                            style={"marginTop": "10px"}
                        )
                    ]
                ),

                html.Div(
                    style={
                        "backgroundColor": "white",
                        "padding": "15px",
                        "borderRadius": "10px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                        "flex": "1"
                    },
                    children=[
                        html.Label("Filter by Precipitation Category", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="precipitation-filter",
                            options=[
                                {"label": category, "value": category}
                                for category in precipitation_options
                            ],
                            value=precipitation_options,
                            multi=True,
                            placeholder="Select precipitation categories",
                            style={"marginTop": "10px"}
                        )
                    ]
                )
            ]
        ),

        html.Div(
            id="kpi-cards",
            style={
                "display": "flex",
                "gap": "20px",
                "marginBottom": "25px",
                "flexWrap": "wrap"
            }
        ),

        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "25px"
            },
            children=[
                html.Div(
                    style={
                        "backgroundColor": "white",
                        "padding": "15px",
                        "borderRadius": "10px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"
                    },
                    children=[
                        html.H3("Temperature Trend Over Time"),
                        dcc.Graph(id="temperature-trend-chart")
                    ]
                ),

                html.Div(
                    style={
                        "backgroundColor": "white",
                        "padding": "15px",
                        "borderRadius": "10px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"
                    },
                    children=[
                        html.H3("Daily Precipitation Pattern"),
                        dcc.Graph(id="precipitation-bar-chart")
                    ]
                ),

                html.Div(
                    style={
                        "backgroundColor": "white",
                        "padding": "15px",
                        "borderRadius": "10px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"
                    },
                    children=[
                        html.H3("Rain Category Distribution"),
                        dcc.Graph(id="rain-category-chart")
                    ]
                ),

                html.Div(
                    style={
                        "backgroundColor": "white",
                        "padding": "15px",
                        "borderRadius": "10px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"
                    },
                    children=[
                        html.H3("Wind Speed vs. Temperature"),
                        dcc.Graph(id="wind-temperature-scatter")
                    ]
                )
            ]
        ),

        html.Div(
            style={
                "marginTop": "25px",
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "10px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"
            },
            children=[
                html.H3("Business Insight Summary"),
                html.P(
                    "This dashboard helps users monitor short-term weather conditions in Lagos. "
                    "The dashboard highlights temperature trends, rainfall intensity, rainy-day frequency, "
                    "and wind patterns. These insights can support planning for transportation, outdoor activity, "
                    "public health awareness, and local operations affected by weather conditions."
                )
            ]
        )
    ]
)


# -------------------------------------------------------
# 5. CALLBACKS FOR INTERACTIVITY
# -------------------------------------------------------

@app.callback(
    Output("kpi-cards", "children"),
    Output("temperature-trend-chart", "figure"),
    Output("precipitation-bar-chart", "figure"),
    Output("rain-category-chart", "figure"),
    Output("wind-temperature-scatter", "figure"),
    Input("date-range-filter", "start_date"),
    Input("date-range-filter", "end_date"),
    Input("precipitation-filter", "value")
)
def update_dashboard(start_date, end_date, selected_precipitation_categories):
    """
    Updates KPI cards and charts based on user-selected filters.
    """

    filtered_df = weather_df.copy()

    if start_date:
        filtered_df = filtered_df[
            filtered_df["weather_date"] >= pd.to_datetime(start_date)
        ]

    if end_date:
        filtered_df = filtered_df[
            filtered_df["weather_date"] <= pd.to_datetime(end_date)
        ]

    if selected_precipitation_categories:
        filtered_df = filtered_df[
            filtered_df["precipitation_category"].isin(selected_precipitation_categories)
        ]

    if filtered_df.empty:
        empty_fig = px.scatter(title="No data available for selected filters.")
        return create_kpi_cards(0, 0, 0, 0), empty_fig, empty_fig, empty_fig, empty_fig

    avg_temp = filtered_df["temperature_mean"].mean()
    total_precipitation = filtered_df["precipitation_sum"].sum()
    rainy_days = filtered_df["rain_flag"].sum()
    avg_wind_speed = filtered_df["wind_speed_max"].mean()

    kpi_cards = create_kpi_cards(
        avg_temp,
        total_precipitation,
        rainy_days,
        avg_wind_speed
    )

    temperature_fig = px.line(
        filtered_df,
        x="weather_date",
        y=["temperature_max", "temperature_mean", "temperature_min"],
        markers=True,
        title="Max, Mean, and Min Temperature Over Time",
        labels={
            "weather_date": "Date",
            "value": "Temperature (°C)",
            "variable": "Temperature Metric"
        }
    )

    precipitation_fig = px.bar(
        filtered_df,
        x="weather_date",
        y="precipitation_sum",
        color="precipitation_category",
        title="Daily Precipitation by Category",
        labels={
            "weather_date": "Date",
            "precipitation_sum": "Precipitation (mm)",
            "precipitation_category": "Rain Category"
        }
    )

    category_counts = (
        filtered_df.groupby("precipitation_category")
        .size()
        .reset_index(name="days")
    )

    rain_category_fig = px.pie(
        category_counts,
        names="precipitation_category",
        values="days",
        title="Distribution of Rain Categories"
    )

    scatter_fig = px.scatter(
        filtered_df,
        x="temperature_mean",
        y="wind_speed_max",
        size="precipitation_sum",
        color="precipitation_category",
        hover_data=["weather_date", "temperature_range"],
        title="Wind Speed vs. Mean Temperature",
        labels={
            "temperature_mean": "Mean Temperature (°C)",
            "wind_speed_max": "Max Wind Speed",
            "precipitation_sum": "Precipitation (mm)"
        }
    )

    return kpi_cards, temperature_fig, precipitation_fig, rain_category_fig, scatter_fig


def create_kpi_cards(avg_temp, total_precipitation, rainy_days, avg_wind_speed):
    """
    Creates KPI metric cards for the dashboard.
    """

    card_style = {
        "backgroundColor": "white",
        "padding": "20px",
        "borderRadius": "10px",
        "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
        "flex": "1",
        "textAlign": "center",
        "minWidth": "180px"
    }

    title_style = {
        "fontSize": "14px",
        "color": "#555",
        "marginBottom": "8px"
    }

    value_style = {
        "fontSize": "28px",
        "fontWeight": "bold",
        "color": "#1f4e79"
    }

    return [
        html.Div(
            style=card_style,
            children=[
                html.Div("Average Temperature", style=title_style),
                html.Div(f"{avg_temp:.1f} °C", style=value_style)
            ]
        ),
        html.Div(
            style=card_style,
            children=[
                html.Div("Total Precipitation", style=title_style),
                html.Div(f"{total_precipitation:.1f} mm", style=value_style)
            ]
        ),
        html.Div(
            style=card_style,
            children=[
                html.Div("Rainy Days", style=title_style),
                html.Div(f"{int(rainy_days)}", style=value_style)
            ]
        ),
        html.Div(
            style=card_style,
            children=[
                html.Div("Average Wind Speed", style=title_style),
                html.Div(f"{avg_wind_speed:.1f}", style=value_style)
            ]
        )
    ]


# -------------------------------------------------------
# 6. RUN APP
# -------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)