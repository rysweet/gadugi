test_solver_result = {
    'test_name': 'test_function_name',
    'original_status': TestStatus.FAIL,
    'final_status': TestStatus.PASS,
    'analysis': TestAnalysis(...),
    'root_cause': 'detailed_root_cause_description',
    'resolution_applied': 'specific_fix_description',
    'skip_reason': None,  # or SkipReason.* if skipped
    'skip_justification': '',  # if skipped
    'validation_results': ['test_pass_confirmation', 'regression_check_pass'],
    'recommendations': ['prevent_similar_issues_in_future']
}
