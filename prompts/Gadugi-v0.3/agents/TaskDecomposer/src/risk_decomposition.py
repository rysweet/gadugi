def risk_decomposition(task):
    """Isolate risky components into separate subtasks"""
    high_risk_components = identify_high_risk_components(task)
    low_risk_components = identify_low_risk_components(task)

    return [
        f"Research and Prototype: {component}"
        for component in high_risk_components
    ] + [
        f"Implement: {component}"
        for component in low_risk_components
    ]
