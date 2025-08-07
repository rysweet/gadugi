def create_new_fixture(fixture_name, purpose):
    """Create new fixture when shared ones don't suffice."""
    return f'''
@pytest.fixture
def {fixture_name}():
    """
    {purpose}

    Provides: {describe_fixture_provides()}
    Cleanup: {describe_cleanup_behavior()}
    Scope: function (default for isolation)
    """
    # Setup
    resource = create_test_resource()

    yield resource

    # Cleanup
    cleanup_test_resource(resource)
'''
