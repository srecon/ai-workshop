import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import numpy as np

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

def create_wealth_pyramid(allocation: dict) -> str:
    """Create Wealth Pyramid visualization"""
    categories = ['Foundation Assets', 'Growth Assets', 'High-Risk Assets']
    values = [
        float(allocation.get('foundation', 0)),
        float(allocation.get('growth', 0)),
        float(allocation.get('high_risk', 0))
    ]
    colors = ['#2ecc71', '#3498db', '#e74c3c']
    
    fig = go.Figure(data=[
        go.Bar(
            x=values,
            y=categories,
            orientation='h',
            marker_color=colors,
            text=[f'₽{v:,.0f}' for v in values],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='Wealth Pyramid - Risk Structure',
        xaxis_title='Value (RUB)',
        yaxis_title='Asset Class',
        height=400,
        showlegend=False,
        template='plotly_white'
    )
    
    # Convert to dict and handle numpy types
    fig_dict = fig.to_dict()
    fig_dict = convert_numpy_types(fig_dict)
    return json.dumps(fig_dict)

def create_asset_allocation_pie(allocation: dict) -> str:
    """Create asset allocation pie chart"""
    labels = []
    values = []
    for category, value in allocation.items():
        if value > 0:
            labels.append(category.replace('_', ' ').title())
            values.append(float(value))
    
    if not values:
        # Return empty chart if no data
        fig = go.Figure()
        fig.update_layout(title='No Asset Data Available', height=400)
        fig_dict = fig.to_dict()
        fig_dict = convert_numpy_types(fig_dict)
        return json.dumps(fig_dict)
    
    fig = px.pie(
        values=values, 
        names=labels,
        title='Asset Allocation by Category',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    fig_dict = fig.to_dict()
    fig_dict = convert_numpy_types(fig_dict)
    return json.dumps(fig_dict)

def create_net_worth_gauge(net_worth: float) -> str:
    """Create net worth gauge chart"""
    net_worth = float(net_worth)
    max_value = max(net_worth * 2, 100000)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=net_worth,
        title={'text': "Net Worth (RUB)"},
        delta={'reference': 0},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, net_worth/2], 'color': "lightgray"},
                {'range': [net_worth/2, net_worth], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': net_worth
            }
        }
    ))
    
    fig.update_layout(height=300)
    fig_dict = fig.to_dict()
    fig_dict = convert_numpy_types(fig_dict)
    return json.dumps(fig_dict)

def create_cashflow_chart(monthly_income: float, monthly_expenses: float) -> str:
    """Create cashflow comparison chart"""
    monthly_income = float(monthly_income)
    monthly_expenses = float(monthly_expenses)
    
    fig = go.Figure(data=[
        go.Bar(name='Income', x=['Monthly'], y=[monthly_income], marker_color='#2ecc71'),
        go.Bar(name='Expenses', x=['Monthly'], y=[monthly_expenses], marker_color='#e74c3c')
    ])
    
    fig.update_layout(
        title='Monthly Cashflow',
        yaxis_title='Amount (RUB)',
        barmode='group',
        height=350,
        template='plotly_white'
    )
    
    fig_dict = fig.to_dict()
    fig_dict = convert_numpy_types(fig_dict)
    return json.dumps(fig_dict)

def create_risk_gauge(risk_score: int) -> str:
    """Create risk score gauge"""
    risk_score = int(risk_score)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        title={'text': "Risk Score (1-10)"},
        gauge={
            'axis': {'range': [None, 10]},
            'bar': {'color': "darkred"},
            'steps': [
                {'range': [0, 3], 'color': "lightgreen"},
                {'range': [3, 6], 'color': "yellow"},
                {'range': [6, 10], 'color': "salmon"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': risk_score
            }
        }
    ))
    
    fig.update_layout(height=300)
    fig_dict = fig.to_dict()
    fig_dict = convert_numpy_types(fig_dict)
    return json.dumps(fig_dict)