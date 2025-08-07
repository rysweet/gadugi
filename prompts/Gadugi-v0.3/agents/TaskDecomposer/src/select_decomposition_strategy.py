def select_decomposition_strategy(task_analysis):
    """Choose optimal decomposition approach"""

    if task_analysis.has_clear_functional_components():
        return "FUNCTIONAL_DECOMPOSITION"
    elif task_analysis.has_layered_architecture():
        return "LAYER_DECOMPOSITION"
    elif task_analysis.has_sequential_process():
        return "WORKFLOW_DECOMPOSITION"
    elif task_analysis.has_high_risk_components():
        return "RISK_DECOMPOSITION"
    else:
        return "HYBRID_DECOMPOSITION"
