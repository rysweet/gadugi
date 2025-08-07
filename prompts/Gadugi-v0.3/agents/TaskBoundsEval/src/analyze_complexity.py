def analyze_complexity(task):
    # Technical complexity scoring
    tech_score = assess_technical_complexity(task)

    # Domain complexity scoring
    domain_score = assess_domain_complexity(task)

    # Integration complexity scoring
    integration_score = assess_integration_complexity(task)

    # Knowledge complexity scoring
    knowledge_score = assess_knowledge_complexity(task)

    return ComplexityAssessment(
        technical=tech_score,
        domain=domain_score,
        integration=integration_score,
        knowledge=knowledge_score,
        overall=weighted_average([tech_score, domain_score, integration_score, knowledge_score])
    )
