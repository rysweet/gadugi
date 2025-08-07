def manage_configuration():
    """Manage Gadugi service configuration"""

    # 1. Load current configuration
    config = load_service_config()

    # 2. Interactive configuration wizard
    config = configuration_wizard(config)

    # 3. Validate configuration
    validate_configuration(config)

    # 4. Save configuration
    save_service_config(config)

    # 5. Restart service if needed
    restart_service_if_running()
