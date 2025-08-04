# Navigate-to-SaaS (N2S) Efficiency Modeling Application

An interactive Streamlit application that quantifies professional services efficiency gains and cost impacts when Ellucian adopts its Navigate-to-SaaS (N2S) "shift-left" delivery methodology.

## Overview

This application models the efficiency improvements and cost benefits of implementing shift-left practices across the software development lifecycle. It uses industry benchmarks and configurable initiative maturity levels to calculate realistic efficiency gains.

## Features

- **Interactive Configuration**: Sidebar controls for all model parameters
- **Multiple Scenarios**: Conservative (10%), Elevated (20%), and Aggressive (30%) improvement scenarios
- **Industry-Grounded**: Based on research from Gartner, Forrester, McKinsey, and empirical case studies
- **Comprehensive Analytics**: Hour savings, cost reductions, risk assessments, and cost avoidance calculations
- **Rich Visualizations**: Interactive charts showing phase comparisons, variance analysis, and financial breakdowns
- **Export Capabilities**: Download results as CSV or Excel with full detail breakdown
- **Validation**: Built-in checks against realistic industry improvement bounds

## Architecture

```
n2s_efficiency_app/
├── app.py               # Streamlit main application
├── model.py             # Core calculation engine
├── config.py            # Configuration constants and helpers
├── requirements.txt     # Python dependencies
├── data/               # Data directory
│   └── ShiftLeft_Levers_PhaseMatrix_v3.xlsx  # Input matrix (place here)
├── README.md           # This file
└── Assumptions.md      # Industry benchmark sources and assumptions
```

### Core Components

1. **`app.py`** - Streamlit user interface with:
   - Sidebar configuration controls
   - Interactive visualizations (Plotly)
   - Results dashboard and KPI metrics
   - Export functionality

2. **`model.py`** - Business logic containing:
   - `N2SEfficiencyModel` class for all calculations
   - Matrix loading and phase mapping
   - Scenario application with industry benchmarks
   - Cost/savings calculations with validation

3. **`config.py`** - Configuration management:
   - Default values and constants
   - Industry benchmark data
   - Helper functions for formatting and validation
   - Scenario definitions with layered benefits

## Getting Started

### Prerequisites

- Python 3.8+ 
- pip package manager

### Installation

1. **Clone or download** the application files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Place your data file** (optional):
   - Put `ShiftLeft_Levers_PhaseMatrix_v3.xlsx` in the `data/` folder
   - If not provided, the app will use built-in sample data

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## Using the Application

### Sidebar Configuration

1. **Project Parameters**:
   - Total project hours (default: 17,054)
   - Blended labor rate (default: $100/hour)

2. **Phase Allocation**:
   - Adjust percentage allocation across 7 N2S phases
   - Must sum to 100%

3. **Initiative Maturity Levels**:
   - Set maturity (0-100%) for each improvement initiative
   - Higher maturity = greater benefit realization

4. **Scenario Selection**:
   - **Moderate (10%)**: Conservative baseline improvements
   - **Elevated (20%)**: Enhanced benefits from automation
   - **Aggressive (30%)**: Near-maximum credible improvements

5. **Risk Weights**:
   - Multipliers for risk assessment by phase
   - Higher weights = riskier phases

6. **Financial Options**:
   - Toggle inclusion of post-go-live cost avoidance

### Interpreting Results

- **KPI Metrics**: High-level hours saved, costs, and financial benefits
- **Summary Table**: Detailed phase-by-phase comparison
- **Charts**: 
  - Phase hours comparison (baseline vs. modeled)
  - Financial benefits breakdown (savings vs. avoidance)
  - Variance analysis showing improvements by phase

## Extending the Application

### Adding New Initiatives

1. Update the Excel matrix with new initiative rows
2. The application will automatically load new initiatives
3. Initiative names become slider labels in the sidebar

### Modifying Phase Structure

1. Update `PHASE_ORDER` in `config.py`
2. Ensure Excel matrix columns match or use column mapping
3. Update any phase-specific logic in `model.py`

### Adding New Scenarios

1. Add scenario definition to `SCENARIOS` in `config.py`
2. Implement scenario logic in `apply_maturity_and_scenario()` method
3. Update UI scenario selector

### Custom Industry Benchmarks

1. Modify `INDUSTRY_BENCHMARKS` in `config.py`
2. Update scenario calculations in `model.py` to use new benchmarks
3. Document changes in `Assumptions.md`

## Data Requirements

### Input Matrix Format

The Excel file should contain:
- **Sheet Name**: "10pct_Savings" (configurable)
- **Rows**: Initiative names (e.g., "Test Automation Framework")
- **Columns**: Phase names (will be mapped to N2S phases)
- **Values**: Hour deltas (positive = adds effort, negative = saves effort)

### Phase Mapping

The application automatically maps common column names:
- "discovery" → "Discover"
- "planning"/"plan" → "Plan"
- "design" → "Design"
- "development"/"build" → "Build"
- "testing"/"test" → "Test"
- "deployment"/"deploy" → "Deploy"
- "post-go-live"/"support"/"maintenance" → "Post Go-Live"

## Testing

The application includes sample data for testing and demonstration. Key test scenarios:

1. **Baseline Test**: All initiatives at 0% maturity should show no improvements
2. **Full Maturity**: All initiatives at 100% should show maximum configured benefits
3. **Scenario Validation**: Aggressive scenario should show higher benefits than Moderate
4. **Bounds Checking**: Ensure no scenario exceeds 30% total cost reduction

### Running Test Scenarios

```python
from model import run_model_scenario

# Test with different configurations
summary, kpis = run_model_scenario(
    total_hours=17054,
    scenario='Aggressive (30%)',
    maturity_levels={'Test Automation Framework': 100}
)
```

## Future Enhancements

Planned improvements (see TODOs in code):

1. **Role-Based Costing**: Different hourly rates by role/phase
2. **Time-to-Market Calculations**: Revenue impact of faster delivery
3. **Confidence Intervals**: Statistical bounds on improvement estimates
4. **Monte Carlo Simulation**: Risk-adjusted scenario modeling
5. **Historical Tracking**: Compare actual vs. predicted outcomes
6. **Advanced Visualizations**: Gantt charts, sensitivity analysis

## Troubleshooting

### Common Issues

1. **Phase allocation error**: Ensure percentages sum to exactly 100%
2. **File not found**: Place Excel file in `data/` folder or use sample data
3. **Import errors**: Verify all dependencies installed with `pip install -r requirements.txt`
4. **Performance**: Large Excel files may take time to load - consider data optimization

### Getting Help

1. Check the **Model Details & Assumptions** expandable section in the app
2. Review error messages in the Streamlit interface
3. Validate input data format against specifications above

## License

This application is provided for internal use at Ellucian. See organization policies for usage guidelines.

## Contributing

For questions, improvements, or bug reports:
1. Document the issue with steps to reproduce
2. Include relevant configuration and data details
3. Suggest improvements with business justification

---

*Built using Streamlit, Pandas, and Plotly* 