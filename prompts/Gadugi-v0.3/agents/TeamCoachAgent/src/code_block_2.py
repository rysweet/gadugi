# Configure optimization objectives and weights
optimization_config = {
    'objectives': [
        OptimizationObjective.MAXIMIZE_CAPABILITY,
        OptimizationObjective.BALANCE_WORKLOAD,
        OptimizationObjective.MINIMIZE_RISK
    ],
    'weights': {
        'capability_match': 0.4,
        'performance_prediction': 0.3,
        'availability_score': 0.2,
        'workload_balance': 0.1
    },
    'constraints': {
        'max_team_size': 8,
        'min_capability_coverage': 0.8,
        'max_risk_tolerance': 0.3
    }
}
