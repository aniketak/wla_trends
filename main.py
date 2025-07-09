import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
from prophet import Prophet

# --- Page Configuration (Do this first) ---
st.set_page_config(layout="wide", page_title="WLA Trend & Forecast Dashboard")

# --- DB Connection & Caching ---
DATABASE_URL = "postgresql://postgres:root@localhost:5432/TPD_data"
engine = create_engine(DATABASE_URL)

@st.cache_data
def load_data():
    """Loads data from the database, cleans it, and returns a DataFrame."""
    query = """
        SELECT state, month, pop_group, avg
        FROM master_data
        WHERE pop_group IN ('Urban', 'S - Urban', 'Rural')
    """
    with engine.connect() as connection:
        result = connection.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

    df['month'] = pd.to_datetime(df['month'])
    df['state'] = df['state'].str.strip().str.title()
    df['pop_group'] = df['pop_group'].str.strip().str.lower().replace({'s - urban': 's-urban'})
    df['avg'] = pd.to_numeric(df['avg'], errors='coerce')
    df.dropna(subset=['avg'], inplace=True)
    return df

# --- Load and Prepare Data ---
df_master = load_data()

# --- Sidebar for Filters and Controls ---
st.sidebar.header("Dashboard Controls")

all_states = sorted(df_master['state'].unique())
selected_states = st.sidebar.multiselect(
    "Select State(s)",
    options=all_states,
    default=all_states
)

forecast_months = st.sidebar.slider(
    "Months to Forecast",
    min_value=3,
    max_value=36,
    value=12,
    step=1,
    help="Drag to select how many months into the future you want to predict."
)

# --- Main App Logic ---
st.title("📊 WLA Trend & Forecast Dashboard")
st.markdown("An interactive tool for the team to analyze and predict trends.")

if not selected_states:
    st.warning("Please select at least one state from the sidebar to view data.")
    st.stop()

df = df_master[df_master['state'].isin(selected_states)].copy()
df_display = df.groupby(['month', 'pop_group'])['avg'].mean().reset_index()

# --- Key Metrics (KPIs) ---
st.markdown("---")
st.header("Key Metrics for Selected States", divider='rainbow')

kpi1, kpi2, kpi3 = st.columns(3)
if not df_display.empty:
    overall_avg = df_display['avg'].mean()
    peak_row = df_display.loc[df_display['avg'].idxmax()]
    kpi1.metric(label="Overall Average `avg`", value=f"{overall_avg:.2f}")
    kpi2.metric(
        label="Peak `avg` Recorded",
        value=f"{peak_row['avg']:.2f}",
        help=f"For {peak_row['pop_group'].capitalize()} in {peak_row['month'].strftime('%b %Y')}."
    )
else:
    kpi1.metric(label="Overall Average `avg`", value="N/A")
    kpi2.metric(label="Peak `avg` Recorded", value="N/A")

# --- Main Trend Visualization ---
st.header("Monthly Average Trends", divider='rainbow')
st.markdown("This chart shows the historical average `avg` for each POP group across the selected states.")

fig = px.line(df_display, x='month', y='avg', color='pop_group',
              title=f"Monthly Avg Trends for Selected State(s)", markers=True,
              labels={'month': 'Month', 'avg': 'Average Value', 'pop_group': 'POP Group'})
fig.update_layout(legend_title_text='POP Group')
st.plotly_chart(fig, use_container_width=True)

# --- Forecast Section (Single Group) ---
st.header(f"🔮 Individual Forecast for the Next {forecast_months} Months", divider='rainbow')

pop_group_options = sorted(df_display['pop_group'].unique())

if not pop_group_options:
    st.warning("No data available for the selected state(s) to generate a forecast.")
    st.stop()

selected_group_forecast = st.selectbox(
    "Choose a POP Group to Forecast",
    pop_group_options,
    help="Select the specific group you want to see a future prediction for."
)

df_prophet = df_display[df_display['pop_group'] == selected_group_forecast].rename(columns={'month': 'ds', 'avg': 'y'})

if len(df_prophet) < 2:
    st.error(f"Not enough data points (< 2) for '{selected_group_forecast}' in the selected state(s) to create a forecast.")
else:
    m = Prophet()
    m.fit(df_prophet)
    future = m.make_future_dataframe(periods=forecast_months, freq='M')
    forecast = m.predict(future)
    
    # Plot forecast (no confidence interval as per your last code)
    fig_forecast = px.line(forecast, x='ds', y='yhat',
                           title=f"Forecast for {selected_group_forecast.capitalize()}",
                           labels={'ds': 'Date', 'yhat': 'Predicted Average'})
    fig_forecast.add_scatter(x=df_prophet['ds'], y=df_prophet['y'], mode='markers', marker_color='black', name='Actual')
    st.plotly_chart(fig_forecast, use_container_width=True)
    
    last_forecast_date = forecast['ds'].iloc[-1].strftime('%b %Y')
    last_forecast_value = forecast['yhat'].iloc[-1]
    kpi3.metric(
        label=f"Predicted `avg` for {last_forecast_date}",
        value=f"{last_forecast_value:.2f}",
        help=f"Forecast for the {selected_group_forecast.capitalize()} group."
    )

# --- NEW SECTION: COMPARATIVE FORECAST FOR ALL GROUPS ---
st.header("📈 Comparative Forecast Across All POP Groups", divider='rainbow')
st.markdown("This chart projects the trends for all available POP groups on a single graph for easy comparison.")

all_forecasts_df = pd.DataFrame()

# Loop through each pop group, run a forecast, and store the results
for group in pop_group_options:
    df_group = df_display[df_display['pop_group'] == group]
    if len(df_group) >= 2:
        df_group_prophet = df_group.rename(columns={'month': 'ds', 'avg': 'y'})
        
        m_group = Prophet()
        m_group.fit(df_group_prophet)
        
        future_group = m_group.make_future_dataframe(periods=forecast_months, freq='M')
        forecast_group = m_group.predict(future_group)
        
        forecast_group['pop_group'] = group  # Add group name for plotting
        all_forecasts_df = pd.concat([all_forecasts_df, forecast_group], ignore_index=True)

if all_forecasts_df.empty:
    st.warning("Not enough data to generate a comparative forecast.")
else:
    # Plot historical data first (solid lines with markers)
    fig_all_forecasts = px.line(
        df_display, x='month', y='avg', color='pop_group', markers=True,
        title="Historical and Predicted Trends for All Groups",
        labels={'month': 'Date', 'avg': 'Average Value', 'pop_group': 'POP Group'}
    )
    
    # Add predicted data as dashed lines on top of the same figure
    fig_all_forecasts.add_traces(
        px.line(
            all_forecasts_df, x='ds', y='yhat', color='pop_group', line_dash='pop_group'
        ).data
    )

    st.plotly_chart(fig_all_forecasts, use_container_width=True)


# --- Data Expander ---
with st.expander("View and Download Aggregated Historical Data"):
    st.markdown("This is the aggregated data used for the charts above, based on your state selection.")
    st.dataframe(df_display, use_container_width=True)
    
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Aggregated Data as CSV",
        data=csv,
        file_name='wla_trends_data.csv',
        mime='text/csv',
    )