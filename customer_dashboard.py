import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import psycopg2

# ── Database Connection ───────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "my_practice_db",
    "user":     "rajannanda786",
    "password": "HxD7;$pQq1;"
}

def run_query(sql):
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

# ── Run All 10 Queries ────────────────────────────────────────────────────────
q1  = run_query("SELECT gender, SUM(purchase_amount) AS revenue FROM customer GROUP BY gender ORDER BY revenue DESC")
q2  = run_query("SELECT customer_id, purchase_amount FROM customer WHERE discount_applied='Yes' AND purchase_amount>(SELECT AVG(purchase_amount) FROM customer) ORDER BY purchase_amount DESC")
q3  = run_query("SELECT item_purchased, ROUND(AVG(review_rating::numeric),2) AS avg_rating FROM customer GROUP BY item_purchased ORDER BY avg_rating DESC LIMIT 5")
q4  = run_query("SELECT shipping_type, ROUND(AVG(purchase_amount),2) AS avg_purchase FROM customer WHERE shipping_type IN ('Express','Standard') GROUP BY shipping_type")
q5  = run_query("SELECT subscription_status, COUNT(customer_id) AS total_customers, ROUND(AVG(purchase_amount),2) AS avg_spend, SUM(purchase_amount) AS total_revenue FROM customer GROUP BY subscription_status ORDER BY total_revenue DESC")
q6  = run_query("SELECT item_purchased, ROUND(100.0*SUM(CASE WHEN discount_applied='Yes' THEN 1 ELSE 0 END)/COUNT(*),2) AS discount_rate FROM customer GROUP BY item_purchased ORDER BY discount_rate DESC LIMIT 5")
q7  = run_query("WITH ct AS (SELECT customer_id, CASE WHEN previous_purchases=1 THEN 'New' WHEN previous_purchases BETWEEN 2 AND 10 THEN 'Returning' ELSE 'Loyal' END AS segment FROM customer) SELECT segment, COUNT(*) AS num_customers FROM ct GROUP BY segment ORDER BY num_customers DESC")
q8  = run_query("WITH ic AS (SELECT category, item_purchased, COUNT(customer_id) AS total_orders, ROW_NUMBER() OVER(PARTITION BY category ORDER BY COUNT(customer_id) DESC) AS rnk FROM customer GROUP BY category, item_purchased) SELECT category, item_purchased, total_orders FROM ic WHERE rnk<=3 ORDER BY category, total_orders DESC")
q9  = run_query("SELECT subscription_status, COUNT(customer_id) AS repeat_buyers FROM customer WHERE previous_purchases>5 GROUP BY subscription_status")
q10 = run_query("SELECT age_group, SUM(purchase_amount) AS total_revenue FROM customer GROUP BY age_group ORDER BY total_revenue DESC")
kpi = run_query("SELECT COUNT(DISTINCT customer_id) AS total_customers, SUM(purchase_amount) AS total_revenue, ROUND(AVG(review_rating::numeric),2) AS avg_rating, ROUND(AVG(purchase_amount),2) AS avg_spend, SUM(CASE WHEN discount_applied='Yes' THEN 1 ELSE 0 END) AS discounted, SUM(CASE WHEN subscription_status='Yes' THEN 1 ELSE 0 END) AS subscribers FROM customer")

total_customers = int(kpi["total_customers"][0])
total_revenue   = float(kpi["total_revenue"][0])
avg_rating      = float(kpi["avg_rating"][0])
avg_spend       = float(kpi["avg_spend"][0])
discounted      = int(kpi["discounted"][0])
subscribers     = int(kpi["subscribers"][0])

# ── Colors ────────────────────────────────────────────────────────────────────
C1, C2, C3, C4, C5, C6 = "#2C3E7A","#3498DB","#1ABC9C","#E67E22","#9B59B6","#E74C3C"
BG, CARD, PLOT = "#F4F6FB","#FFFFFF","#FAFBFF"

TMPL = dict(
    plot_bgcolor=PLOT, paper_bgcolor=CARD,
    font=dict(family="Segoe UI, Arial", size=12, color="#2C3E50"),
    title=dict(font=dict(size=14, color="#2C3E7A", family="Segoe UI, Arial"), x=0.03, xanchor="left"),
    margin=dict(l=20, r=20, t=55, b=20),
    xaxis=dict(showgrid=True, gridcolor="#ECF0F1", zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="#ECF0F1", zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
    hoverlabel=dict(bgcolor="white", font_size=12),
)

def T(fig, title, sub=""):
    t = f"<b>{title}</b>" + (f"<br><sup style='color:#7F8C8D'>{sub}</sup>" if sub else "")
    fig.update_layout(**TMPL, title_text=t)
    return fig

# ── Charts ────────────────────────────────────────────────────────────────────

# Q1
fig1 = go.Figure()
for i, row in q1.iterrows():
    fig1.add_trace(go.Bar(x=[row["gender"]], y=[row["revenue"]], name=row["gender"],
        marker_color=[C1,C3][i], text=[f"${row['revenue']:,.0f}"], textposition="outside",
        hovertemplate=f"<b>{row['gender']}</b><br>Revenue: ${row['revenue']:,.0f}<extra></extra>"))
T(fig1,"Q1 — Revenue by Gender","Which gender drives more total spending?")
fig1.update_layout(showlegend=False, yaxis_title="Total Revenue (USD)", xaxis_title="", bargap=0.5)
fig1.update_yaxes(tickprefix="$", tickformat=",")

# Q2
fig2 = go.Figure()
fig2.add_trace(go.Histogram(x=q2["purchase_amount"], nbinsx=15, marker_color=C2, opacity=0.85,
    hovertemplate="$%{x} range<br>Count: %{y}<extra></extra>"))
avg_val = q2["purchase_amount"].mean()
fig2.add_vline(x=avg_val, line_dash="dash", line_color=C6,
    annotation_text=f"  Avg: ${avg_val:.0f}", annotation_font_color=C6)
T(fig2, f"Q2 — Discount Buyers Above Average Spend  ({len(q2)} customers)",
  "Distribution of spend for customers who used discounts AND exceeded average")
fig2.update_layout(xaxis_title="Purchase Amount (USD)", yaxis_title="Number of Customers")
fig2.update_xaxes(tickprefix="$")

# Q3
q3s = q3.sort_values("avg_rating")
fig3 = go.Figure(go.Bar(x=q3s["avg_rating"], y=q3s["item_purchased"], orientation="h",
    marker=dict(color=[C1,C2,C3,C4,C5]),
    text=[f"⭐ {v}" for v in q3s["avg_rating"]], textposition="outside",
    hovertemplate="<b>%{y}</b><br>Avg Rating: %{x}/5.0<extra></extra>"))
T(fig3,"Q3 — Top 5 Products by Review Rating","Best-rated items based on customer feedback")
fig3.update_layout(xaxis_title="Average Rating (out of 5.0)", xaxis_range=[0,5.6], showlegend=False)

# Q4
fig4 = go.Figure()
sc = {"Express":C4,"Standard":C2}
for _, row in q4.iterrows():
    fig4.add_trace(go.Bar(x=[row["shipping_type"]], y=[row["avg_purchase"]],
        marker_color=sc.get(row["shipping_type"],C1),
        text=[f"${row['avg_purchase']}"], textposition="outside",
        hovertemplate=f"<b>{row['shipping_type']}</b><br>Avg: ${row['avg_purchase']}<extra></extra>"))
T(fig4,"Q4 — Avg Spend: Express vs Standard Shipping","Does shipping preference reflect spending behaviour?")
fig4.update_layout(showlegend=False, yaxis_title="Avg Purchase (USD)", bargap=0.5)
fig4.update_yaxes(tickprefix="$")

# Q5
fig5 = go.Figure()
fig5.add_trace(go.Bar(name="Total Revenue", x=q5["subscription_status"], y=q5["total_revenue"],
    marker_color=[C1,C3], yaxis="y",
    text=[f"${v:,.0f}" for v in q5["total_revenue"]], textposition="outside",
    hovertemplate="<b>%{x}</b><br>Total Revenue: $%{y:,.0f}<extra></extra>"))
fig5.add_trace(go.Scatter(name="Avg Spend", x=q5["subscription_status"], y=q5["avg_spend"],
    mode="markers+text", marker=dict(size=18, color=C4, symbol="diamond"),
    text=[f"${v}" for v in q5["avg_spend"]], textposition="top center", yaxis="y2",
    hovertemplate="<b>%{x}</b><br>Avg Spend: $%{y}<extra></extra>"))
T(fig5,"Q5 — Subscribers vs Non-Subscribers","Revenue and average spend — do subscribers spend more?")
fig5.update_layout(
    yaxis=dict(title="Total Revenue (USD)", tickprefix="$", tickformat=","),
    yaxis2=dict(title="Avg Spend (USD)", overlaying="y", side="right", showgrid=False, tickprefix="$"),
    legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"), bargap=0.5)

# Q6
q6s = q6.sort_values("discount_rate")
fig6 = go.Figure(go.Bar(x=q6s["discount_rate"], y=q6s["item_purchased"], orientation="h",
    marker=dict(color=q6s["discount_rate"],
        colorscale=[[0,"#F39C12"],[0.5,"#E67E22"],[1,"#C0392B"]],
        showscale=True, colorbar=dict(title="Rate %", thickness=12)),
    text=[f"{v}%" for v in q6s["discount_rate"]], textposition="outside",
    hovertemplate="<b>%{y}</b><br>Discount Rate: %{x}%<extra></extra>"))
T(fig6,"Q6 — Products with Highest Discount Usage","% of purchases where a discount code was applied")
fig6.update_layout(xaxis_title="Discount Rate (%)", showlegend=False, xaxis_range=[0,118])

# Q7
seg_c = {"New":C3,"Returning":C2,"Loyal":C1}
fig7 = go.Figure(go.Pie(labels=q7["segment"], values=q7["num_customers"],
    marker=dict(colors=[seg_c.get(s,C4) for s in q7["segment"]], line=dict(color="white",width=2)),
    textinfo="label+percent+value", textfont=dict(size=13), hole=0.42,
    hovertemplate="<b>%{label}</b><br>Customers: %{value:,}<br>%{percent}<extra></extra>"))
T(fig7,"Q7 — Customer Loyalty Segments","New=1 purchase  ·  Returning=2-10  ·  Loyal=10+")
fig7.update_layout(annotations=[dict(text=f"<b>{total_customers:,}<br>Total</b>",
    x=0.5,y=0.5,font_size=14,showarrow=False,font_color=C1)])

# Q8
cat_c = {"Clothing":C1,"Accessories":C3,"Footwear":C4,"Outerwear":C2}
fig8 = px.bar(q8, x="total_orders", y="item_purchased", color="category", orientation="h",
    color_discrete_map=cat_c, text="total_orders",
    labels={"total_orders":"Total Orders","item_purchased":"Product","category":"Category"})
fig8.update_traces(textposition="outside",
    hovertemplate="<b>%{y}</b><br>Orders: %{x:,}<extra></extra>")
T(fig8,"Q8 — Top 3 Products per Category","Best-selling items within each shopping category")
fig8.update_layout(yaxis=dict(categoryorder="total ascending"),
    legend=dict(orientation="h",y=1.1,x=0.5,xanchor="center"), xaxis_title="Total Orders")

# Q9
fig9 = go.Figure(go.Pie(labels=q9["subscription_status"], values=q9["repeat_buyers"],
    marker=dict(colors=[C1,C3], line=dict(color="white",width=2)),
    textinfo="label+percent+value", textfont=dict(size=13), hole=0.42,
    hovertemplate="<b>%{label}</b><br>Repeat Buyers: %{value:,}<br>%{percent}<extra></extra>"))
T(fig9,"Q9 — Repeat Buyers & Subscription","Among customers with 5+ purchases — are they subscribed?")
total_repeat = int(q9["repeat_buyers"].sum())
fig9.update_layout(annotations=[dict(text=f"<b>{total_repeat:,}<br>Repeat</b>",
    x=0.5,y=0.5,font_size=13,showarrow=False,font_color=C1)])

# Q10
age_c = [C1,C2,C3,C4]
fig10 = go.Figure()
for i,(_, row) in enumerate(q10.iterrows()):
    fig10.add_trace(go.Bar(x=[row["age_group"]], y=[row["total_revenue"]],
        marker_color=age_c[i%4], text=[f"${row['total_revenue']:,.0f}"], textposition="outside",
        hovertemplate=f"<b>{row['age_group']}</b><br>Revenue: ${row['total_revenue']:,.0f}<extra></extra>"))
T(fig10,"Q10 — Revenue by Age Group","Which age segment contributes the most to total revenue?")
fig10.update_layout(showlegend=False, yaxis_title="Total Revenue (USD)", xaxis_title="Age Group", bargap=0.4)
fig10.update_yaxes(tickprefix="$", tickformat=",")

# ── UI Helpers ────────────────────────────────────────────────────────────────
def kpi_card(icon, title, value, sub, color):
    return html.Div([
        html.Div(icon, style={"fontSize":"28px","marginBottom":"6px"}),
        html.P(title, style={"margin":"0","fontSize":"10px","color":"#7F8C8D",
            "fontWeight":"700","letterSpacing":"0.8px","textTransform":"uppercase"}),
        html.H2(value, style={"margin":"4px 0","color":color,"fontSize":"22px","fontWeight":"800"}),
        html.P(sub, style={"margin":"0","fontSize":"10px","color":"#95A5A6"}),
    ], style={"background":"white","borderRadius":"12px","padding":"18px 16px",
              "boxShadow":"0 2px 12px rgba(0,0,0,0.07)","flex":"1","minWidth":"140px",
              "borderLeft":f"5px solid {color}"})

def chart_card(fig, q_label, insight):
    return html.Div([
        dcc.Graph(figure=fig, config={"displayModeBar":False}, style={"height":"340px"}),
        html.Div([
            html.Span(q_label, style={"background":C1,"color":"white","borderRadius":"4px",
                "padding":"2px 9px","fontSize":"11px","fontWeight":"700","marginRight":"8px"}),
            html.Span(f"💡 {insight}", style={"fontSize":"11px","color":"#7F8C8D","fontStyle":"italic"})
        ], style={"padding":"8px 16px 14px"})
    ], style={"background":"white","borderRadius":"12px",
              "boxShadow":"0 2px 12px rgba(0,0,0,0.07)","overflow":"hidden","flex":"1","minWidth":"280px"})

def row_div(*cards):
    return html.Div(list(cards), style={"display":"flex","gap":"16px","padding":"0 32px 20px","flexWrap":"wrap"})

def section_header(text):
    return html.Div([
        html.H3(text, style={"color":C1,"margin":"0","fontSize":"14px","fontWeight":"700","letterSpacing":"0.3px"}),
        html.Div(style={"height":"2px","background":f"linear-gradient(90deg,{C1},{C2},transparent)","marginTop":"6px","borderRadius":"2px"})
    ], style={"padding":"20px 32px 10px"})

# ── App ───────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__)
app.title = "Customer Shopping Analytics"

app.layout = html.Div(style={"backgroundColor":BG,"fontFamily":"Segoe UI, Arial","minHeight":"100vh"}, children=[

    # Header
    html.Div([
        html.Div([
            html.Div("🛍️", style={"fontSize":"38px","marginRight":"18px"}),
            html.Div([
                html.H1("Customer Shopping Analytics Dashboard",
                    style={"color":"white","margin":"0","fontSize":"22px","fontWeight":"800","letterSpacing":"0.3px"}),
                html.P("10 Business Questions  ·  PostgreSQL  ·  Interactive & Filterable  ·  Rajan Nanda",
                    style={"color":"rgba(255,255,255,0.72)","margin":"5px 0 0","fontSize":"12px"})
            ])
        ], style={"display":"flex","alignItems":"center"}),
        html.Div([
            html.Span("📋 699 Rows", style={"background":"rgba(255,255,255,0.15)","color":"white",
                "borderRadius":"20px","padding":"6px 14px","fontSize":"12px","marginRight":"8px"}),
            html.Span("🗂 18 Columns", style={"background":"rgba(255,255,255,0.15)","color":"white",
                "borderRadius":"20px","padding":"6px 14px","fontSize":"12px"}),
        ])
    ], style={"background":f"linear-gradient(135deg,{C1} 0%,#1A6FA8 100%)",
              "padding":"22px 32px","display":"flex","justifyContent":"space-between","alignItems":"center"}),

    # KPI Row
    html.Div([
        kpi_card("👥","Total Customers",   f"{total_customers:,}",    "Unique customers in dataset",       C1),
        kpi_card("💰","Total Revenue",     f"${total_revenue:,.0f}",  "Sum of all purchase amounts",       C2),
        kpi_card("⭐","Avg Review Rating", f"{avg_rating} / 5.0",     "Across all products & purchases",   C3),
        kpi_card("🛒","Avg Order Value",   f"${avg_spend}",           "Average spend per transaction",     C4),
        kpi_card("🏷️","Discount Orders",  f"{discounted:,}",         "Purchases with discount applied",   C6),
        kpi_card("✅","Subscribers",       f"{subscribers:,}",        "Active subscription status = Yes",  C5),
    ], style={"display":"flex","gap":"14px","padding":"22px 32px 8px","flexWrap":"wrap"}),

    # Section 1
    section_header("📈  Revenue & Customer Overview"),
    row_div(
        chart_card(fig1,  "Q1", "Male vs Female — compare total spending contribution"),
        chart_card(fig7,  "Q7", "Segment customers into New, Returning, and Loyal groups"),
        chart_card(fig10, "Q10","Young Adult, Adult, Middle-aged, Senior revenue comparison"),
    ),

    # Section 2
    section_header("🎯  Subscriptions, Discounts & Loyalty"),
    row_div(
        chart_card(fig5, "Q5", "Do subscribers spend more on average and generate more revenue?"),
        chart_card(fig9, "Q9", "Of repeat buyers (5+ purchases) — how many are subscribed?"),
        chart_card(fig2, "Q2", "Discount users who still spent above the dataset average"),
    ),

    # Section 3
    section_header("🏆  Product Ratings & Discount Patterns"),
    row_div(
        chart_card(fig3, "Q3", "Top 5 highest-rated products based on customer reviews"),
        chart_card(fig6, "Q6", "Which products are most frequently bought with a discount?"),
    ),

    # Section 4
    section_header("📦  Category Leaders & Shipping Behaviour"),
    row_div(
        chart_card(fig8, "Q8", "Top 3 best-selling products within each shopping category"),
        chart_card(fig4, "Q4", "Express vs Standard shipping — which customers spend more?"),
    ),

    # Footer
    html.Div([
        html.P("Customer Shopping Analytics  ·  Python Dash & Plotly  ·  PostgreSQL  ·  Built by Rajan Nanda",
            style={"color":"rgba(255,255,255,0.65)","margin":"0","fontSize":"12px","textAlign":"center"})
    ], style={"background":C1,"padding":"16px","marginTop":"24px"}),
])

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  ✅  Dashboard running!")
    print("  🌐  Open: http://127.0.0.1:8050")
    print("="*50 + "\n")
    app.run(debug=False)
