def install_gadugi_service():
    """Install Gadugi event service with all dependencies"""

    # 1. Check system requirements
    check_system_requirements()

    # 2. Install Python dependencies
    install_python_dependencies()

    # 3. Setup service configuration
    setup_service_config()

    # 4. Initialize event handlers
    setup_default_event_handlers()

    # 5. Configure GitHub webhook (optional)
    configure_github_webhook()

    # 6. Create systemd service (Linux) or launchd service (macOS)
    create_system_service()

    # 7. Validate installation
    validate_installation()
