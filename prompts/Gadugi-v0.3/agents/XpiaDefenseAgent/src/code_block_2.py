from xpia_defense import XPIADefenseAgent

defense = XPIADefenseAgent()
validation_result = defense.validate_content(
    content=suspicious_input,
    context="agent_communication",
    strict_mode=True
)

if validation_result.is_safe:
    process_content(validation_result.sanitized_content)
else:
    handle_threat(validation_result.threat_analysis)
