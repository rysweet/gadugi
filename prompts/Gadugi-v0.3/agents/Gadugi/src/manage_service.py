def manage_service(action: str):
    """Manage Gadugi service lifecycle"""

    if action == "start":
        start_service()
    elif action == "stop":
        stop_service()
    elif action == "status":
        show_service_status()
    elif action == "restart":
        restart_service()
    elif action == "logs":
        show_service_logs()
