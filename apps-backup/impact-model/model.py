"""
Core calculation engine for N2S Efficiency Modeling Application
Handles data loading, scenario application, and cost calculations
"""

import pandas as pd
from typing import Dict, Tuple, Optional, List

from config import (
    PHASE_ORDER, DEFAULT_PHASE_ALLOCATION, DEFAULT_RISK_WEIGHTS,
    INDUSTRY_BENCHMARKS, calculate_baseline_hours, INITIATIVE_FALLBACK
)


def get_initiatives() -> List[str]:
    """Return list of initiative names."""
    return INITIATIVE_FALLBACK.copy()


class N2SEfficiencyModel:
    """Core model for calculating N2S efficiency improvements"""
    
    def __init__(self):
        """Initialize the model"""
        self.matrix_data = None
        self.initiatives = []
        self.loaded = False
        
    def create_sample_data(self):
        """Create and use sample matrix data"""
        self._create_sample_matrix()
        return True
    
    def _create_sample_matrix(self):
        """Create sample efficiency matrix with research-based data"""
        # Calibrated for: 50% maturity baseline = ~8% savings, 100% = ~16%
        sample_data = {
            # Early phases: Moderate savings from better planning/reuse
            'Discover': [-13, -10, -19, -26, -6, -16, -22],
            'Plan': [-19, -16, -32, -38, -10, -26, -29],
            'Design': [-32, -26, -45, -51, -38, -35, -42],

            # Development: Major savings from automation, reuse, tools
            'Build': [-51, -77, -64, -96, -128, -58, -115],

            # Testing: Biggest savings potential from automation
            'Test': [-128, -115, -102, -77, -160, -64, -179],

            # Deployment: Significant savings from automation/environments
            'Deploy': [-26, -51, -19, -38, -32, -22, -29],

            # Post Go-Live: Ongoing operational improvements
            'Post Go-Live': [-96, -64, -77, -115, -51, -58, -90]
        }
        
        self.matrix_data = pd.DataFrame(sample_data, index=INITIATIVE_FALLBACK)
        self.initiatives = INITIATIVE_FALLBACK.copy()
        self.loaded = True

    def apply_maturity_and_scenario(
        self,
        maturity_levels: Dict[str, float],
        scenario_config: Dict,
        industry_benchmarks: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Apply maturity levels and scenario config to get effective hour deltas.
        
        Args:
            maturity_levels: Dict mapping initiative names to maturity % (0-100)
            scenario_config: Dict with target percentage and maturity info
            industry_benchmarks: Optional custom industry benchmark values
            
        Returns:
            DataFrame with effective hour deltas after maturity and scenario
        """
        if not self.loaded:
            raise ValueError("Matrix data not loaded. Call create_sample_data() first.")
        
        # Use provided benchmarks or fall back to defaults
        if industry_benchmarks is None:
            industry_benchmarks = INDUSTRY_BENCHMARKS
            
        # Apply maturity levels (convert percentages to decimal multipliers)
        effective_matrix = self.matrix_data.copy().astype(float)
        for initiative in effective_matrix.index:
            if initiative in maturity_levels:
                maturity_multiplier = maturity_levels[initiative] / 100.0
                effective_matrix.loc[initiative] = (
                    effective_matrix.loc[initiative] * maturity_multiplier
                )
        
        # Apply scaling based on target savings and organizational maturity
        target_percentage = scenario_config.get('target_percentage', 15)
        current_maturity = scenario_config.get('current_maturity', {})
        current_level = current_maturity.get('maturity_level', 2)
        
        # Calculate scaling factors based on target and current maturity
        base_intensity = target_percentage / 15.0  # 15% = 1.0x baseline
        
        # Maturity-based adjustment
        maturity_factor = current_level / 3.0  # Level 3 = 1.0x, higher levels get bonus
        
        # Progressive scaling
        if target_percentage <= 10:
            additional_factor = 0.0
            testing_boost = base_intensity * 0.2 * maturity_factor
            quality_boost = base_intensity * 0.15 * maturity_factor
            
        elif target_percentage <= 20:
            progress = (target_percentage - 10) / 10.0
            additional_factor = progress * 0.8 * maturity_factor
            testing_boost = base_intensity * (0.3 + progress * 0.2) * maturity_factor
            quality_boost = base_intensity * (0.2 + progress * 0.15) * maturity_factor
            
        else:
            progress = min(1.0, (target_percentage - 20) / 10.0)
            additional_factor = (0.8 + progress * 0.7) * maturity_factor
            testing_boost = base_intensity * (0.5 + progress * 0.3) * maturity_factor
            quality_boost = base_intensity * (0.35 + progress * 0.25) * maturity_factor
        
        # Apply enhancements if factors are significant
        if additional_factor > 0 or testing_boost > 0:
            # Enhanced test automation 
            if testing_boost > 0:
                base_test_boost = industry_benchmarks['testing_phase_reduction']
                effective_matrix['Test'] *= (1 + base_test_boost * testing_boost)
            
            # Quality improvements across development phases
            if quality_boost > 0:
                base_quality_boost = industry_benchmarks['quality_improvement']
                quality_phases = ['Design', 'Build', 'Test']
                if additional_factor > 0.5:
                    quality_phases.append('Deploy')
                    
                for phase in quality_phases:
                    if phase in effective_matrix.columns:
                        effective_matrix[phase] *= (1 + base_quality_boost * quality_boost)
        
        # Apply conservative caps for high targets with low maturity
        if target_percentage > 20 and current_level < 4:
            # More conservative caps for organizations not ready for aggressive targets
            conservative_caps = {
                'Discover': 0.35, 'Plan': 0.40, 'Design': 0.45,
                'Build': 0.50, 'Test': 0.60, 'Deploy': 0.45, 'Post Go-Live': 0.65
            }
            
            baseline_hours = calculate_baseline_hours(17054, DEFAULT_PHASE_ALLOCATION)
            
            for phase in effective_matrix.columns:
                if phase in conservative_caps:
                    max_savings = baseline_hours[phase] * conservative_caps[phase]
                    total_savings = abs(effective_matrix[phase].sum())
                    if total_savings > max_savings:
                        scale_factor = max_savings / total_savings
                        effective_matrix[phase] *= scale_factor
        
        return effective_matrix

    def calculate_phase_hours(
        self, 
        total_hours: float, 
        phase_allocation: Dict[str, float], 
        effective_deltas: pd.DataFrame
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Calculate baseline and modeled hours for each phase"""
        baseline_hours = calculate_baseline_hours(total_hours, phase_allocation)
        
        # Calculate modeled hours by applying deltas
        modeled_hours = {}
        for phase in PHASE_ORDER:
            if phase in effective_deltas.columns:
                total_delta = effective_deltas[phase].sum()
                modeled_hours[phase] = max(0, baseline_hours[phase] + total_delta)
            else:
                modeled_hours[phase] = baseline_hours[phase]
                
        return baseline_hours, modeled_hours

    def calculate_costs_and_savings(
        self,
        baseline_hours: Dict[str, float],
        modeled_hours: Dict[str, float],
        blended_rate: float,
        include_cost_avoidance: bool = True,
        cost_avoidance_config: Optional[Dict] = None
    ) -> Dict[str, Dict[str, float]]:
        """Calculate comprehensive cost analysis"""
        
        baseline_cost = {}
        modeled_cost = {}
        savings = {}
        avoidance = {}
        
        for phase in PHASE_ORDER:
            baseline_cost[phase] = baseline_hours[phase] * blended_rate
            modeled_cost[phase] = modeled_hours[phase] * blended_rate
            savings[phase] = baseline_cost[phase] - modeled_cost[phase]
            
            # Cost avoidance calculation
            if include_cost_avoidance and cost_avoidance_config:
                if phase == 'Post Go-Live':
                    # Cost avoidance applies primarily to ongoing operations
                    multiplier = cost_avoidance_config.get('multiplier', 1.0)
                    ongoing_factor = cost_avoidance_config.get('ongoing_factor', 1.0)
                    
                    # Calculate total development savings as basis for avoidance
                    dev_savings = sum(savings[p] for p in PHASE_ORDER if p != 'Post Go-Live')
                    base_avoidance = max(0, dev_savings * ongoing_factor)
                    avoidance[phase] = base_avoidance * multiplier
                else:
                    avoidance[phase] = 0.0
            else:
                avoidance[phase] = 0.0
        
        return {
            'baseline_cost': baseline_cost,
            'modeled_cost': modeled_cost,
            'savings': savings,
            'avoidance': avoidance
        }

    def calculate_risk_adjusted_hours(
        self, 
        modeled_hours: Dict[str, float], 
        risk_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Apply risk weights to modeled hours"""
        risk_adjusted = {}
        for phase in PHASE_ORDER:
            if phase in risk_weights:
                risk_adjusted[phase] = modeled_hours[phase] * risk_weights[phase]
            else:
                risk_adjusted[phase] = modeled_hours[phase]
        return risk_adjusted

    def generate_summary_table(
        self,
        baseline_hours: Dict[str, float],
        modeled_hours: Dict[str, float],
        baseline_cost: Dict[str, float],
        modeled_cost: Dict[str, float],
        risk_adjusted_hours: Dict[str, float]
    ) -> pd.DataFrame:
        """Generate comprehensive summary table"""
        
        summary_data = []
        for phase in PHASE_ORDER:
            hour_variance = modeled_hours[phase] - baseline_hours[phase]
            hour_variance_pct = (hour_variance / baseline_hours[phase] * 100) if baseline_hours[phase] > 0 else 0
            
            cost_variance = modeled_cost[phase] - baseline_cost[phase]
            cost_variance_pct = (cost_variance / baseline_cost[phase] * 100) if baseline_cost[phase] > 0 else 0
            
            summary_data.append({
                'Phase': phase,
                'Baseline Hours': baseline_hours[phase],
                'Modeled Hours': modeled_hours[phase],
                'Hour Variance': hour_variance,
                'Hour Variance %': hour_variance_pct,
                'Baseline Cost': baseline_cost[phase],
                'Modeled Cost': modeled_cost[phase],
                'Cost Variance': cost_variance,
                'Cost Variance %': cost_variance_pct,
                'Risk-Adjusted Hours': risk_adjusted_hours[phase]
            })
        
        return pd.DataFrame(summary_data)

    def get_kpi_summary(
        self,
        baseline_hours: Dict[str, float],
        modeled_hours: Dict[str, float],
        cost_results: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Calculate key performance indicators"""
        
        total_baseline_hours = sum(baseline_hours.values())
        total_modeled_hours = sum(modeled_hours.values())
        total_hours_saved = total_baseline_hours - total_modeled_hours
        total_hours_saved_pct = (total_hours_saved / total_baseline_hours * 100) if total_baseline_hours > 0 else 0
        
        total_baseline_cost = sum(cost_results['baseline_cost'].values())
        total_modeled_cost = sum(cost_results['modeled_cost'].values())
        total_cost_savings = sum(cost_results['savings'].values())
        total_cost_avoidance = sum(cost_results['avoidance'].values())
        total_financial_benefit = total_cost_savings + total_cost_avoidance
        
        return {
            'total_baseline_hours': total_baseline_hours,
            'total_modeled_hours': total_modeled_hours,
            'total_hours_saved': total_hours_saved,
            'total_hours_saved_pct': total_hours_saved_pct,
            'total_baseline_cost': total_baseline_cost,
            'total_modeled_cost': total_modeled_cost,
            'total_cost_savings': total_cost_savings,
            'total_cost_avoidance': total_cost_avoidance,
            'total_financial_benefit': total_financial_benefit
        }

    def generate_initiative_impact_table(
        self,
        effective_deltas: pd.DataFrame,
        maturity_levels: Dict[str, float],
        blended_rate: float,
        include_cost_avoidance: bool = True,
        cost_avoidance_config: Optional[Dict] = None
    ) -> pd.DataFrame:
        """Generate detailed initiative impact analysis"""
        
        impact_data = []
        
        for initiative in effective_deltas.index:
            if maturity_levels.get(initiative, 0) > 0:
                # Calculate hour impacts for development vs post go-live
                dev_phases = ['Discover', 'Plan', 'Design', 'Build', 'Test', 'Deploy']
                dev_hours = sum(effective_deltas.loc[initiative, phase] for phase in dev_phases)
                post_golive_hours = effective_deltas.loc[initiative, 'Post Go-Live']
                
                # Calculate financial impacts
                dev_cost_impact = dev_hours * blended_rate
                post_golive_cost_impact = post_golive_hours * blended_rate
                
                # Add cost avoidance if applicable
                if include_cost_avoidance and cost_avoidance_config and dev_cost_impact < 0:
                    multiplier = cost_avoidance_config.get('multiplier', 1.0)
                    ongoing_factor = cost_avoidance_config.get('ongoing_factor', 1.0)
                    avoidance_value = abs(dev_cost_impact) * ongoing_factor * multiplier
                    post_golive_cost_impact -= avoidance_value
                
                total_financial_impact = dev_cost_impact + post_golive_cost_impact
                
                impact_data.append({
                    'Initiative': initiative,
                    'Maturity %': maturity_levels[initiative],
                    'Baseline Hour Delta': self.matrix_data.loc[initiative].sum(),
                    'Effective Hour Delta': effective_deltas.loc[initiative].sum(),
                    'Development Hours': dev_hours,
                    'Post Go-Live Hours': post_golive_hours,
                    'Development Cost Impact': dev_cost_impact,
                    'Post Go-Live Cost Impact': post_golive_cost_impact,
                    'Total Financial Impact': total_financial_impact
                })
        
        df = pd.DataFrame(impact_data)
        return df.sort_values('Total Financial Impact', ascending=True)


def run_model_scenario(
    total_hours: float = 17054,
    blended_rate: float = 100,
    phase_allocation: Optional[Dict[str, float]] = None,
    maturity_levels: Optional[Dict[str, float]] = None,
    target_savings: float = 15,  # Changed from scenario string to target percentage
    risk_weights: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Convenience function to run a complete modeling scenario
    
    Returns:
        Dict containing all results (summary_df, cost_results, kpi_summary)
    """
    # Use defaults if not provided
    if phase_allocation is None:
        phase_allocation = DEFAULT_PHASE_ALLOCATION.copy()
    
    if maturity_levels is None:
        maturity_levels = {initiative: 50 for initiative in INITIATIVE_FALLBACK}
    
    if risk_weights is None:
        risk_weights = DEFAULT_RISK_WEIGHTS.copy()

    # Run calculations
    model = N2SEfficiencyModel()
    model.create_sample_data()
    
    # Generate simple scenario config for utility function
    scenario_config = {
        'target_percentage': target_savings,
        'current_maturity': {'maturity_level': 2},  # Default to Level 2 for utility
        'description': f"Utility run with {target_savings}% target"
    }
    
    effective_deltas = model.apply_maturity_and_scenario(
        maturity_levels, scenario_config, None
    )
    baseline_hours, modeled_hours = model.calculate_phase_hours(
        total_hours, phase_allocation, effective_deltas
    )
    
    cost_results = model.calculate_costs_and_savings(
        baseline_hours, modeled_hours, blended_rate
    )
    
    risk_adjusted_hours = model.calculate_risk_adjusted_hours(
        modeled_hours, risk_weights
    )
    
    summary_df = model.generate_summary_table(
        baseline_hours, modeled_hours,
        cost_results['baseline_cost'], cost_results['modeled_cost'],
        risk_adjusted_hours
    )
    
    kpi_summary = model.get_kpi_summary(
        baseline_hours, modeled_hours, cost_results
    )
    
    return {
        'model': model,
        'summary_df': summary_df,
        'cost_results': cost_results,
        'kpi_summary': kpi_summary,
        'baseline_hours': baseline_hours,
        'modeled_hours': modeled_hours,
        'effective_deltas': effective_deltas,
        'scenario_config': scenario_config
    } 