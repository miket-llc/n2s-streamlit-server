"""
N2S Efficiency Modeling Application
Interactive Streamlit app for quantifying professional services efficiency
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from datetime import datetime

from model import N2SEfficiencyModel
from config import (
    DEFAULT_PHASE_ALLOCATION, DEFAULT_RISK_WEIGHTS, PHASE_ORDER,
    COST_AVOIDANCE_OPTIONS, get_phase_colors, format_currency, format_hours,
    validate_scenario_results
)

# Page configuration
st.set_page_config(
    page_title="N2S Efficiency Model",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_custom_css():
    """Load custom CSS for better styling"""
    st.markdown("""
    <style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .big-metric {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .savings-positive {
        color: #28a745;
    }
    .cost-negative {
        color: #dc3545;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data
def initialize_model():
    """Initialize and cache the model instance"""
    model = N2SEfficiencyModel()
    model.create_sample_data()
    return model


def create_sidebar_controls():
    """Create sidebar input controls for model parameters"""
    from config import (
        get_initiative_description, get_maturity_description,
        RISK_LEVEL_DEFINITIONS, get_phase_risk_info,
        get_risk_level_description, INITIATIVE_FALLBACK, 
        INDUSTRY_BENCHMARKS, COST_AVOIDANCE_OPTIONS
    )
    
    st.sidebar.title("Model Parameters")
    
    # Version indicator in sidebar
    from config import APP_VERSION
    st.sidebar.caption(f"{APP_VERSION}")
    
    # Baseline Efficiency Reminder - Updated
    st.sidebar.info("""
    **Step 1: Assess Your Current Automation Maturity**
    
    Complete the assessment below to understand your starting point 
    and realistic savings potential.
    """)
    
    # Current State Assessment
    st.sidebar.subheader("Current State Assessment")
    
    from config import AUTOMATION_ASSESSMENT, assess_current_maturity
    
    # Collect assessment responses
    assessment_responses = {}
    
    for question_key, question_config in AUTOMATION_ASSESSMENT.items():
        if question_config['type'] == 'slider':
            assessment_responses[question_key] = st.sidebar.slider(
                question_config['question'],
                min_value=question_config['min_value'],
                max_value=question_config['max_value'],
                value=question_config['default'],
                help=question_config['help'],
                key=f"assess_{question_key}"
            )
        elif question_config['type'] == 'selectbox':
            assessment_responses[question_key] = st.sidebar.selectbox(
                question_config['question'],
                options=question_config['options'],
                index=question_config['default'],
                help=question_config['help'],
                key=f"assess_{question_key}"
            )
    
    # Calculate current maturity
    current_maturity = assess_current_maturity(assessment_responses)
    
    # Display maturity assessment results
    st.sidebar.success(f"""
    **Your Current Maturity: Level {current_maturity['maturity_level']} - {current_maturity['maturity_name']}**
    
    Realistic Savings Potential: {current_maturity['current_savings_potential']:.1f}%
    """)
    
    # Major Modeling Decisions
    st.sidebar.subheader("Target & Strategy")
    
    # Target savings with guidance
    max_potential = current_maturity['current_savings_potential'] + 10  # Buffer for initiatives
    target_savings = st.sidebar.slider(
        "Target Project Savings %",
        min_value=5,
        max_value=30,
        value=min(15, int(current_maturity['current_savings_potential'])),
        step=1,
        help=(
            f"Based on your maturity assessment, you can realistically achieve "
            f"up to {current_maturity['current_savings_potential']:.1f}% savings. "
            f"Higher targets may require maturity improvements first."
        )
    )
    
    # Generate scenario configuration based on target and maturity
    from config import calculate_target_feasibility
    
    # We'll need selected initiatives for feasibility check - get a preview first
    available_initiatives = INITIATIVE_FALLBACK  # Will be updated below
    
    feasibility = calculate_target_feasibility(
        current_maturity, target_savings, available_initiatives
    )
    
    # Display feasibility assessment
    if feasibility['feasible']:
        st.sidebar.success(f"✓ Target {target_savings}% is achievable with your current maturity")
    else:
        st.sidebar.warning(f"""
        ⚠️ Target {target_savings}% requires maturity improvements
        
        Gap: {feasibility['gap']:.1f}% 
        Recommended: Level {feasibility['required_maturity_level']} ({feasibility['required_maturity_name']})
        """)
    
    # Convert to scenario config for the existing model
    scenario_config = {
        'target_percentage': target_savings,
        'current_maturity': current_maturity,
        'feasibility': feasibility,
        'description': f"Target {target_savings}% savings (Current maturity: Level {current_maturity['maturity_level']})"
    }
    
    # Display the approach being used
    st.sidebar.caption(f"Approach: {scenario_config['description']}")
    
    cost_avoidance_selection = st.sidebar.selectbox(
        "Cost Avoidance Model",
        options=list(COST_AVOIDANCE_OPTIONS.keys()),
        index=3,  # Default to "Moderate (2.5x)"
        help="Additional value beyond direct savings"
    )
    
    cost_avoidance_config = COST_AVOIDANCE_OPTIONS[cost_avoidance_selection]
    
    # Project Basics
    st.sidebar.subheader("Project Basics")
    
    total_hours = st.sidebar.number_input(
        "Total Project Hours",
        min_value=1000,
        max_value=100000,
        value=17054,
        step=500,
        help="Total estimated hours for your project across all phases"
    )
    
    blended_rate = st.sidebar.number_input(
        "Blended Hourly Rate ($)",
        min_value=50,
        max_value=300,
        value=100,
        step=5,
        help=(
            "Average hourly cost across all team members "
            "(developers, testers, architects, etc.)"
        )
    )
    
    # Phase Allocation
    st.sidebar.subheader("Phase Time Allocation")
    st.sidebar.markdown("**Adjust based on your project type:**")
    
    phase_allocation = {}
    
    # Show sliders for all phases
    for phase in PHASE_ORDER:
        default_value = DEFAULT_PHASE_ALLOCATION[phase]
        phase_allocation[phase] = st.sidebar.slider(
            f"{phase} %",
            min_value=1,
            max_value=50,
            value=default_value,
            step=1,
            help=f"Percentage of total project time spent in {phase} phase"
        )
    
    # Validation
    total_allocation = sum(phase_allocation.values())
    if abs(total_allocation - 100) > 0.1:
        st.sidebar.error(
            f"Phase allocation must sum to 100% "
            f"(currently {total_allocation}%)"
        )
        st.sidebar.info("Adjust the sliders above so they total exactly 100%")
    
    # Industry Benchmarks
    st.sidebar.subheader("Industry Benchmarks")
    st.sidebar.markdown("""
    **Adjust based on your organization's automation maturity:**
    Sources: Gartner, McKinsey, Perfecto/Testlio, IBM studies
    """)
    
    # Testing Phase Reduction
    st.sidebar.markdown("**Testing Automation Effectiveness**")
    testing_reduction = st.sidebar.slider(
        "Testing Phase Time Reduction",
        min_value=0.1,
        max_value=0.8,
        value=float(INDUSTRY_BENCHMARKS['testing_phase_reduction']),
        step=0.05,
        format="%.0f%%",
        help="""Testing time reduction from automation.
30-50% typical (Perfecto/Testlio studies).
Higher for manual→automated transitions."""
    )
    
    # Manual Testing Reduction  
    manual_testing_reduction = st.sidebar.slider(
        "Manual Testing Reduction",
        min_value=0.1,
        max_value=0.7,
        value=float(INDUSTRY_BENCHMARKS['manual_testing_reduction']),
        step=0.05,
        format="%.0f%%",
        help="""Manual testing effort elimination via automation.
35-45% typical reduction. Higher for manual-heavy organizations."""
    )
    
    # Quality Improvement
    st.sidebar.markdown("**Quality & Defect Reduction**")
    quality_improvement = st.sidebar.slider(
        "Overall Quality Improvement",
        min_value=0.05,
        max_value=0.5,
        value=float(INDUSTRY_BENCHMARKS['quality_improvement']),
        step=0.05,
        format="%.0f%%",
                help="""Quality improvement from shift-left practices.
20% average improvement (McKinsey). Higher for high-defect orgs."""
    )
    
    defect_reduction = st.sidebar.slider(
        "Post-Release Defect Reduction", 
        min_value=0.1,
        max_value=0.6,
        value=float(INDUSTRY_BENCHMARKS['post_release_defect_reduction']),
        step=0.05,
        format="%.0f%%",
                help="""Post-production defect reduction from shift-left.
25% average reduction (IBM). Higher for issue-prone systems."""
    )
    
    # Package industry benchmarks
    custom_benchmarks = {
        'testing_phase_reduction': testing_reduction,
        'manual_testing_reduction': manual_testing_reduction,
        'quality_improvement': quality_improvement,
        'post_release_defect_reduction': defect_reduction,
        'test_automation_cost_reduction': INDUSTRY_BENCHMARKS[
            'test_automation_cost_reduction'
        ],
        'defect_fix_cost_multipliers': INDUSTRY_BENCHMARKS[
            'defect_fix_cost_multipliers'
        ]
    }
    
    # Initiative Maturity Levels  
    st.sidebar.subheader("Initiative Maturity Levels")
    
    # First, set all initiatives to default values for enabled ones
    maturity_levels = {}
    for initiative in INITIATIVE_FALLBACK:
        maturity_levels[initiative] = 50  # Default all to 50% for now
    
    # Risk Assessment
    st.sidebar.subheader("Risk Assessment")
    
    # General risk information
    general_risk_info = RISK_LEVEL_DEFINITIONS["general"]["description"]
    st.sidebar.markdown(f"**Risk Multipliers:** {general_risk_info}")
    
    risk_weights = {}
    for phase in PHASE_ORDER:
        phase_info = get_phase_risk_info(phase)
        help_text = f"""**{phase_info['description']}**

**Typical Risks:**
{chr(10).join([f"• {risk}" for risk in phase_info['typical_risks']])}

**Low Risk Example:** {phase_info['low_risk']}
**High Risk Example:** {phase_info['high_risk']}"""
        
        risk_weights[phase] = st.sidebar.slider(
            f"{phase} Risk",
            min_value=0.5,
            max_value=10.0,
            value=float(DEFAULT_RISK_WEIGHTS[phase]),
            step=0.5,
            format="%.1fx",
            help=help_text,
            key=f"risk_{phase}"
        )
        
        # Real-time risk level description
        risk_level_desc = get_risk_level_description(risk_weights[phase])
        st.sidebar.caption(f"{risk_level_desc}")
    
    # Initiative Selection
    st.sidebar.subheader("Initiative Selection")
    st.sidebar.markdown("**Select available N2S initiatives:**")
    
    initiative_weights = {}
    available_initiatives = []
    
    for initiative in INITIATIVE_FALLBACK:
        col1, col2 = st.sidebar.columns([3, 1])
        
        with col1:
            enabled = st.checkbox(
                initiative,
                value=True,
                key=f"enable_{initiative}",
                help=get_initiative_description(initiative)
            )
        
        with col2:
            if enabled:
                weight = st.number_input(
                    "Weight",
                    min_value=0,
                    max_value=100,
                    value=100,
                    step=5,
                    key=f"weight_{initiative}",
                    help="Relevance to your project (0-100%)"
                )
                initiative_weights[initiative] = weight / 100.0
                available_initiatives.append(initiative)
            else:
                initiative_weights[initiative] = 0.0
    
    # Update maturity levels based on selection
    for initiative in INITIATIVE_FALLBACK:
        if initiative in available_initiatives and initiative_weights[initiative] > 0:
            help_text = get_maturity_description(initiative, 50)
            caption = f"Weight: {initiative_weights[initiative]*100:.0f}% | {help_text}"
            
            maturity_levels[initiative] = st.sidebar.slider(
                f"{initiative} Maturity",
                min_value=0,
                max_value=100,
                value=50,
                step=5,
                help=f"Current implementation maturity for {initiative}",
                key=f"maturity_{initiative}"
            )
            st.sidebar.caption(caption)
        else:
            maturity_levels[initiative] = 0  # Disabled initiatives
    
    return {
        'total_hours': total_hours,
        'blended_rate': blended_rate,
        'phase_allocation': phase_allocation,
        'maturity_levels': maturity_levels,
        'initiative_weights': initiative_weights,
        'available_initiatives': available_initiatives,
        'scenario_config': scenario_config,
        'risk_weights': risk_weights,
        'cost_avoidance_config': cost_avoidance_config,
        'industry_benchmarks': custom_benchmarks,
        'current_maturity': current_maturity,
        'feasibility': feasibility,
        'assessment_responses': assessment_responses
    }


def display_kpi_metrics(kpi_summary):
    """Display key performance indicators"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Hours Saved",
            format_hours(kpi_summary['total_hours_saved']),
            delta=f"{kpi_summary['total_hours_saved_pct']:.1f}%"
        )
    
    with col2:
        st.metric(
            "Cost Savings",
            format_currency(kpi_summary['total_cost_savings']),
            delta="Direct savings"
        )
    
    with col3:
        st.metric(
            "Cost Avoidance",
            format_currency(kpi_summary['total_cost_avoidance']),
            delta="Future savings"
        )
    
    with col4:
        st.metric(
            "Total Financial Benefit",
            format_currency(kpi_summary['total_financial_benefit']),
            delta=format_currency(
                kpi_summary['total_baseline_cost'] - kpi_summary['total_modeled_cost']
            )
        )


def create_cost_breakdown_by_phase_chart(cost_results, summary_df):
    """Create detailed cost breakdown chart showing baseline, savings, and avoidance by phase"""
    fig = make_subplots(
        rows=1, cols=1,
        subplot_titles=('Cost Breakdown by Phase',)
    )
    
    phases = summary_df['Phase']
    baseline_costs = [cost_results['baseline_cost'][phase] for phase in phases]
    direct_savings = [cost_results['savings'][phase] for phase in phases]
    cost_avoidance = [cost_results['avoidance'][phase] for phase in phases]
    modeled_costs = [cost_results['modeled_cost'][phase] for phase in phases]
    
    # Baseline costs (what we would spend without initiatives)
    fig.add_trace(go.Bar(
        x=phases,
        y=baseline_costs,
        name='Baseline Cost',
        marker_color='lightcoral',
        text=[format_currency(c) for c in baseline_costs],
        textposition='outside'
    ))
    
    # Modeled costs (what we actually spend after initiatives)
    fig.add_trace(go.Bar(
        x=phases,
        y=modeled_costs,
        name='Actual Cost (After Initiatives)',
        marker_color='lightblue',
        text=[format_currency(c) for c in modeled_costs],
        textposition='outside'
    ))
    
    # Direct cost savings (negative bars showing savings)
    fig.add_trace(go.Bar(
        x=phases,
        y=[-s for s in direct_savings],  # Show savings as negative
        name='Direct Savings',
        marker_color='green',
        text=[format_currency(-s) if s > 0 else '' for s in direct_savings],
        textposition='outside'
    ))
    
    # Cost avoidance (additional benefits, shown as negative)
    fig.add_trace(go.Bar(
        x=phases,
        y=[-a for a in cost_avoidance],  # Show avoidance as negative
        name='Cost Avoidance',
        marker_color='darkgreen',
        text=[format_currency(-a) if a > 0 else '' for a in cost_avoidance],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Executive Cost Summary: Baseline vs Actual Costs with Benefits",
        xaxis_title="Project Phase",
        yaxis_title="Cost ($)",
        barmode='group',
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        annotations=[
            dict(
                x=0.5, xref='paper',
                y=1.15, yref='paper',
                text="Green bars show financial benefits (savings = immediate, avoidance = future)",
                showarrow=False,
                font=dict(size=12, color='gray')
            )
        ]
    )
    
    # Add zero line for reference
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    
    return fig


def create_phase_comparison_chart(summary_df):
    """Create side-by-side bar chart comparing baseline vs modeled hours"""
    fig = go.Figure()
    
    # Add baseline hours
    fig.add_trace(go.Bar(
        x=summary_df['Phase'],
        y=summary_df['Baseline Hours'],
        name='Baseline Hours',
        marker_color='lightblue',
        text=[format_hours(h) for h in summary_df['Baseline Hours']],
        textposition='outside',
        offsetgroup=1
    ))
    
    # Add modeled hours
    fig.add_trace(go.Bar(
        x=summary_df['Phase'],
        y=summary_df['Modeled Hours'],
        name='Modeled Hours',
        marker_color='darkblue',
        text=[format_hours(h) for h in summary_df['Modeled Hours']],
        textposition='outside',
        offsetgroup=2
    ))
    
    fig.update_layout(
        title="Baseline vs Modeled Hours by Phase",
        xaxis_title="Phase",
        yaxis_title="Hours",
        barmode='group',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_hours_saved_chart(summary_df):
    """Create chart showing hours saved/added by phase"""
    fig = go.Figure()
    
    # Calculate hours saved (negative = savings, positive = additional hours)
    hours_variance = summary_df['Hour Variance']
    colors = ['green' if x < 0 else 'red' if x > 0 else 'gray' for x in hours_variance]
    
    fig.add_trace(go.Bar(
        x=summary_df['Phase'],
        y=hours_variance,
        name='Hours Saved',
        marker_color=colors,
        text=[f"{h:+,.0f}" for h in hours_variance],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Hours Saved by Phase (Negative = Savings)",
        xaxis_title="Phase",
        yaxis_title="Hour Variance",
        height=400,
        showlegend=False
    )
    
    # Add zero line for reference
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    
    return fig


def create_cost_breakdown_chart(cost_results):
    """Create pie chart showing cost savings vs avoidance"""
    total_savings = sum(cost_results['savings'].values())
    total_avoidance = sum(cost_results['avoidance'].values())
    
    if total_savings + total_avoidance == 0:
        st.warning("No cost benefits calculated")
        return None
    
    fig = go.Figure(data=[go.Pie(
        labels=['Direct Cost Savings', 'Cost Avoidance'],
        values=[total_savings, total_avoidance],
        hole=0.3,
        marker_colors=['#2E8B57', '#4682B4']
    )])
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont_size=12
    )
    
    fig.update_layout(
        title="Financial Benefits Breakdown",
        annotations=[dict(text=f'Total<br>{format_currency(total_savings + total_avoidance)}', 
                         x=0.5, y=0.5, font_size=16, showarrow=False)]
    )
    
    return fig


def create_variance_chart(summary_df):
    """Create variance analysis chart"""
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Hour Variance by Phase', 'Cost Variance by Phase'),
        vertical_spacing=0.1
    )
    
    colors = get_phase_colors()
    
    # Hour variance
    fig.add_trace(
        go.Bar(
            x=summary_df['Phase'],
            y=summary_df['Hour Variance'],
            name='Hour Variance',
            marker_color=[colors[phase] for phase in summary_df['Phase']],
            text=[f"{h:,.0f}" for h in summary_df['Hour Variance']],
            textposition='outside'
        ),
        row=1, col=1
    )
    
    # Cost variance
    fig.add_trace(
        go.Bar(
            x=summary_df['Phase'],
            y=summary_df['Cost Variance'],
            name='Cost Variance',
            marker_color=[colors[phase] for phase in summary_df['Phase']],
            text=[format_currency(c) for c in summary_df['Cost Variance']],
            textposition='outside'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title="Variance Analysis (Negative = Savings)",
        showlegend=False,
        height=600
    )
    
    fig.update_xaxes(title_text="Phase", row=2, col=1)
    fig.update_yaxes(title_text="Hour Variance", row=1, col=1)
    fig.update_yaxes(title_text="Cost Variance ($)", row=2, col=1)
    
    return fig


def create_initiative_impact_chart(initiative_df):
    """Create chart showing financial impact by initiative"""
    # Filter to show only initiatives with meaningful impact
    significant_df = initiative_df[
        abs(initiative_df['Total Financial Impact']) > 1000
    ].head(10)  # Top 10 initiatives
    
    if len(significant_df) == 0:
        return None
    
    # Reverse the order so best initiatives (most negative/savings) appear at top
    significant_df = significant_df.iloc[::-1]
    
    fig = go.Figure()
    
    # Color code by impact (green for savings, red for costs)
    colors = ['#28a745' if x < 0 else '#dc3545' 
              for x in significant_df['Total Financial Impact']]
    
    fig.add_trace(go.Bar(
        x=significant_df['Total Financial Impact'],
        y=significant_df['Initiative'],
        orientation='h',
        marker_color=colors,
        text=[format_currency(abs(x)) for x in significant_df['Total Financial Impact']],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Initiative Financial Impact (Top Contributors)",
        xaxis_title="Financial Impact ($)",
        yaxis_title="",
        height=max(400, len(significant_df) * 40),
        showlegend=False
    )
    
    return fig


def export_to_excel(summary_df, kpi_summary, cost_results, initiative_impact_df=None):
    """Export results to Excel file"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Summary table
        summary_df.to_excel(writer, sheet_name='Phase Summary', index=False)
        
        # Initiative impacts
        if initiative_impact_df is not None:
            initiative_impact_df.to_excel(writer, sheet_name='Initiative Impacts', index=False)
        
        # KPI summary
        kpi_df = pd.DataFrame([kpi_summary]).T
        kpi_df.columns = ['Value']
        kpi_df.to_excel(writer, sheet_name='KPIs')
        
        # Cost breakdown
        cost_breakdown = []
        for phase in PHASE_ORDER:
            cost_breakdown.append({
                'Phase': phase,
                'Baseline Cost': cost_results['baseline_cost'][phase],
                'Modeled Cost': cost_results['modeled_cost'][phase],
                'Cost Savings': cost_results['savings'][phase],
                'Cost Avoidance': cost_results['avoidance'][phase]
            })
        
        cost_df = pd.DataFrame(cost_breakdown)
        cost_df.to_excel(writer, sheet_name='Cost Details', index=False)
    
    return output.getvalue()


def main():
    """Main application function"""
    load_custom_css()
    
    # Title and version
    from config import APP_VERSION
    st.title("N2S Impact Modeling Tool")
    st.markdown(f"*{APP_VERSION}*")
    
    # Getting Started Guide for Novices
    with st.expander("Getting Started Guide - How This Model Works", expanded=False):
        st.markdown("""
        ## Understanding the N2S Impact Model
        
        This tool helps you estimate the time and cost savings from implementing Next to Source (N2S) efficiency initiatives across your development projects.
        
        ### The Big Picture: How It Works
        
        **1. Initiatives Work Across All Development Phases**
        Your project has 7 phases: Discover → Plan → Design → Build → Test → Deploy → Post Go-Live
        
        Each N2S initiative (like "Automated Testing" or "AI/Automation") can save hours in multiple phases:
        - **Automated Testing** saves the most in Test phase, but also helps in Build and Deploy
        - **Modernization Studio** primarily helps Build and Design phases
        - **Integration Code Reuse** saves time in Build, Test, and Deploy phases
        
        The model calculates how much time each initiative saves in each phase, then adds them up.
        
        ### Key Concepts You Need to Understand
        
        #### **Cost Savings vs Cost Avoidance**
        - **Cost Savings** = Direct money saved during development (fewer hours = lower cost)
        - **Cost Avoidance** = Future costs you avoid after go-live (fewer bugs, faster fixes, less maintenance)
        
        **Think of it this way:**
        - Cost Savings: "We finished the project $50k under budget"
        - Cost Avoidance: "Because we built it better, we're saving $20k/month in support costs"
        
        #### **How to Set Cost Avoidance:**
        - **Conservative (1.5x)**: Very risk-averse, minimal long-term benefits
        - **Moderate (2.5x)**: Industry average for shift-left practices
        - **Aggressive (4-6x)**: High-maturity organizations with strong DevOps practices
        
        ### Step-by-Step: How to Use This Model
        
        #### **Step 1: Set Your Project Context (Do This First)**
        1. **Total Project Hours**: How big is your project? (5k = small, 20k = medium, 50k = large)
        2. **Phase Allocation**: What type of project?
           - **Greenfield/New**: More Design (20%) and Build (30%)
           - **Maintenance**: More Test (25%) and Deploy (15%)
           - **Migration**: More Discover (10%) and Plan (15%)
        3. **Cost Avoidance Model**: Start with "Moderate (2.5x)" - adjust later based on your organization's maturity
        
        #### **Step 2: Choose Your Initiatives (Core Decision)**
        - **Enable only initiatives your organization actually has access to**
        - **Weight them by relevance** (100% = fully applicable, 50% = partially applicable)
        - Common starting point: Enable all at 100% weight, then adjust down
        
        #### **Step 3: Set Industry Benchmarks (Important!)**
        These reflect your organization's **current state automation maturity**:
        
        **If you're a legacy organization (lots of manual processes):**
        - Testing Phase Reduction: 50-70% (high savings potential)
        - Manual Testing Reduction: 60-70% (lots of manual work to automate)
        - Quality Improvement: 30-40% (big gains from better practices)
        
        **If you're already modern/automated:**
        - Testing Phase Reduction: 20-35% (already automated, smaller gains)
        - Manual Testing Reduction: 15-30% (less manual work to eliminate)
        - Quality Improvement: 10-20% (incremental improvements only)
        
        #### **Step 4: Fine-Tune the Details (Do This Last)**
        1. **Initiative Maturity Levels**: Start with 50% for all, then adjust based on your organization's adoption
        2. **Blended Hourly Rate**: Adjust for your location and team composition
        3. **Risk Weights**: Start with defaults, increase for high-risk/complex phases
        
        ### What the Results Tell You
        
        - **Hours Saved**: Direct time reduction in your project
        - **Cost Savings**: Money saved during development 
        - **Cost Avoidance**: Future operational savings
        - **Total Financial Benefit**: Combined impact over time
        
        ### Pro Tips for Realistic Results
        
        1. **Start Conservative**: It's better to under-promise and over-deliver
        2. **Focus on 2-3 Key Initiatives**: Don't try to implement everything at once
        3. **Adjust Industry Benchmarks First**: This has the biggest impact on results
        4. **Validate with Pilots**: Run small pilots to validate your assumptions before scaling
        
        ---
        **Ready to start? Work through Steps 1-4 above, then review your results!**
        """)
    
    # Understanding Your Baseline - NEW SECTION
    with st.expander("Understanding Your Baseline Efficiency", expanded=False):
        st.markdown("""
        ## What Does "Baseline" Mean in This Model?
        
        **Your baseline represents your organization's CURRENT development efficiency** - how you build software TODAY without any N2S initiatives.
        
        ### Baseline Assumptions (Industry Averages)
        
        The model assumes your current baseline includes:
        
        #### **Current Automation Level: ~20-30%**
        - **Some basic unit testing** (but not comprehensive)
        - **Manual regression testing** for most critical paths
        - **Basic CI/CD pipelines** (but not fully automated)
        - **Standard development tools** (IDEs, version control)
        - **Traditional project management** approaches
        
        #### **Current Quality Practices:**
        - **Bug detection primarily in testing phases** (not shift-left)
        - **Manual code reviews** without extensive automation
        - **Standard defect rates** (industry average: 1-5 defects per 1000 lines of code)
        - **Traditional environment setup** (some manual configuration)
        
        #### **Current Integration Patterns:**
        - **Custom integrations** built from scratch for most projects
        - **Limited code reuse** between projects
        - **Manual deployment processes** for production releases
        
        ### How N2S Initiatives Improve Upon Baseline
        
        **The efficiency gains calculated represent improvements ABOVE your current baseline:**
        
        #### **Example: Automated Testing Initiative**
        - **Your Baseline**: 70% manual testing, 30% automated
        - **At 50% N2S Maturity**: 45% manual testing, 55% automated  
        - **At 100% N2S Maturity**: 15% manual testing, 85% automated
        - **Hours Saved**: Reduction in manual testing effort + faster feedback loops
        
        #### **Example: Integration Code Reuse**
        - **Your Baseline**: Build each integration from scratch
        - **At 50% N2S Maturity**: Reuse 40-50% of integration components
        - **At 100% N2S Maturity**: Reuse 80-90% via standardized API library
        - **Hours Saved**: Reduction in custom development time
        
        ### Calibrating to YOUR Baseline
        
        **If your organization is MORE advanced than industry average:**
        - Set **Industry Benchmarks lower** (20-30% improvements)
        - Your actual savings will be **smaller** than shown
        - Focus on **incremental optimization** rather than transformation
        
        **If your organization is LESS advanced than industry average:**
        - Set **Industry Benchmarks higher** (50-70% improvements)  
        - Your actual savings will be **larger** than shown
        - You have **significant transformation opportunity**
        
        ### Key Principle: Conservative by Design
        
        **This model errs on the side of conservative estimates:**
        - Baseline assumes you're **already doing some automation**
        - Efficiency gains are **incremental improvements**, not wholesale transformation
        - Results should be **achievable and defensible** to stakeholders
        
                 **Bottom Line:** The baseline represents a "typical" software development organization with moderate automation maturity. Adjust the Industry Benchmarks to reflect YOUR organization's current state relative to this baseline.
        """)
    
    # Load model
    model = initialize_model()
    
    # Create sidebar controls (includes maturity assessment)
    controls = create_sidebar_controls()
    if controls is None:
        st.error("Please fix the phase allocation percentages in the sidebar.")
        return
    
    # Display Maturity Assessment Results
    st.header("Maturity Assessment Results")
    
    current_maturity = controls['current_maturity']
    feasibility = controls['feasibility']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Current Maturity Level",
            f"Level {current_maturity['maturity_level']}",
            delta=current_maturity['maturity_name']
        )
    
    with col2:
        st.metric(
            "Current Savings Potential", 
            f"{current_maturity['current_savings_potential']:.1f}%",
            delta=f"{current_maturity['savings_range'][0]}-{current_maturity['savings_range'][1]}% range"
        )
    
    with col3:
        target_savings = controls['scenario_config']['target_percentage']
        if feasibility['feasible']:
            st.metric("Target Feasibility", "✓ Achievable", delta="With current maturity")
        else:
            st.metric("Target Feasibility", "⚠ Requires Improvement", delta=f"{feasibility['gap']:.1f}% gap")
    
    # Maturity Details and Recommendations
    with st.expander("Maturity Analysis & Recommendations", expanded=False):
        st.markdown(f"""
        ### Current State: {current_maturity['maturity_name']}
        
        **Description:** {current_maturity['maturity_description']}
        
        ### Current Automation Characteristics:
        """)
        
        for area, description in current_maturity['automation_characteristics'].items():
            st.markdown(f"- **{area.replace('_', ' ').title()}**: {description}")
        
        if not feasibility['feasible']:
            st.markdown(f"""
            ### Recommendations to Reach {target_savings}% Target:
            
            **Required Maturity Level:** {feasibility['required_maturity_name']} (Level {feasibility['required_maturity_level']})
            """)
            
            for i, recommendation in enumerate(feasibility['recommendations'], 1):
                st.markdown(f"{i}. {recommendation}")
        
        else:
            st.success("Your current maturity level supports your target savings goal!")
    
    # Run calculations with existing model
    try:
        # Apply maturity and scenario with dynamic scaling
        effective_deltas = model.apply_maturity_and_scenario(
            controls['maturity_levels'],
            controls['scenario_config'],  # Pass the config dict instead of string
            controls['industry_benchmarks']
        )
        
        baseline_hours, modeled_hours = model.calculate_phase_hours(
            controls['total_hours'], 
            controls['phase_allocation'], 
            effective_deltas
        )
        
        # Get cost avoidance configuration
        cost_avoidance_config = controls['cost_avoidance_config']
        
        cost_results = model.calculate_costs_and_savings(
            baseline_hours, 
            modeled_hours, 
            controls['blended_rate'],
            True, # Always include cost avoidance for now
            cost_avoidance_config
        )
        
        risk_adjusted_hours = model.calculate_risk_adjusted_hours(
            modeled_hours, 
            controls['risk_weights']
        )
        
        summary_df = model.generate_summary_table(
            baseline_hours, 
            modeled_hours,
            cost_results['baseline_cost'], 
            cost_results['modeled_cost'],
            risk_adjusted_hours
        )
        
        kpi_summary = model.get_kpi_summary(
            baseline_hours, 
            modeled_hours, 
            cost_results
        )
        
        # Generate initiative impact analysis
        initiative_impact_df = model.generate_initiative_impact_table(
            effective_deltas,
            controls['maturity_levels'],
            controls['blended_rate'],
            True, # Always include cost avoidance for now
            cost_avoidance_config
        )
        
        # Validate results
        is_valid, warning = validate_scenario_results(
            kpi_summary['total_baseline_cost'],
            kpi_summary['total_modeled_cost']
        )
        
        if not is_valid:
            st.warning(warning)
        
        # Display results
        st.header("Results Dashboard")
        
        # KPI Metrics
        st.subheader("Key Performance Indicators")
        display_kpi_metrics(kpi_summary)
        
        # Initiative Impact Analysis
        st.subheader("Initiative Impact Analysis")
        st.markdown("See how each initiative contributes to overall savings:")
        
        # Show initiative impact table
        st.dataframe(
            initiative_impact_df.style.format({
                'Maturity %': '{:.0f}%',
                'Baseline Hour Delta': '{:,.0f}',
                'Effective Hour Delta': '{:,.0f}',
                'Development Hours': '{:,.0f}',
                'Post Go-Live Hours': '{:,.0f}',
                'Development Cost Impact': '${:,.0f}',
                'Post Go-Live Cost Impact': '${:,.0f}',
                'Total Financial Impact': '${:,.0f}'
            }),
            use_container_width=True,
            height=400
        )
        
        # Summary table
        st.subheader("Phase-by-Phase Summary")
        st.dataframe(
            summary_df.style.format({
                'Baseline Hours': '{:,.0f}',
                'Modeled Hours': '{:,.0f}',
                'Hour Variance': '{:,.0f}',
                'Hour Variance %': '{:.1f}%',
                'Baseline Cost': '${:,.0f}',
                'Modeled Cost': '${:,.0f}',
                'Cost Variance': '${:,.0f}',
                'Cost Variance %': '{:.1f}%',
                'Risk-Adjusted Hours': '{:,.0f}'
            }),
            use_container_width=True
        )
        
        # Charts
        st.subheader("Executive Cost Analysis")
        
        # New comprehensive cost breakdown chart
        cost_breakdown_chart = create_cost_breakdown_by_phase_chart(cost_results, summary_df)
        st.plotly_chart(cost_breakdown_chart, use_container_width=True)
        
        st.markdown("""
        **Key for Executives:**
        - **Baseline Cost**: What we'd spend without any efficiency initiatives
        - **Actual Cost**: What we actually spend after implementing initiatives  
        - **Direct Savings**: Immediate cost reductions during development
        - **Cost Avoidance**: Future operational savings from better quality/processes
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Phase Hours Comparison")
            phase_chart = create_phase_comparison_chart(summary_df)
            st.plotly_chart(phase_chart, use_container_width=True)
        
        with col2:
            st.subheader("Hours Saved by Phase")
            hours_saved_chart = create_hours_saved_chart(summary_df)
            st.plotly_chart(hours_saved_chart, use_container_width=True)
        
        # Financial Benefits Chart
        st.subheader("Financial Benefits Summary")
        cost_chart = create_cost_breakdown_chart(cost_results)
        if cost_chart:
            st.plotly_chart(cost_chart, use_container_width=True)
        
        # Initiative Impact Chart
        st.subheader("Top Initiative Contributors")
        initiative_chart = create_initiative_impact_chart(initiative_impact_df)
        if initiative_chart:
            st.plotly_chart(initiative_chart, use_container_width=True)
        else:
            st.info("No significant initiative impacts to display (adjust maturity levels to see impacts)")
        
        # Variance analysis
        st.subheader("Detailed Variance Analysis")
        variance_chart = create_variance_chart(summary_df)
        st.plotly_chart(variance_chart, use_container_width=True)
        
        # Export functionality
        st.header("Export Results")
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV export
            csv_data = summary_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"n2s_efficiency_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
        
        with col2:
            # Excel export
            excel_data = export_to_excel(summary_df, kpi_summary, cost_results, initiative_impact_df)
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name=f"n2s_efficiency_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        # Model details
        with st.expander("Model Details & Assumptions"):
            st.markdown("""
            **Dynamic Scaling Approach:**
            - **5-12%**: Conservative automation, proven low-risk approaches
            - **13-22%**: Moderate automation with enhanced testing and quality  
            - **23%+**: Aggressive transformation with comprehensive safety caps
            
            **Scenario Definitions:**
            - **Target: ~10% Savings**: Light automation improvements, proven approaches
            - **Target: ~20% Savings**: Moderate automation with enhanced testing  
            - **Target: ~30% Savings**: Aggressive automation transformation
            
            **Key Assumptions:**
            - Direct savings apply to development phases (Discover-Deploy)
            - Cost avoidance applies to Post Go-Live phase
            - Risk weights multiply modeled hours for risk assessment
            - Maximum total cost reduction capped at 30%
            """)
        
        # Initiative Maturity Guide
        with st.expander("Initiative Maturity Level Guide"):
            from config import (
                INITIATIVE_FALLBACK, INITIATIVE_MATURITY_DEFINITIONS,
                get_initiative_description, get_maturity_description
            )
            
            st.markdown("### Initiative Definitions and Maturity Levels")
            
            for initiative in INITIATIVE_FALLBACK:
                st.markdown(f"#### {initiative}")
                desc = get_initiative_description(initiative)
                st.markdown(f"**Description:** {desc}")
                
                st.markdown("**Maturity Levels:**")
                if initiative in INITIATIVE_MATURITY_DEFINITIONS:
                    definitions = INITIATIVE_MATURITY_DEFINITIONS[initiative]
                    for level, definition in definitions.items():
                        if level != "description":  # Skip the main description
                            st.markdown(f"- **{level}:** {definition}")
                else:
                    st.markdown("- **0%:** Not implemented")
                    st.markdown("- **25%:** Initial adoption")  
                    st.markdown("- **50%:** Regular use")
                    st.markdown("- **75%:** Advanced implementation")
                    st.markdown("- **100%:** Fully mature and optimized")
                
                st.markdown("---")
        
        # Risk Assessment Guide
        with st.expander("Risk Assessment Guide"):
            from config import (
                PHASE_ORDER, RISK_LEVEL_DEFINITIONS,
                get_phase_risk_info, get_risk_level_description
            )
            
            st.markdown("### Risk Level Guidelines")
            
            # General risk information
            general_info = RISK_LEVEL_DEFINITIONS["general"]
            st.markdown(f"**Overview:** {general_info['description']}")
            
            st.markdown("### Risk Level Definitions")
            for level, desc in general_info.items():
                if level != "description":  # Skip the general description
                    st.markdown(f"- **{level}x:** {desc}")
            
            st.markdown("### Phase-Specific Risk Factors")
            
            for phase in PHASE_ORDER:
                phase_info = get_phase_risk_info(phase)
                st.markdown(f"#### {phase}")
                st.markdown(f"**Description:** {phase_info['description']}")
                
                st.markdown("**Typical Risk Factors:**")
                for risk in phase_info['typical_risks']:
                    st.markdown(f"- {risk}")
                
                st.markdown(f"**Low Risk Example:** {phase_info['low_risk']}")
                st.markdown(f"**High Risk Example:** {phase_info['high_risk']}")
                st.markdown("---")
    
    except Exception as e:
        st.error(f"Error running calculations: {e}")
        st.exception(e)

if __name__ == "__main__":
    main() 