import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser
import os

# ── 1. GENERATE DATA ──────────────────────────────────────────────────────────
np.random.seed(42)
random.seed(42)

n = 500

regions       = ['Nairobi','Mombasa','Kisumu','Nakuru','Eldoret','Thika','Nyeri','Meru']
statuses      = ['Settled','Pending','Rejected']
status_weights= [0.6, 0.25, 0.15]
vehicle_types = ['Private Saloon','SUV','Truck','Motorcycle','Bus']

start_date = datetime(2022, 1, 1)
end_date   = datetime(2023, 12, 31)

def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

data = {
    'claim_id'        : [f'CLM{str(i).zfill(4)}' for i in range(1, n+1)],
    'date_of_claim'   : [random_date(start_date, end_date) for _ in range(n)],
    'region'          : random.choices(regions, k=n),
    'vehicle_type'    : random.choices(vehicle_types, k=n),
    'claim_amount_kes': np.random.lognormal(mean=11, sigma=1, size=n).round(2),
    'status'          : random.choices(statuses, weights=status_weights, k=n),
    'claimant_age'    : np.random.randint(18, 75, size=n),
}

df = pd.DataFrame(data)
df['year']       = df['date_of_claim'].dt.year
df['month']      = df['date_of_claim'].dt.month
df['year_month'] = df['date_of_claim'].dt.to_period('M').astype(str)

print("✅ Data generated:", len(df), "claims")

# ── 2. AGGREGATE ──────────────────────────────────────────────────────────────
monthly = (
    df.groupby('year_month')
      .agg(total_claims=('claim_id','count'),
           total_amount=('claim_amount_kes','sum'))
      .reset_index()
      .sort_values('year_month')
)

region_df = (
    df.groupby('region')
      .agg(total_claims=('claim_id','count'),
           avg_amount=('claim_amount_kes','mean'))
      .reset_index()
      .sort_values('total_claims', ascending=True)
)

status_df = df['status'].value_counts().reset_index()
status_df.columns = ['status','count']

vehicle_df = (
    df.groupby('vehicle_type')
      .agg(avg_claim=('claim_amount_kes','mean'))
      .reset_index()
      .sort_values('avg_claim', ascending=False)
)

# ── 3. KPIs ───────────────────────────────────────────────────────────────────
total_claims   = len(df)
total_paid     = df[df['status']=='Settled']['claim_amount_kes'].sum()
avg_claim      = df['claim_amount_kes'].mean()
rejection_rate = (df['status']=='Rejected').mean() * 100

print("✅ Data aggregated")

# ── 4. BUILD CHARTS ───────────────────────────────────────────────────────────
COLORS = {'Settled':'#2ecc71','Pending':'#f39c12','Rejected':'#e74c3c'}

fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=(
        '📈 Monthly Claims Volume',
        '🥧 Claim Status Breakdown',
        '🗺  Total Claims by Region',
        '🚗 Avg Claim Amount by Vehicle Type',
        '💰 Monthly Total Claim Amount (KES)',
        '👤 Claimant Age Distribution',
    ),
    specs=[
        [{"type":"xy"},     {"type":"domain"}],
        [{"type":"xy"},     {"type":"xy"}],
        [{"type":"xy"},     {"type":"xy"}],
    ],
    vertical_spacing=0.13,
    horizontal_spacing=0.1,
)

# Chart 1 — Monthly volume
fig.add_trace(go.Scatter(
    x=monthly['year_month'],
    y=monthly['total_claims'],
    mode='lines+markers',
    line=dict(color='#3498db', width=2.5),
    fill='tozeroy',
    fillcolor='rgba(52,152,219,0.1)',
    name='Claims',
), row=1, col=1)

# Chart 2 — Status pie
fig.add_trace(go.Pie(
    labels=status_df['status'],
    values=status_df['count'],
    marker_colors=[COLORS[s] for s in status_df['status']],
    hole=0.45,
    textinfo='label+percent',
), row=1, col=2)

# Chart 3 — Region bar
fig.add_trace(go.Bar(
    x=region_df['total_claims'],
    y=region_df['region'],
    orientation='h',
    marker_color='#9b59b6',
    text=region_df['total_claims'],
    textposition='outside',
), row=2, col=1)

# Chart 4 — Vehicle type
fig.add_trace(go.Bar(
    x=vehicle_df['vehicle_type'],
    y=vehicle_df['avg_claim'],
    marker_color='#e67e22',
    text=vehicle_df['avg_claim'].round(0),
    textposition='outside',
), row=2, col=2)

# Chart 5 — Monthly total amount
fig.add_trace(go.Bar(
    x=monthly['year_month'],
    y=monthly['total_amount'],
    marker_color='#1abc9c',
), row=3, col=1)

# Chart 6 — Age distribution
fig.add_trace(go.Histogram(
    x=df['claimant_age'],
    nbinsx=20,
    marker_color='#e74c3c',
    opacity=0.8,
), row=3, col=2)

# ── 5. STYLING ────────────────────────────────────────────────────────────────
fig.update_layout(
    title=dict(
        text=(
            f"🛡️  Motor Insurance Claims Dashboard — Kenya (2022–2023)<br>"
            f"<sup>Total Claims: {total_claims:,}  |  "
            f"Total Settled: KES {total_paid:,.0f}  |  "
            f"Avg Claim: KES {avg_claim:,.0f}  |  "
            f"Rejection Rate: {rejection_rate:.1f}%</sup>"
        ),
        font=dict(size=18),
        x=0.5,
        xanchor='center',
    ),
    height=1000,
    showlegend=False,
    paper_bgcolor='#f8f9fa',
    plot_bgcolor='#ffffff',
    font=dict(family='Arial', size=12),
)

fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=True, gridcolor='#ecf0f1')

# ── 6. SAVE & OPEN ────────────────────────────────────────────────────────────
output_file = 'motor_claims_dashboard.html'
fig.write_html(output_file)

print("✅ Dashboard saved!")
print("✅ Opening in your browser now...")

# This opens it automatically in your browser
webbrowser.open('file://' + os.path.realpath(output_file))