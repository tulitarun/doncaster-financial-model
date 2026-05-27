import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Doncaster East Dev Model", layout="wide", initial_sidebar_state="expanded")

# Title & Header
st.markdown("# 🏗️ Doncaster East Dual-Occupancy Development")
st.markdown("**Interactive Financial Model — Offline Version**")
st.markdown("---")

# Initialize session state
if 'inputs' not in st.session_state:
    st.session_state.inputs = {
        'land_price': 1400000,
        'build_per_unit': 950000,
        'sale_per_unit': 2000000,
        'interest_rate': 0.0775,
        'timeline_months': 34,
        'equity_pct': 0.20,
        'contingency_pct': 0.10,
        'min_return_rate': 0.060,
    }

if 'soft_costs' not in st.session_state:
    st.session_state.soft_costs = {
        'demolition': 25000,
        'subdivision_survey': 65000,
        'architecture_design': 55000,
        'engineering_permits': 30000,
        'council_contributions': 28000,
        'landscaping': 55000,
        'accounting_legal': 20000,
        'insurance': 12000,
        'misc1_cost': 20000,
        'misc1_header': 'Project Management',
        'misc2_cost': 0,
        'misc2_header': 'Reserve Buffer',
        'misc3_cost': 0,
        'misc3_header': 'Contingency (Additional)',
        'misc4_cost': 0,
        'misc4_header': 'Utilities & Connections',
    }

def calc_stamp_duty(land_price):
    if land_price <= 25000:
        return land_price * 0.014
    elif land_price <= 130000:
        return 350 + (land_price - 25000) * 0.024
    elif land_price <= 960000:
        return 2870 + (land_price - 130000) * 0.06
    else:
        return 52800 + (land_price - 960000) * 0.06

def calc_project(land, build, sale, rate, months, equity, contingency, soft_costs_dict):
    """Full project calculation with dynamic soft costs"""
    # Land acquisition
    stamp_duty = calc_stamp_duty(land)
    legal_land = 8000
    land_cost = land + stamp_duty + legal_land
    
    # Construction
    total_construction = build * 2
    contingency_amt = total_construction * contingency
    
    # Soft costs (sum from all items in dict)
    soft_costs = (
        soft_costs_dict['demolition'] +
        soft_costs_dict['subdivision_survey'] +
        soft_costs_dict['architecture_design'] +
        soft_costs_dict['engineering_permits'] +
        soft_costs_dict['council_contributions'] +
        soft_costs_dict['landscaping'] +
        soft_costs_dict['accounting_legal'] +
        soft_costs_dict['insurance'] +
        soft_costs_dict['misc1_cost'] +
        soft_costs_dict['misc2_cost'] +
        soft_costs_dict['misc3_cost'] +
        soft_costs_dict['misc4_cost']
    )
    
    # Hard costs
    hard_costs = land_cost + total_construction + contingency_amt + soft_costs
    
    # Finance
    equity_amt = hard_costs * equity
    loan = hard_costs * (1 - equity)
    finance_cost = loan * 0.65 * rate * (months / 12)
    
    # Revenue
    gross_revenue = sale * 2
    
    # Selling costs
    agent_fees = gross_revenue * 0.025
    marketing_legal = 15000 + 8000
    
    # GST CALCULATION (Dynamic)
    # GST collected on sale (margin scheme)
    gst_collected = max(0, (gross_revenue - land) / 11)
    
    # GST paid on inputs (can claim back once registered)
    gst_on_construction = (total_construction + contingency_amt) * 0.10
    gst_on_soft_costs = soft_costs * 0.10
    total_gst_paid = gst_on_construction + gst_on_soft_costs
    
    # NET GST payable (after claiming input credits)
    net_gst_payable = max(0, gst_collected - total_gst_paid)
    
    gst = net_gst_payable  # For backwards compatibility
    total_selling = agent_fees + marketing_legal + net_gst_payable
    
    # Total costs
    total_costs = hard_costs + finance_cost + total_selling
    
    # Profit
    net_profit = gross_revenue - total_costs
    
    return {
        'land_cost': land_cost,
        'stamp_duty': stamp_duty,
        'total_construction': total_construction,
        'contingency': contingency_amt,
        'soft_costs': soft_costs,
        'hard_costs': hard_costs,
        'equity_amt': equity_amt,
        'loan': loan,
        'finance_cost': finance_cost,
        'gross_revenue': gross_revenue,
        'agent_fees': agent_fees,
        'gst_collected': gst_collected,
        'gst_on_construction': gst_on_construction,
        'gst_on_soft_costs': gst_on_soft_costs,
        'total_gst_paid': total_gst_paid,
        'net_gst_payable': net_gst_payable,
        'total_selling': total_selling,
        'total_costs': total_costs,
        'net_profit': net_profit,
        'roi': (net_profit / total_costs * 100) if total_costs > 0 else 0,
        'roe_total': (net_profit / equity_amt * 100) if equity_amt > 0 else 0,
        'roe_pa': (net_profit / equity_amt * 100 / (months / 12)) if equity_amt > 0 and months > 0 else 0,
    }

# Helper function for synced slider + input
def slider_with_input(label, min_val, max_val, current_val_pct, step, key_suffix, display_pct=True):
    """Create a slider with synced input box. Values in % (multiply by 100)"""
    col_slider, col_input = st.columns([3, 1])
    
    with col_slider:
        slider_val = st.slider(
            label, 
            min_value=min_val, 
            max_value=max_val, 
            value=current_val_pct,
            step=step,
            format="%.2f%%" if display_pct else "%.0f",
            label_visibility="collapsed",
            key=f"{key_suffix}_slider"
        )
    
    with col_input:
        input_val = st.number_input(
            f"{label} input",
            value=current_val_pct,
            step=step,
            min_value=min_val,
            max_value=max_val,
            format="%.2f",
            label_visibility="collapsed",
            key=f"{key_suffix}_input"
        )
    
    # Return the value that was most recently changed
    # (slider takes priority if it was moved)
    final_val = slider_val if slider_val != current_val_pct else input_val
    return final_val

# Sidebar for inputs
st.sidebar.markdown("## 📋 INPUT ASSUMPTIONS")
st.sidebar.markdown("Drag sliders OR type exact values. All % values shown with 2 decimals.")

with st.sidebar:
    st.subheader("Land & Acquisition")
    land = st.number_input("Land purchase price ($)", value=st.session_state.inputs['land_price'], step=50000, min_value=500000, max_value=3000000)
    st.session_state.inputs['land_price'] = land
    st.caption("Source: Domain/Allhomes 2025-26 sales, EDSC zone")
    
    st.subheader("Construction Costs")
    build = st.number_input("Build cost per unit ($)", value=st.session_state.inputs['build_per_unit'], step=25000, min_value=400000, max_value=1500000)
    st.session_state.inputs['build_per_unit'] = build
    st.caption("Range: $900K-$1.1M (local builder intel)")
    
    # ============================================================
    # CONTINGENCY: Slider + Input (Synced)
    # ============================================================
    st.markdown("**Contingency %** (Slider or Input)")
    contingency_pct = slider_with_input(
        "Contingency",
        min_val=5.0,
        max_val=20.0,
        current_val_pct=st.session_state.inputs['contingency_pct'] * 100,
        step=0.1,
        key_suffix="contingency",
        display_pct=True
    )
    st.session_state.inputs['contingency_pct'] = contingency_pct / 100
    
    # ============================================================
    # SOFT COSTS BREAKDOWN (NEW)
    # ============================================================
    st.subheader("Soft Costs Breakdown")
    st.caption("💡 Edit each item below. Total auto-sums.")
    
    soft_demo = st.number_input("Demolition ($)", value=st.session_state.soft_costs['demolition'], step=1000, min_value=0, max_value=100000, key="sc_demo")
    st.session_state.soft_costs['demolition'] = soft_demo
    
    soft_sub = st.number_input("Subdivision & Survey ($)", value=st.session_state.soft_costs['subdivision_survey'], step=1000, min_value=0, max_value=150000, key="sc_sub")
    st.session_state.soft_costs['subdivision_survey'] = soft_sub
    
    soft_arch = st.number_input("Architecture & Design ($)", value=st.session_state.soft_costs['architecture_design'], step=1000, min_value=0, max_value=150000, key="sc_arch")
    st.session_state.soft_costs['architecture_design'] = soft_arch
    
    soft_eng = st.number_input("Engineering & Permits ($)", value=st.session_state.soft_costs['engineering_permits'], step=1000, min_value=0, max_value=100000, key="sc_eng")
    st.session_state.soft_costs['engineering_permits'] = soft_eng
    
    soft_council = st.number_input("Council Contributions ($)", value=st.session_state.soft_costs['council_contributions'], step=1000, min_value=0, max_value=100000, key="sc_council")
    st.session_state.soft_costs['council_contributions'] = soft_council
    
    soft_land = st.number_input("Landscaping ($)", value=st.session_state.soft_costs['landscaping'], step=1000, min_value=0, max_value=150000, key="sc_land")
    st.session_state.soft_costs['landscaping'] = soft_land
    
    soft_acc = st.number_input("Accounting & Legal ($)", value=st.session_state.soft_costs['accounting_legal'], step=1000, min_value=0, max_value=50000, key="sc_acc")
    st.session_state.soft_costs['accounting_legal'] = soft_acc
    
    soft_ins = st.number_input("Insurance ($)", value=st.session_state.soft_costs['insurance'], step=1000, min_value=0, max_value=50000, key="sc_ins")
    st.session_state.soft_costs['insurance'] = soft_ins
    
    st.markdown("**Miscellaneous / Custom Items:**")
    
    # Misc 1
    misc1_header = st.text_input("Item 1 Name", value=st.session_state.soft_costs['misc1_header'], key="misc1_hdr", placeholder="e.g. Project Management")
    st.session_state.soft_costs['misc1_header'] = misc1_header
    soft_misc1 = st.number_input(f"{misc1_header} ($)", value=st.session_state.soft_costs['misc1_cost'], step=1000, min_value=0, max_value=100000, key="sc_misc1")
    st.session_state.soft_costs['misc1_cost'] = soft_misc1
    
    # Misc 2
    misc2_header = st.text_input("Item 2 Name", value=st.session_state.soft_costs['misc2_header'], key="misc2_hdr", placeholder="e.g. Reserve Buffer")
    st.session_state.soft_costs['misc2_header'] = misc2_header
    soft_misc2 = st.number_input(f"{misc2_header} ($)", value=st.session_state.soft_costs['misc2_cost'], step=1000, min_value=0, max_value=100000, key="sc_misc2")
    st.session_state.soft_costs['misc2_cost'] = soft_misc2
    
    # Misc 3
    misc3_header = st.text_input("Item 3 Name", value=st.session_state.soft_costs['misc3_header'], key="misc3_hdr", placeholder="e.g. Extra Contingency")
    st.session_state.soft_costs['misc3_header'] = misc3_header
    soft_misc3 = st.number_input(f"{misc3_header} ($)", value=st.session_state.soft_costs['misc3_cost'], step=1000, min_value=0, max_value=100000, key="sc_misc3")
    st.session_state.soft_costs['misc3_cost'] = soft_misc3
    
    # Misc 4
    misc4_header = st.text_input("Item 4 Name", value=st.session_state.soft_costs['misc4_header'], key="misc4_hdr", placeholder="e.g. Utilities")
    st.session_state.soft_costs['misc4_header'] = misc4_header
    soft_misc4 = st.number_input(f"{misc4_header} ($)", value=st.session_state.soft_costs['misc4_cost'], step=1000, min_value=0, max_value=100000, key="sc_misc4")
    st.session_state.soft_costs['misc4_cost'] = soft_misc4
    
    # Show total soft costs
    total_soft = (soft_demo + soft_sub + soft_arch + soft_eng + soft_council + 
                  soft_land + soft_acc + soft_ins + soft_misc1 + soft_misc2 + soft_misc3 + soft_misc4)
    st.info(f"**Total Soft Costs: ${total_soft:,.0f}**")
    
    st.markdown("---")
    
    st.subheader("Revenue")
    sale = st.number_input("Sale price per unit ($)", value=st.session_state.inputs['sale_per_unit'], step=50000, min_value=1200000, max_value=2500000)
    st.session_state.inputs['sale_per_unit'] = sale
    st.caption("EDSC zone 4bed new: $1.3M-$2.3M range")
    
    st.subheader("Finance")
    
    # ============================================================
    # INTEREST RATE: Slider + Input (Synced)
    # ============================================================
    st.markdown("**Interest Rate p.a. %** (Slider or Input)")
    interest_rate_pct = slider_with_input(
        "Interest rate",
        min_val=5.0,
        max_val=12.0,
        current_val_pct=st.session_state.inputs['interest_rate'] * 100,
        step=0.05,
        key_suffix="interest_rate",
        display_pct=True
    )
    st.session_state.inputs['interest_rate'] = interest_rate_pct / 100
    
    # Timeline
    st.markdown("**Project Timeline (months)**")
    months = st.slider("Months", 20, 50, st.session_state.inputs['timeline_months'], 1, label_visibility="collapsed")
    st.session_state.inputs['timeline_months'] = months
    
    # ============================================================
    # EQUITY CONTRIBUTION: Slider + Input (Synced)
    # ============================================================
    st.markdown("**Equity Contribution %** (Slider or Input)")
    equity_pct = slider_with_input(
        "Equity %",
        min_val=10.0,
        max_val=50.0,
        current_val_pct=st.session_state.inputs['equity_pct'] * 100,
        step=0.5,
        key_suffix="equity",
        display_pct=True
    )
    st.session_state.inputs['equity_pct'] = equity_pct / 100
    
    st.subheader("Partner Safety Net")
    
    # ============================================================
    # MIN RETURN RATE: Slider + Input (Synced)
    # ============================================================
    st.markdown("**Min Guaranteed Return (p.a.) %** (Slider or Input)")
    min_ret_pct = slider_with_input(
        "Min return %",
        min_val=2.0,
        max_val=12.0,
        current_val_pct=st.session_state.inputs['min_return_rate'] * 100,
        step=0.1,
        key_suffix="min_return",
        display_pct=True
    )
    st.session_state.inputs['min_return_rate'] = min_ret_pct / 100
    st.caption("Above TD (~5.20%), below ASX (~9.50%)")

# Calculate base case
result = calc_project(
    st.session_state.inputs['land_price'],
    st.session_state.inputs['build_per_unit'],
    st.session_state.inputs['sale_per_unit'],
    st.session_state.inputs['interest_rate'],
    st.session_state.inputs['timeline_months'],
    st.session_state.inputs['equity_pct'],
    st.session_state.inputs['contingency_pct'],
    st.session_state.soft_costs
)

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 P&L Summary", "📈 Scenarios", "🔍 Sensitivity", "👥 Partners", "📚 Research"])

# ============================================================================
# TAB 1: P&L SUMMARY
# ============================================================================
with tab1:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Gross Revenue", f"${result['gross_revenue']:,.0f}", delta="2 units")
        st.metric("Equity Required", f"${result['equity_amt']:,.0f}", delta=f"{st.session_state.inputs['equity_pct']*100:.2f}% of hard costs")
    
    with col2:
        st.metric("Total Costs", f"${result['total_costs']:,.0f}", delta="All-in")
        st.metric("Peak Bank Loan", f"${result['loan']:,.0f}", delta=f"{st.session_state.inputs['interest_rate']*100:.2f}% p.a.")
    
    with col3:
        profit_color = "green" if result['net_profit'] >= 0 else "red"
        st.metric("Net Profit", f"${result['net_profit']:,.0f}", 
                 delta=f"{result['roi']:.1f}% ROI on cost", delta_color=profit_color)
        roe_color = "green" if result['roe_pa'] >= 15 else "orange" if result['roe_pa'] >= 0 else "red"
        st.metric("ROE p.a.", f"{result['roe_pa']:.1f}%", 
                 delta=f"{result['roe_total']:.1f}% total", delta_color=roe_color)
    
    st.markdown("---")
    
    # Cost breakdown chart
    col1, col2 = st.columns(2)
    
    with col1:
        costs = {
            'Land + Stamp Duty': result['land_cost'],
            'Construction': result['total_construction'],
            'Contingency': result['contingency'],
            'Soft Costs': result['soft_costs'],
            'Finance Interest': result['finance_cost'],
            'Selling & GST': result['total_selling'],
        }
        fig = go.Figure(data=[go.Pie(labels=list(costs.keys()), values=list(costs.values()), hole=0.3)])
        fig.update_layout(title="Cost Breakdown", height=400, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Waterfall
        categories = ['Revenue', 'Land\n& Acq.', 'Construction\n& Soft', 'Finance\n& Selling', 'Net Profit']
        values = [
            result['gross_revenue'],
            -result['land_cost'],
            -(result['total_construction'] + result['contingency'] + result['soft_costs']),
            -(result['finance_cost'] + result['total_selling']),
            result['net_profit']
        ]
        fig = go.Figure(go.Waterfall(
            x=categories,
            y=values,
            text=[f"${v/1e6:.2f}M" for v in values],
            textposition="outside",
            connector={"line": {"color": "rgba(0,0,0,0.2)"}},
        ))
        fig.update_layout(title="Profit Waterfall", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed P&L table
    st.subheader("Detailed Cost Breakdown")
    pl_data = {
        'Category': [
            'REVENUE',
            'Gross Revenue (2 units)',
            '',
            'HARD COSTS',
            'Land Purchase',
            'Stamp Duty (VIC)',
            'Legal & Conveyancing',
            'Construction (2 units)',
            'Contingency (%.2f%%)' % (st.session_state.inputs['contingency_pct']*100),
            'Soft Costs',
            '  - Demolition',
            '  - Subdivision & Survey',
            '  - Architecture & Design',
            '  - Engineering & Permits',
            '  - Council Contributions',
            '  - Landscaping',
            '  - Accounting & Legal',
            '  - Insurance',
            f'  - {st.session_state.soft_costs["misc1_header"]}',
            f'  - {st.session_state.soft_costs["misc2_header"]}',
            f'  - {st.session_state.soft_costs["misc3_header"]}',
            f'  - {st.session_state.soft_costs["misc4_header"]}',
            'Total Hard Costs',
            '',
            'FINANCING',
            'Development Finance Interest (%.2f%% p.a.)' % (st.session_state.inputs['interest_rate']*100),
            '',
            'SELLING COSTS',
            'Agent Commission (2.5%)',
            'Marketing & Legal',
            'GST (Net payable to ATO)',
            'Total Selling Costs',
            '',
            'TOTAL ALL COSTS',
            '',
            'NET PROFIT / (LOSS)',
        ],
        'Amount': [
            '',
            f"${result['gross_revenue']:,.0f}",
            '',
            '',
            f"${st.session_state.inputs['land_price']:,.0f}",
            f"${result['stamp_duty']:,.0f}",
            "$8,000",
            f"${result['total_construction']:,.0f}",
            f"${result['contingency']:,.0f}",
            f"${result['soft_costs']:,.0f}",
            f"${st.session_state.soft_costs['demolition']:,.0f}",
            f"${st.session_state.soft_costs['subdivision_survey']:,.0f}",
            f"${st.session_state.soft_costs['architecture_design']:,.0f}",
            f"${st.session_state.soft_costs['engineering_permits']:,.0f}",
            f"${st.session_state.soft_costs['council_contributions']:,.0f}",
            f"${st.session_state.soft_costs['landscaping']:,.0f}",
            f"${st.session_state.soft_costs['accounting_legal']:,.0f}",
            f"${st.session_state.soft_costs['insurance']:,.0f}",
            f"${st.session_state.soft_costs['misc1_cost']:,.0f}",
            f"${st.session_state.soft_costs['misc2_cost']:,.0f}",
            f"${st.session_state.soft_costs['misc3_cost']:,.0f}",
            f"${st.session_state.soft_costs['misc4_cost']:,.0f}",
            f"${result['hard_costs']:,.0f}",
            '',
            '',
            f"${result['finance_cost']:,.0f}",
            '',
            '',
            f"${result['agent_fees']:,.0f}",
            "$23,000",
            f"${result['net_gst_payable']:,.0f}",
            f"${result['total_selling']:,.0f}",
            '',
            f"${result['total_costs']:,.0f}",
            '',
            f"${result['net_profit']:,.0f}",
        ],
        '% of Revenue': [
            '',
            '100.0%',
            '',
            '',
            f"{(st.session_state.inputs['land_price']/result['gross_revenue']*100):.1f}%",
            f"{(result['stamp_duty']/result['gross_revenue']*100):.1f}%",
            f"{(8000/result['gross_revenue']*100):.2f}%",
            f"{(result['total_construction']/result['gross_revenue']*100):.1f}%",
            f"{(result['contingency']/result['gross_revenue']*100):.1f}%",
            f"{(result['soft_costs']/result['gross_revenue']*100):.1f}%",
            "", "", "", "", "", "", "", "", "", "", "", "",
            f"{(result['hard_costs']/result['gross_revenue']*100):.1f}%",
            '',
            '',
            f"{(result['finance_cost']/result['gross_revenue']*100):.1f}%",
            '',
            '',
            f"{(result['agent_fees']/result['gross_revenue']*100):.2f}%",
            f"{(23000/result['gross_revenue']*100):.2f}%",
            f"{(result['net_gst_payable']/result['gross_revenue']*100):.1f}%",
            f"{(result['total_selling']/result['gross_revenue']*100):.1f}%",
            '',
            f"{(result['total_costs']/result['gross_revenue']*100):.1f}%",
            '',
            f"{(result['net_profit']/result['gross_revenue']*100):.1f}%",
        ]
    }
    df_pl = pd.DataFrame(pl_data)
    st.dataframe(df_pl, use_container_width=True, hide_index=True)
    
    # Min guarantee check
    st.markdown("---")
    min_guarantee = result['equity_amt'] * st.session_state.inputs['min_return_rate'] * (st.session_state.inputs['timeline_months'] / 12)
    surplus = result['net_profit'] - min_guarantee
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Min Guarantee Required", f"${min_guarantee:,.0f}", delta=f"{st.session_state.inputs['min_return_rate']*100:.2f}% p.a.")
    with col2:
        status = "✅ PASS" if result['net_profit'] >= min_guarantee else "❌ FAIL"
        st.metric("Profit vs Guarantee", status)
    with col3:
        st.metric("Surplus / (Shortfall)", f"${surplus:,.0f}")
    
    # ============================================================
    # GST BREAKDOWN (NEW - DYNAMIC)
    # ============================================================
    st.markdown("---")
    st.subheader("📊 GST Breakdown (Dynamic)")
    st.caption("💡 All figures update automatically as you change build cost, sale price, or soft costs")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("GST Collected (on sale)", f"${result['gst_collected']:,.0f}", delta="Margin scheme")
    with col2:
        st.metric("GST on Inputs (to claim)", f"${result['total_gst_paid']:,.0f}", delta=f"Construction: ${result['gst_on_construction']:,.0f}\nSoft costs: ${result['gst_on_soft_costs']:,.0f}")
    with col3:
        st.metric("NET GST Payable to ATO", f"${result['net_gst_payable']:,.0f}", delta="After input credits")
    
    # Detailed GST table
    st.markdown("**GST Detailed Calculation:**")
    gst_breakdown = {
        'GST Item': [
            'GST COLLECTED (On Sale)',
            'Sale revenue (margin)',
            'GST collected (margin scheme)',
            '',
            'GST ON INPUTS (Can Claim Back)',
            'Construction + Contingency',
            'GST on construction',
            'Soft costs',
            'GST on soft costs',
            'Total GST paid on inputs',
            '',
            'NET GST PAYABLE TO ATO',
            'GST collected',
            'Less: GST on inputs (credit)',
            'Net GST to pay',
        ],
        'Amount': [
            '',
            f"${(result['gross_revenue'] - st.session_state.inputs['land_price']):,.0f}",
            f"${result['gst_collected']:,.0f}",
            '',
            '',
            f"${result['total_construction'] + result['contingency']:,.0f}",
            f"${result['gst_on_construction']:,.0f}",
            f"${result['soft_costs']:,.0f}",
            f"${result['gst_on_soft_costs']:,.0f}",
            f"${result['total_gst_paid']:,.0f}",
            '',
            '',
            f"${result['gst_collected']:,.0f}",
            f"-${result['total_gst_paid']:,.0f}",
            f"${result['net_gst_payable']:,.0f}",
        ]
    }
    df_gst = pd.DataFrame(gst_breakdown)
    st.dataframe(df_gst, use_container_width=True, hide_index=True)
    
    st.info(
        "💡 **How This Works:**\n\n"
        "1. You collect GST on the sale from your buyers\n"
        "2. You paid GST to contractors and suppliers on construction & soft costs\n"
        "3. Once registered, you can **claim back** the GST you paid on inputs\n"
        "4. **NET GST** = What you collected - What you paid = What you owe to ATO\n\n"
        "**Example:** Collected $236K - Paid $180K on inputs = Owe ATO ~$56K"
    )

# ============================================================================
# TAB 2: SCENARIOS
# ============================================================================
with tab2:
    st.subheader("Four Pre-Built Scenarios + Custom")
    
    scenarios = {
        'Base': {
            'land': 1400000, 'build': 950000, 'sale': 2000000, 'rate': 0.0775, 'months': 34, 'equity': 0.20, 'cont': 0.10
        },
        'Bull': {
            'land': 1400000, 'build': 900000, 'sale': 2200000, 'rate': 0.070, 'months': 30, 'equity': 0.20, 'cont': 0.08
        },
        'Bear': {
            'land': 1400000, 'build': 1050000, 'sale': 1800000, 'rate': 0.0875, 'months': 38, 'equity': 0.20, 'cont': 0.12
        },
        'Stress': {
            'land': 1400000, 'build': 1100000, 'sale': 1650000, 'rate': 0.095, 'months': 44, 'equity': 0.25, 'cont': 0.15
        },
        'Custom': {
            'land': st.session_state.inputs['land_price'],
            'build': st.session_state.inputs['build_per_unit'],
            'sale': st.session_state.inputs['sale_per_unit'],
            'rate': st.session_state.inputs['interest_rate'],
            'months': st.session_state.inputs['timeline_months'],
            'equity': st.session_state.inputs['equity_pct'],
            'cont': st.session_state.inputs['contingency_pct'],
        }
    }
    
    scn_results = {}
    for name, params in scenarios.items():
        scn_results[name] = calc_project(
            params['land'], params['build'], params['sale'],
            params['rate'], params['months'], params['equity'], params['cont'],
            st.session_state.soft_costs
        )
    
    # Summary cards
    cols = st.columns(5)
    colors = {'Base': '🔵', 'Bull': '🟢', 'Bear': '🟠', 'Stress': '🔴', 'Custom': '⚪'}
    
    for col, name in zip(cols, scenarios.keys()):
        with col:
            res = scn_results[name]
            color_indicator = colors[name]
            profit_color = "green" if res['net_profit'] >= 0 else "red"
            st.metric(
                f"{color_indicator} {name}",
                f"${res['net_profit']/1e6:.2f}M",
                delta=f"{res['roe_pa']:.2f}% ROE p.a.",
                delta_color=profit_color
            )
    
    st.markdown("---")
    
    # Comparison table
    st.subheader("Scenario Comparison")
    comparison_data = {
        'Scenario': list(scenarios.keys()),
        'Build/Unit': [f"${scenarios[s]['build']/1e3:.0f}K" for s in scenarios.keys()],
        'Sale/Unit': [f"${scenarios[s]['sale']/1e6:.2f}M" for s in scenarios.keys()],
        'Interest %': [f"{scenarios[s]['rate']*100:.2f}%" for s in scenarios.keys()],
        'Timeline': [f"{scenarios[s]['months']} mths" for s in scenarios.keys()],
        'Net Profit': [f"${scn_results[s]['net_profit']/1e6:.2f}M" for s in scenarios.keys()],
        'ROI': [f"{scn_results[s]['roi']:.1f}%" for s in scenarios.keys()],
        'ROE Total': [f"{scn_results[s]['roe_total']:.1f}%" for s in scenarios.keys()],
        'ROE p.a.': [f"{scn_results[s]['roe_pa']:.2f}%" for s in scenarios.keys()],
    }
    df_scn = pd.DataFrame(comparison_data)
    st.dataframe(df_scn, use_container_width=True, hide_index=True)
    
    # Profit comparison chart
    st.subheader("Net Profit by Scenario")
    scn_names = list(scenarios.keys())
    scn_profits = [scn_results[s]['net_profit'] for s in scn_names]
    colors_map = {'Base': '#1f77b4', 'Bull': '#2ca02c', 'Bear': '#ff7f0e', 'Stress': '#d62728', 'Custom': '#9467bd'}
    
    fig = go.Figure(data=[
        go.Bar(x=scn_names, y=scn_profits,
               marker_color=[colors_map.get(s, '#808080') for s in scn_names],
               text=[f"${p/1e6:.2f}M" for p in scn_profits],
               textposition='outside')
    ])
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
    fig.update_layout(title="Net Profit Comparison", yaxis_title="Net Profit ($)", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # ROE comparison
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(data=[
            go.Bar(x=scn_names, y=[scn_results[s]['roe_total']*100 for s in scn_names],
                   marker_color=[colors_map.get(s, '#808080') for s in scn_names],
                   text=[f"{scn_results[s]['roe_total']:.2f}%" for s in scn_names],
                   textposition='outside')
        ])
        fig.update_layout(title="Total ROE by Scenario", yaxis_title="ROE (%)", height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure(data=[
            go.Bar(x=scn_names, y=[scn_results[s]['roe_pa']*100 for s in scn_names],
                   marker_color=[colors_map.get(s, '#808080') for s in scn_names],
                   text=[f"{scn_results[s]['roe_pa']:.2f}%" for s in scn_names],
                   textposition='outside')
        ])
        fig.add_hline(y=6.0, line_dash="dash", line_color="green", annotation_text="Min Guarantee (6.00%)")
        fig.update_layout(title="Annualised ROE by Scenario", yaxis_title="ROE p.a. (%)", height=350)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 3: SENSITIVITY ANALYSIS
# ============================================================================
with tab3:
    st.subheader("Sensitivity: Net Profit by Build Cost × Sale Price")
    st.caption("All other inputs held at current values. Hover over cells for exact amounts.")
    
    builds = np.arange(800, 1150, 50) * 1000
    sales = np.arange(1600, 2450, 100) * 1000
    
    sensitivity_matrix = np.zeros((len(builds), len(sales)))
    
    for i, b in enumerate(builds):
        for j, s in enumerate(sales):
            res = calc_project(
                st.session_state.inputs['land_price'], b, s,
                st.session_state.inputs['interest_rate'],
                st.session_state.inputs['timeline_months'],
                st.session_state.inputs['equity_pct'],
                st.session_state.inputs['contingency_pct'],
                st.session_state.soft_costs
            )
            sensitivity_matrix[i, j] = res['net_profit']
    
    # Heatmap
    fig = go.Figure(data=go.Heatmap(
        z=sensitivity_matrix / 1e6,
        x=[f"${s/1e6:.1f}M" for s in sales],
        y=[f"${b/1e6:.1f}M" for b in builds],
        colorscale='RdYlGn',
        zmid=0,
        text=np.round(sensitivity_matrix / 1e6, 2),
        texttemplate='$%{text:.2f}M',
        textfont={"size": 9},
        colorbar=dict(title="Profit ($M)")
    ))
    fig.update_layout(
        title="Net Profit Heatmap (Build Cost vs Sale Price)",
        xaxis_title="Sale Price per Unit",
        yaxis_title="Build Cost per Unit",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Break-even analysis
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Break-even Analysis")
        # Find approximate break-even
        for b in np.arange(800, 1150, 25) * 1000:
            for s in np.arange(1600, 2450, 25) * 1000:
                res = calc_project(
                    st.session_state.inputs['land_price'], b, s,
                    st.session_state.inputs['interest_rate'],
                    st.session_state.inputs['timeline_months'],
                    st.session_state.inputs['equity_pct'],
                    st.session_state.inputs['contingency_pct'],
                    st.session_state.soft_costs
                )
                if -50000 < res['net_profit'] < 50000:
                    st.info(f"**Break-even approximately at:**\n\n- Build cost: **${b:,.0f}** per unit\n- Sale price: **${s:,.0f}** per unit")
                    break
            else:
                continue
            break
    
    with col2:
        st.subheader("Profit Zones")
        st.success("🟢 **Green zone:** Profit > $200K")
        st.warning("🟡 **Yellow zone:** Break-even to $200K profit")
        st.error("🔴 **Red zone:** Loss")

# ============================================================================
# TAB 4: PARTNER RETURNS
# ============================================================================
with tab4:
    st.subheader("Partner Equity, Returns & Minimum Guarantee")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.markdown("### Partner Equity Split")
        partners = ["You (Lead)", "Partner 2", "Partner 3", "Partner 4", "Partner 5"]
        
        if 'partner_pcts' not in st.session_state:
            st.session_state.partner_pcts = [0.20, 0.20, 0.20, 0.20, 0.20]
        
        partner_pcts = []
        for i, p in enumerate(partners):
            val = st.slider(f"{p} (%)", 0.0, 100.0, st.session_state.partner_pcts[i], 5.0, key=f"partner_{i}", format="%.2f%%")
            partner_pcts.append(val / 100)
            st.session_state.partner_pcts[i] = val / 100
        
        total_pct = sum(partner_pcts)
        if abs(total_pct - 1.0) > 0.01:
            st.warning(f"⚠️ Total = {total_pct*100:.0f}% (normalising to 100%)")
            partner_pcts = [p / total_pct for p in partner_pcts]
    
    with col2:
        st.markdown("### Capital Deployment & Returns")
        
        equity_pool = result['equity_amt']
        min_return_rate = st.session_state.inputs['min_return_rate']
        timeline_yrs = st.session_state.inputs['timeline_months'] / 12
        
        partner_data = []
        for i, p in enumerate(partners):
            capital = equity_pool * partner_pcts[i]
            min_guarantee = capital * min_return_rate * timeline_yrs
            profit_share = result['net_profit'] * partner_pcts[i]
            actual_return = max(min_guarantee, profit_share)
            roe_total = (actual_return / capital * 100) if capital > 0 else 0
            roe_pa = roe_total / timeline_yrs if timeline_yrs > 0 else 0
            
            partner_data.append({
                'Partner': p,
                'Equity %': f"{partner_pcts[i]*100:.0f}%",
                'Capital In': f"${capital:,.0f}",
                'Min Guarantee': f"${min_guarantee:,.0f}",
                'Profit Share': f"${profit_share:,.0f}",
                'Actual Return': f"${actual_return:,.0f}",
                'ROE Total': f"{roe_total:.2f}%",
                'ROE p.a.': f"{roe_pa:.2f}%",
            })
        
        df_partners = pd.DataFrame(partner_data)
        st.dataframe(df_partners, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Partner breakdown charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Capital Distribution")
        capital_amounts = [equity_pool * pct for pct in partner_pcts]
        fig = go.Figure(data=[go.Pie(labels=partners, values=capital_amounts)])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Profit Distribution")
        profit_shares = [result['net_profit'] * pct for pct in partner_pcts]
        fig = go.Figure(data=[go.Pie(labels=partners, values=profit_shares)])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Individual partner cards
    st.subheader("Individual Partner Breakdown")
    partner_cols = st.columns(5)
    
    for i, (p_col, partner) in enumerate(zip(partner_cols, partners)):
        with p_col:
            capital = equity_pool * partner_pcts[i]
            min_guarantee = capital * min_return_rate * timeline_yrs
            profit_share = result['net_profit'] * partner_pcts[i]
            actual_return = max(min_guarantee, profit_share)
            roe_pa = (actual_return / capital * 100 / timeline_yrs) if capital > 0 and timeline_yrs > 0 else 0
            
            with st.container(border=True):
                st.markdown(f"### {partner}")
                st.metric("Capital", f"${capital/1e6:.2f}M")
                st.metric("Actual Return", f"${actual_return/1e6:.2f}M")
                st.metric("ROE p.a.", f"{roe_pa:.2f}%")
                
                if actual_return == min_guarantee:
                    st.caption("⚠️ Receiving min guarantee (not profit)")
                else:
                    st.caption("✅ Profit exceeds guarantee")

# ============================================================================
# TAB 5: MARKET RESEARCH
# ============================================================================
with tab5:
    st.subheader("Market Research & Benchmarks")
    
    research_data = {
        'Category': [
            'BUILD COSTS',
            'Standard 4bed (volume builder)',
            'Custom build (premium)',
            'Townhouse/duplex quality',
            'Your local intel',
            'Model default',
            '',
            'SALE PRICES - EDSC ZONE',
            '4bed recent sales (2024-25)',
            'Brand new premium range',
            'Off-plan listings',
            'Model default',
            '',
            'FINANCE BENCHMARKS',
            'RBA cash rate (May 2026)',
            'Dev finance rates',
            'Your model rate',
            '',
            'ALTERNATIVE RETURNS',
            '3-year term deposit',
            'HISA bonus rates',
            'ASX 200 (10yr avg)',
            'Melbourne property (3yr)',
            'Your min guarantee',
        ],
        'Value': [
            '',
            '$320K-$430K per unit',
            '$2,700-$4,000+ per sqm',
            '$2,600-$2,800 per sqm',
            '$900K-$1.1M per unit',
            f'${st.session_state.inputs["build_per_unit"]/1e3:.0f}K per unit',
            '',
            '',
            '$1.34M-$1.78M (Domain 2024-25)',
            '$1.78M-$2.0M+ (top spec)',
            '$1.1M-$1.3M (modest spec)',
            f'${st.session_state.inputs["sale_per_unit"]/1e6:.1f}M per unit',
            '',
            '',
            '4.10%',
            '7.0%-9.5% p.a.',
            f'{st.session_state.inputs["interest_rate"]*100:.2f}% p.a.',
            '',
            '',
            '5.20%-5.60% p.a.',
            '5.00%-5.50% p.a.',
            '~9-11% p.a.',
            '~1.5%-5% p.a.',
            f'{st.session_state.inputs["min_return_rate"]*100:.2f}% p.a.',
        ],
        'Source': [
            '',
            'Xircon Homes 2026',
            'Pascon/Arch10 2026',
            'Infinity Built 2025-26',
            'Local builder conversations',
            'Mid-range premium estimate',
            '',
            '',
            'Domain.com.au Sold Results',
            'Fletchers/Woodards listings',
            'Allhomes/Trovit May 2026',
            'Your projection',
            '',
            '',
            'RBA May 2026',
            'Typical dev finance range',
            'Your assumption',
            '',
            '',
            'Canstar/Great Southern Bank',
            'Finder May 2026',
            'Vanguard/Motley Fool',
            'CoreLogic historical',
            'Your safety net setting',
        ]
    }
    
    df_research = pd.DataFrame(research_data)
    st.dataframe(df_research, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("Key Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(
            "💡 **Build Cost is Critical**\n\n"
            "At $950K per unit, construction eats ~47% of sale revenue. "
            "Small changes (±$50K) swing profit by $100K+."
        )
        
        st.info(
            "💡 **School Zone Premium**\n\n"
            "EDSC zone brand-new 4beds command $1.3M-$1.78M today. "
            "Your $2M assumption targets top-third of market (luxury spec)."
        )
    
    with col2:
        st.warning(
            "⚠️ **Finance Costs Add Up**\n\n"
            f"At {st.session_state.inputs['interest_rate']*100:.2f}% over {st.session_state.inputs['timeline_months']} months, "
            f"interest totals ~${result['finance_cost']/1e3:.0f}K—nearly {result['finance_cost']/result['gross_revenue']*100:.1f}% of revenue. "
            "Lower rates or faster timeline improve significantly."
        )
        
        st.success(
            "✅ **Min Guarantee Strategy**\n\n"
            f"Your {st.session_state.inputs['min_return_rate']*100:.2f}% p.a. safety net sits above savings (~5.20%) "
            "but well below ASX (~9.50%), balancing security & upside."
        )

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 12px; color: #808080;'>"
    "<p>Doncaster East Dual-Occupancy Financial Model — Offline Version</p>"
    f"<p>Generated {datetime.now().strftime('%d %b %Y %H:%M')} | All % values show 2 decimal places for precision</p>"
    "</div>",
    unsafe_allow_html=True
)
