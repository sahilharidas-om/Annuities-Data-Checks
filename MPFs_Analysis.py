import pandas as pd
from pandas import CategoricalDtype

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

product_mapping = {
    'Index-Linked': ['C_IL_S', 'C_IL_J', 'C_IL_T'],
    'Non-Profit': ['C_NI_S', 'C_NI_J', 'C_NI_T', 'C_NP_S', 'C_NP_J', 'C_NP_T'],
    'Max Income': ['C_MX_S', 'C_MX_J', 'C_MX_T'],
    'OptiPlus': ['C_OP_S', 'C_OP_J', 'C_OP_T'],
    'Plat2003': ['C_P3_S', 'C_P3_J', 'C_P3_T'],
    'Plat1999': ['C_PL_S', 'C_PL_J', 'C_PL_T'],
    'PlatMM': ['C_PM_S', 'C_PM_J', 'C_PM_T']
}

# Dictionary to map period number to corresponding months and years
period_mapping = {
    1: 'Jun22',
    2: 'Dec22',
    3: 'Jun23',
    4: 'Dec23',
    5: 'Jun24',
    6: 'Dec24',
    7: 'Jun25',
    8: 'Dec25'
}

# Load data
df_CLS_pkl = pd.read_pickle('Extracted_MPFs_truncated.pkl')

# Define columns of interest
columns_of_interest = ['SOURCE', 'Period', 'SPCODE', 'PREM_SINGLE', 'ANNUITY_ANNUAL', 'AGE_AT_ENTRY', 'DURATION_IF_M',
                       'ANNUITY_EXPENSE_REN', 'ANNUITY_ESC_MONTH', 'ANNUITY_ESC_PC']

# Group by SOURCE and Period
grouped = df_CLS_pkl[columns_of_interest].groupby(['SOURCE', 'Period'])

# Calculate required statistics
results = grouped.agg({
    'SPCODE': 'count',  # Line Counts
    'PREM_SINGLE': 'sum',  # Premiums
    'ANNUITY_ANNUAL': 'sum',  # Annuity Benefits
    'AGE_AT_ENTRY': 'mean',  # Avg age
    'DURATION_IF_M': 'mean',  # Avg duration
    'ANNUITY_EXPENSE_REN': 'mean',  # Ren exp / policy
    'ANNUITY_ESC_MONTH': 'mean',  # Esc month
    'ANNUITY_ESC_PC': lambda x: x[x != 0].mean()  # Avg if non-zero
}).rename(columns={
    'SPCODE': 'Line_Counts',
    'PREM_SINGLE': 'Total_Premiums',
    'ANNUITY_ANNUAL': 'Total_Annuity_Benefits',
    'AGE_AT_ENTRY': 'Avg_Age_at_Entry',
    'DURATION_IF_M': 'Avg_Duration',
    'ANNUITY_EXPENSE_REN': 'Avg_Ren_Exp_per_Policy',
    'ANNUITY_ESC_MONTH': 'Avg_Esc_Month',
    'ANNUITY_ESC_PC': 'Avg_Esc_Perc_NPA'
}).reset_index()

results['Period'] = results['Period'].str.extract(r'(\d+)').astype(int)
results['Period'] = results['Period'].map(period_mapping)


def create_comparison_table(df, periods, metric):
    comparison = df[df['Period'].isin(periods)][['Period', 'SOURCE', metric]]
    comparison_pivot = comparison.pivot(index='SOURCE', columns='Period', values=metric)
    source_order = [source for group in product_mapping.values() for source in group]
    cat_type = CategoricalDtype(categories=source_order, ordered=True)
    comparison_pivot = comparison_pivot.assign(SOURCE2=pd.Series(comparison_pivot.index, index=comparison_pivot.index).astype(cat_type))
    comparison_pivot = comparison_pivot.sort_values('SOURCE2').drop(columns='SOURCE2')
    
    # Round to 0 decimal places
    comparison_pivot[periods] = comparison_pivot[periods]
    
    # Calculate difference
    if len(periods) == 2:
        comparison_pivot['Difference'] = comparison_pivot[periods[0]] - comparison_pivot[periods[1]]
        # comparison_pivot = comparison_pivot[periods + ['Difference']].applymap(lambda x: '{:.0f}'.format(x) if pd.notnull(x) else '')
        comparison_pivot = comparison_pivot[periods + ['Difference']].applymap(
            lambda x: '{:,.0f}'.format(x).replace(',', ' ') if pd.notnull(x) else '')

    return comparison_pivot

def color_difference(val, mode='dark'):
    val = val.replace(' ', '')
    if val.strip():
        val = int(val)
    else:
        val = 0
    if mode == 'dark':
        color = '#4d0000' if val < 0 else '#003300' if val > 0 else '#333333'
    else:
        color = '#ffcccc' if val < 0 else '#ccffcc' if val > 0 else '#f2f2f2'
    return f'background-color: {color}'

def create_graphs(results, selected_sources):
    # Filter the results based on selected sources
    filtered_results = results[results['SOURCE'].isin(selected_sources)]

    periods_to_compare = ['Jun24', 'Dec23']
    
    fig1 = px.line(filtered_results, x='Period', y='Line_Counts', color='SOURCE', title='Line Counts by Source Over Time', markers=True)
    fig2 = px.line(filtered_results, x='Period', y='Total_Premiums', color='SOURCE', title='Total Premiums by Source Over Time', markers=True)
    fig3 = px.line(filtered_results, x='Period', y='Total_Annuity_Benefits', color='SOURCE', title='Total Annuity Benefits by Source Over Time', markers=True)
    fig4 = px.line(filtered_results, x='Period', y='Avg_Age_at_Entry', color='SOURCE', title='Average Age by Source Over Time', markers=True)
    fig5 = px.line(filtered_results, x='Period', y='Avg_Duration', color='SOURCE', title='Average Duration by Source Over Time', markers=True)
    fig6 = px.line(filtered_results, x='Period', y='Avg_Ren_Exp_per_Policy', color='SOURCE', title='Average Renewal Expense per Policy by Source Over Time', markers=True)
    fig7 = px.line(filtered_results, x='Period', y='Avg_Esc_Month', color='SOURCE', title='Average Escalation Month by Source Over Time', markers=True)

    non_profit_values = product_mapping['Non-Profit']
    if any(value in selected_sources for value in non_profit_values):
        final_filtered_results = filtered_results[filtered_results['SOURCE'].isin(non_profit_values)]
        fig8 = px.line(final_filtered_results, x='Period', y='Avg_Esc_Perc_NPA', color='SOURCE', title='Average Escalation Percentage Over Time (NPA)', markers=True)

    figures = [fig1, fig2, fig3, fig4, fig5, fig6, fig7]
    if any(value in selected_sources for value in non_profit_values):
        figures.append(fig8)
    metrics = ['Line_Counts', 'Total_Premiums', 'Total_Annuity_Benefits', 'Avg_Age_at_Entry', 'Avg_Duration', 'Avg_Ren_Exp_per_Policy', 'Avg_Esc_Month', 'Avg_Esc_Perc_NPA']

    # Display the tables and graphs side by side
    for fig, metric in zip(figures, metrics):
        with st.container():
            _, col1, col2, _ = st.columns([0.5, 1, 2, 0.5])
            
            with col1:
                table = create_comparison_table(filtered_results, periods_to_compare, metric)
                st.write(f'**Comparison of {metric}**')
                
                if 'Difference' in table.columns:
                    styled_table = table.style.applymap(color_difference, subset=['Difference'])#.applymap(color_source, subset=pd.IndexSlice[:, 'SOURCE'])#.applymap(color_source, subset=['SOURCE'])
                
                    st.dataframe(styled_table)
                else:
                    st.table(table)
            
            with col2:
                fig.update_layout(autosize=False, width=800, margin=dict(t=50))
                st.plotly_chart(fig, use_container_width=False)

def main():
    st.set_page_config(layout="wide")
    st.title("Annuities Data Checks - June 2024")
    st.subheader("Model Point Files Checks", divider='gray')

    with st.spinner('Generating graphs...'):
        col1, _ = st.columns(2)

        products = product_mapping.keys()

        with col1:
            selected_products = st.multiselect('Select Products:', products, default=products)
        st.markdown("---")

        if selected_products:
            selected_sources = []
            for product in selected_products:
                sources = product_mapping[product]
                if isinstance(sources, list):
                    selected_sources.extend(sources)
                else:
                    selected_sources.append(sources)
            
            results_filtered = results[results['SOURCE'].isin(selected_sources)]
            create_graphs(results_filtered, selected_sources)

if __name__ == "__main__":
    main()