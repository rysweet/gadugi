def setup_github_webhook():
    """Setup GitHub webhook for repository"""

    # 1. Check GitHub token permissions
    verify_github_token()

    # 2. Create webhook endpoint
    webhook_url = create_webhook_endpoint()

    # 3. Configure webhook secret
    webhook_secret = generate_webhook_secret()

    # 4. Install webhook via GitHub API
    install_github_webhook(webhook_url, webhook_secret)

    # 5. Test webhook delivery
    test_webhook_delivery()
