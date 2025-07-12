# 📊 WLA Trend & Forecast Dashboard

An interactive web application built with Streamlit for analyzing historical Workload Assessment (WLA) trends and generating robust future forecasts using Facebook's Prophet library.

This dashboard empowers internal teams and analysts to visualize data across different states and population groups, understand key performance metrics, and predict future trends with just a few clicks.

---
---

## ✨ Features

*   **Interactive Filtering:** Dynamically filter data by one or more states using a simple multi-select widget.
*   **Key Performance Indicators (KPIs):** At-a-glance metrics for the selected data, including Overall Average, Peak Value, and a Predicted Future Value.
*   **Historical Trend Visualization:** An interactive Plotly line chart displays historical `avg` values, color-coded by population group (`Urban`, `S-Urban`, `Rural`).
*   **Adjustable Time-Series Forecasting:**
    *   Generate future predictions for any individual population group.
    *   Use a slider to easily select the forecast horizon (from 3 to 36 months).
*   **Comparative Forecasting:** A unique chart that plots the predicted trends for all population groups on a single graph, making it easy to compare future performance.
*   **Data Caching:** Uses Streamlit's caching for high performance and fast re-loads when filters are changed.
*   **Data Export:** View the aggregated data in an expandable table and download it as a `.csv` file for offline analysis.

---

## 🛠️ Technology Stack

*   **Backend & Web Framework:** [Streamlit](https://streamlit.io/)
*   **Data Analysis:** [Pandas](https://pandas.pydata.org/)
*   **Database:** [PostgreSQL](https://www.postgresql.org/)
*   **DB Connector:** [SQLAlchemy](https://www.sqlalchemy.org/)
*   **Time-Series Forecasting:** [Prophet (by Facebook)](https://facebook.github.io/prophet/)
*   **Data Visualization:** [Plotly Express](https://plotly.com/python/plotly-express/)

---

## 🚀 Setup and Installation

Follow these steps to set up the project locally.

### Prerequisites

*   Python 3.8+
*   A running PostgreSQL instance.

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-folder>
```

### 2. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

*   **For macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
*   **For Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

### 3. Install Dependencies

Install all the required libraries from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Database Setup

1.  **Create Database:** Ensure your PostgreSQL server is running. Create a new database named `TPD_data`.

    ```sql
    CREATE DATABASE "TPD_data";
    ```

2.  **Create Table & Populate Data:** Connect to the `TPD_data` database and create the `master_data` table. You will then need to populate this table with your data.

    The application expects the following schema:
    *   `state` (VARCHAR)
    *   `month` (DATE or TIMESTAMP)
    *   `pop_group` (VARCHAR, e.g., 'Urban', 'S - Urban', 'Rural')
    *   `avg` (NUMERIC or FLOAT)

3.  **Update Connection String:** Open the Python script (`app.py` or your script name) and update the `DATABASE_URL` constant if your database credentials (username, password, host, port) are different from the default.

    ```python
    # In your script
    DATABASE_URL = "postgresql://YOUR_USERNAME:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/TPD_data"
    ```

---

## ▶️ Running the Application

Once the setup is complete, you can run the Streamlit application with a single command:

```bash
streamlit run app.py
```

Navigate to `http://localhost:8501` in your web browser to view the dashboard.

---
## 📄 Code Structure

The main script (`app.py`) is organized as follows:

*   **Page Configuration:** Sets the initial page layout and title.
*   **Database Connection:** Establishes the connection to PostgreSQL using SQLAlchemy.
*   **Data Loading Function:** A cached function (`load_data`) to fetch and clean data efficiently.
*   **Sidebar Controls:** All user inputs (state selection, forecast slider) are defined in the sidebar.
*   **Main App Logic:**
    *   Displays the title and filters the main DataFrame based on user selection.
    *   Calculates and displays KPIs.
    *   Renders the historical trend chart.
    *   Contains the logic for both individual and comparative forecasting.
*   **Data Expander:** Provides a section to view and download the underlying data.
