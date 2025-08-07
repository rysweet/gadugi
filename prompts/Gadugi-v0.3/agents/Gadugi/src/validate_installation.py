def validate_installation():
    """Validate Gadugi service installation"""

    # 1. Check service is running
    assert_service_running()

    # 2. Test GitHub webhook (if configured)
    test_github_webhook()

    # 3. Test local event submission
    test_local_events()

    # 4. Validate event handler execution
    test_event_handlers()

    # 5. Check log file creation
    verify_logging_system()
