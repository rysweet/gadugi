def assess_risks(task):
    risks = []

    # Technical risks
    if task.uses_new_technology():
        risks.append(Risk("NEW_TECH", "Learning curve for new technology", "HIGH"))

    # Dependency risks
    if task.has_external_dependencies():
        risks.append(Risk("EXTERNAL_DEPS", "Third-party service reliability", "MEDIUM"))

    # Complexity risks
    if task.complexity_score() > HIGH_THRESHOLD:
        risks.append(Risk("COMPLEXITY", "High complexity may cause delays", "MEDIUM"))

    return risks
