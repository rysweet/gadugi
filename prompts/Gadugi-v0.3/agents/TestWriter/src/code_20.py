test_writer_result = {
    'module_name': 'test_module_name',
    'tests_created': [
        {
            'test_name': 'test_function_name',
            'purpose': 'what_this_test_validates',
            'coverage_areas': ['functionality', 'error_handling', 'edge_cases'],
            'fixtures_used': ['fixture1', 'fixture2'],
            'validation_status': 'passed_all_checks'
        }
    ],
    'fixtures_created': [
        {
            'fixture_name': 'new_fixture_name',
            'purpose': 'fixture_purpose',
            'scope': 'function'
        }
    ],
    'coverage_analysis': {
        'lines_covered': 'percentage',
        'branches_covered': 'percentage',
        'functions_covered': 'list_of_functions'
    },
    'tdd_alignment': {
        'design_guidance_provided': True,
        'interfaces_specified': True,
        'behaviors_documented': True
    },
    'quality_metrics': {
        'idempotent': True,
        'parallel_safe': True,
        'well_documented': True,
        'follows_patterns': True
    }
}
