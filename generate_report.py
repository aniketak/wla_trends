import pandas as pd
from sqlalchemy import create_engine, text
from fpdf import FPDF
from datetime import datetime

# --- Configuration ---
DATABASE_URL = "postgresql://postgres:root@localhost:5432/TPD_data"
REPORT_TITLE = "WLA Historical Performance Analysis"
AUTHOR = "Business Intelligence Team"

# --- 1. Data Loading ---
def get_data():
    """Connects to the database and fetches the complete, clean dataset."""
    print("Connecting to the database and fetching data...")
    engine = create_engine(DATABASE_URL)
    query = "SELECT state, month, pop_group, avg FROM master_data"
    
    with engine.connect() as connection:
        df = pd.DataFrame(connection.execute(text(query)).fetchall(), columns=['state', 'month', 'pop_group', 'avg'])

    # Data Cleaning
    df['month'] = pd.to_datetime(df['month'])
    df['state'] = df['state'].str.strip().str.title()
    df['pop_group'] = df['pop_group'].str.strip().str.lower().replace({'s - urban': 's-urban'})
    df['avg'] = pd.to_numeric(df['avg'], errors='coerce')
    df.dropna(inplace=True)
    df.sort_values(by='month', inplace=True)
    print("Data loaded and cleaned successfully.")
    return df

# --- 2. Data Analysis ---
def analyze_data(df):
    """Performs all analyses and returns a dictionary of insights."""
    print("Analyzing data...")
    insights = {}

    # Overall Summary
    insights['date_range'] = f"{df['month'].min().strftime('%b %Y')} to {df['month'].max().strftime('%b %Y')}"
    insights['total_records'] = len(df)
    insights['overall_avg'] = df['avg'].mean()
    
    peak_perf = df.loc[df['avg'].idxmax()]
    insights['peak_performance'] = {
        'value': peak_perf['avg'],
        'details': f"{peak_perf['pop_group'].capitalize()} in {peak_perf['state']} ({peak_perf['month'].strftime('%b %Y')})"
    }
    
    # Analysis by POP Group
    pop_group_analysis = df.groupby('pop_group')['avg'].agg(['mean', 'min', 'max', 'std']).reset_index()
    pop_group_analysis.columns = ['POP Group', 'Mean Avg', 'Min Avg', 'Max Avg', 'Volatility (Std Dev)']
    insights['pop_group_table'] = pop_group_analysis.sort_values(by='Mean Avg', ascending=False)

    # Analysis by State
    state_analysis = df.groupby('state')['avg'].agg(['mean', 'count']).reset_index()
    state_analysis.columns = ['State', 'Mean Avg', 'Record Count']
    insights['top_5_states'] = state_analysis.nlargest(5, 'Mean Avg')
    insights['bottom_5_states'] = state_analysis.nsmallest(5, 'Mean Avg')

    # Growth/Trend Analysis
    df['year'] = df['month'].dt.year
    first_month_avg = df[df['month'] == df['month'].min()]['avg'].mean()
    last_month_avg = df[df['month'] == df['month'].max()]['avg'].mean()
    insights['overall_growth'] = ((last_month_avg - first_month_avg) / first_month_avg) * 100 if first_month_avg else 0
    
    # Most Improved State
    # Filter out states with less than 2 data points to calculate growth
    state_counts = df['state'].value_counts()
    valid_states = state_counts[state_counts >= 2].index
    df_valid_growth = df[df['state'].isin(valid_states)]

    if not df_valid_growth.empty:
        state_growth = df_valid_growth.groupby('state').apply(lambda x: ((x.sort_values('month')['avg'].iloc[-1] - x.sort_values('month')['avg'].iloc[0]) / x.sort_values('month')['avg'].iloc[0]) * 100).reset_index(name='growth')
        insights['most_improved_state'] = state_growth.nlargest(1, 'growth').iloc[0]
    else:
        insights['most_improved_state'] = pd.Series({'state': 'N/A', 'growth': 0})


    print("Analysis complete.")
    return insights

# --- 3. PDF Report Generation ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, REPORT_TITLE, 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 6, title, 0, 1, 'L', 1)
        self.ln(4)

    def kpi_box(self, label, value, description):
        self.set_font('Arial', '', 10)
        self.cell(50, 6, label, border=1)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 6, value, border=1, ln=1)
        self.set_font('Arial', 'I', 9)
        # --- THIS IS THE FIX ---
        # Removed the 'ln=1' argument from multi_cell
        self.multi_cell(0, 5, f"  ({description})")
        self.ln(2)

    def simple_table(self, df):
        if df.empty:
            self.cell(0, 10, "No data available for this section.", ln=1)
            return
            
        self.set_font('Arial', 'B', 9)
        # Calculate width to fit the page
        page_width = self.w - 2 * self.l_margin
        col_width = page_width / len(df.columns)
        
        # Header
        for col in df.columns:
            self.cell(col_width, 7, col, 1, 0, 'C')
        self.ln()

        # Data
        self.set_font('Arial', '', 9)
        for index, row in df.iterrows():
            for item in row:
                if isinstance(item, float):
                    item = f"{item:.2f}"
                self.cell(col_width, 6, str(item), 1, 0, 'C')
            self.ln()


def create_report(insights, filename):
    """Creates and saves the PDF report using the analyzed insights."""
    print(f"Generating PDF report: {filename}...")
    pdf = PDF()
    pdf.add_page()
    pdf.set_author(AUTHOR)

    # Section 1: Executive Summary
    pdf.chapter_title('Executive Summary')
    pdf.kpi_box('Data Range Analyzed', insights['date_range'], 'The start and end dates of the data included.')
    pdf.kpi_box('Overall Average `avg`', f"{insights['overall_avg']:.2f}", 'The mean `avg` across all states, pop groups, and months.')
    pdf.kpi_box('Peak Performance', f"{insights['peak_performance']['value']:.2f}", f"Achieved by {insights['peak_performance']['details']}.")
    pdf.kpi_box('Overall Growth', f"{insights['overall_growth']:.2f}%", 'Percentage change in avg `avg` from the first to the last month.')
    pdf.kpi_box('Most Improved State', f"{insights['most_improved_state']['state']} ({insights['most_improved_state']['growth']:.2f}%)", 'State with the highest percentage growth over the entire period.')
    pdf.ln(10)

    # Section 2: POP Group Performance
    pdf.chapter_title('Performance by POP Group')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, 'This section details the performance metrics for each population group, highlighting average performance and volatility.')
    pdf.ln(5)
    pdf.simple_table(insights['pop_group_table'])
    pdf.ln(10)

    # Section 3: State-Level Performance
    pdf.chapter_title('Performance by State')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, 'The following tables rank states by their average `avg` to identify top performers and areas for potential improvement.')
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, 'Top 5 Performing States', ln=1)
    pdf.simple_table(insights['top_5_states'])
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, 'Bottom 5 Performing States', ln=1)
    pdf.simple_table(insights['bottom_5_states'])
    pdf.ln(5)
    
    pdf.output(filename)
    print(f"Report successfully generated and saved as '{filename}'")

# --- Main Execution ---
if __name__ == "__main__":
    df = get_data()
    if not df.empty:
        insights_data = analyze_data(df)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"WLA_Historical_Report_{timestamp}.pdf"
        create_report(insights_data, report_filename)
    else:
        print("No data found. Report cannot be generated.")