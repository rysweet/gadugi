# CI/CD Best Practices and Patterns

## Pipeline Architecture

### Multi-Stage Pipeline Design
```yaml
# Example GitHub Actions workflow
name: CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Run tests
        run: |
          pip install -e .
          pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build application
        run: |
          python -m build
          docker build -t app:${{ github.sha }} .

  deploy:
    needs: [test, build]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: echo "Deploying to production"
```

### Pipeline Stages Best Practices

#### 1. Source Control Integration
- **Trigger Patterns**:
  - Push to main/master: Full pipeline
  - Pull requests: Test and build only
  - Tags: Release pipeline
  - Scheduled: Nightly builds, security scans

#### 2. Build Stage
- **Parallel builds** for different platforms/versions
- **Caching** for dependencies and build artifacts
- **Artifact management** for downstream stages
- **Build matrix** for multiple environments

#### 3. Test Stage
- **Unit tests**: Fast, isolated tests
- **Integration tests**: Component interaction tests
- **E2E tests**: Full system tests
- **Performance tests**: Load and stress tests
- **Security tests**: Vulnerability scanning

#### 4. Quality Gates
- **Code coverage** thresholds (80%+ recommended)
- **Type checking** (MyPy, Pyright)
- **Linting** (Black, Flake8, ESLint)
- **Security scanning** (Bandit, Safety)
- **Dependency checks** (pip-audit, npm audit)

## Environment Management

### Environment Strategy
```yaml
environments:
  development:
    url: https://dev.example.com
    secrets: DEV_SECRETS
  staging:
    url: https://staging.example.com
    secrets: STAGING_SECRETS
    protection_rules:
      required_reviewers: 1
  production:
    url: https://example.com
    secrets: PROD_SECRETS
    protection_rules:
      required_reviewers: 2
      delay_timer: 5
```

### Configuration Management
- **Environment variables** for configuration
- **Secret management** (GitHub Secrets, AWS Secrets Manager)
- **Feature flags** for gradual rollouts
- **Configuration validation** before deployment

## Testing Patterns

### Test Pyramid Strategy
```yaml
# Unit Tests (70%)
- name: Unit Tests
  run: |
    uv run pytest tests/unit/ \
      --cov=src \
      --cov-report=xml \
      --cov-fail-under=80

# Integration Tests (20%)
- name: Integration Tests
  run: |
    docker-compose up -d database
    uv run pytest tests/integration/ \
      --timeout=300
    docker-compose down

# E2E Tests (10%)
- name: E2E Tests
  run: |
    uv run pytest tests/e2e/ \
      --browser=chrome \
      --timeout=600
```

### Test Data Management
```yaml
- name: Setup Test Data
  run: |
    # Use fixtures or factories
    python scripts/setup_test_data.py

    # Or use test containers
    docker run --rm -d \
      --name test-db \
      -p 5432:5432 \
      -e POSTGRES_DB=test \
      postgres:13
```

### Flaky Test Handling
```yaml
- name: Run Tests with Retry
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 10
    max_attempts: 3
    retry_on: error
    command: uv run pytest tests/ --reruns=2
```

## Deployment Strategies

### Blue-Green Deployment
```yaml
deploy-blue-green:
  steps:
    - name: Deploy to Green Environment
      run: |
        kubectl apply -f k8s/green-deployment.yaml
        kubectl wait --for=condition=available deployment/app-green

    - name: Health Check Green
      run: |
        curl -f https://green.example.com/health

    - name: Switch Traffic to Green
      run: |
        kubectl patch service app-service \
          -p '{"spec":{"selector":{"version":"green"}}}'

    - name: Cleanup Blue
      run: |
        kubectl delete deployment app-blue
```

### Canary Deployment
```yaml
deploy-canary:
  steps:
    - name: Deploy Canary (10% traffic)
      run: |
        kubectl apply -f k8s/canary-deployment.yaml
        kubectl patch ingress app-ingress \
          --patch-file=canary-patch.yaml

    - name: Monitor Canary Metrics
      run: |
        python scripts/monitor_canary.py --duration=300

    - name: Promote or Rollback
      run: |
        if [ $CANARY_SUCCESS = "true" ]; then
          kubectl apply -f k8s/full-deployment.yaml
        else
          kubectl delete -f k8s/canary-deployment.yaml
        fi
```

### Rolling Deployment
```yaml
deploy-rolling:
  steps:
    - name: Rolling Update
      run: |
        kubectl set image deployment/app \
          app=myapp:${{ github.sha }}
        kubectl rollout status deployment/app

    - name: Rollback on Failure
      if: failure()
      run: |
        kubectl rollout undo deployment/app
```

## Security Best Practices

### Secrets Management
```yaml
# Environment-specific secrets
- name: Deploy with Secrets
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    API_KEY: ${{ secrets.API_KEY }}
  run: |
    # Never log secrets
    echo "Deploying with configured secrets"
```

### Security Scanning
```yaml
security-scan:
  steps:
    - name: Dependency Vulnerability Scan
      run: |
        uv run pip-audit
        uv run safety check

    - name: Code Security Scan
      run: |
        uv run bandit -r src/
        uv run semgrep --config=auto src/

    - name: Container Security Scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'myapp:${{ github.sha }}'
        format: 'sarif'
        output: 'trivy-results.sarif'
```

### Access Control
- **Principle of least privilege** for service accounts
- **Branch protection rules** for critical branches
- **Required reviews** for production deployments
- **Time-based access** for sensitive operations

## Performance Optimization

### Build Optimization
```yaml
- name: Optimized Build
  run: |
    # Use build cache
    docker build \
      --cache-from=myapp:latest \
      --build-arg BUILDKIT_INLINE_CACHE=1 \
      -t myapp:${{ github.sha }} .

    # Multi-stage builds
    docker build \
      --target=production \
      -t myapp:${{ github.sha }} .
```

### Parallel Execution
```yaml
test-matrix:
  strategy:
    matrix:
      os: [ubuntu-latest, windows-latest, macos-latest]
      python-version: [3.9, 3.10, 3.11]
    fail-fast: false
  runs-on: ${{ matrix.os }}
```

### Caching Strategies
```yaml
- name: Cache Dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('uv.lock') }}

- name: Cache Docker Layers
  uses: actions/cache@v3
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
    restore-keys: ${{ runner.os }}-buildx-
```

## Monitoring and Observability

### Pipeline Monitoring
```yaml
- name: Send Metrics
  if: always()
  run: |
    # Send pipeline metrics to monitoring system
    curl -X POST https://metrics.example.com/api/v1/metrics \
      -H "Content-Type: application/json" \
      -d '{
        "pipeline": "${{ github.workflow }}",
        "status": "${{ job.status }}",
        "duration": "${{ steps.timer.outputs.duration }}"
      }'
```

### Deployment Monitoring
```yaml
- name: Post-Deployment Health Check
  run: |
    # Wait for deployment to stabilize
    sleep 30

    # Check health endpoints
    curl -f https://api.example.com/health

    # Check key metrics
    python scripts/check_metrics.py \
      --threshold-error-rate=1% \
      --threshold-response-time=500ms
```

### Alerting Integration
```yaml
- name: Send Alert on Failure
  if: failure()
  run: |
    curl -X POST https://hooks.slack.com/services/... \
      -H 'Content-Type: application/json' \
      -d '{
        "text": "🚨 Pipeline failed: ${{ github.workflow }} on ${{ github.ref }}"
      }'
```

## Documentation and Compliance

### Pipeline Documentation
- **README with setup instructions**
- **Architecture decision records (ADRs)**
- **Runbooks for common operations**
- **Disaster recovery procedures**

### Compliance Automation
```yaml
compliance-checks:
  steps:
    - name: Generate SBOM
      run: |
        cyclone-dx requirements.txt > sbom.json

    - name: License Compliance
      run: |
        pip-licenses --format=json > licenses.json

    - name: Audit Log
      run: |
        echo "Deployment audit: $(date)" >> audit.log
        echo "Deployer: ${{ github.actor }}" >> audit.log
        echo "Commit: ${{ github.sha }}" >> audit.log
```

## Error Handling and Recovery

### Failure Recovery Patterns
```yaml
deploy:
  steps:
    - name: Deploy with Rollback
      run: |
        # Store previous version
        PREVIOUS_VERSION=$(kubectl get deployment app -o jsonpath='{.spec.template.spec.containers[0].image}')
        echo "PREVIOUS_VERSION=$PREVIOUS_VERSION" >> $GITHUB_ENV

        # Deploy new version
        kubectl set image deployment/app app=myapp:${{ github.sha }}
        kubectl rollout status deployment/app --timeout=300s

      # Automatic rollback on health check failure
    - name: Health Check
      run: |
        if ! curl -f https://api.example.com/health; then
          echo "Health check failed, rolling back"
          kubectl set image deployment/app app=$PREVIOUS_VERSION
          kubectl rollout status deployment/app
          exit 1
        fi
```

### Circuit Breaker Pattern
```python
# In deployment scripts
import time
import requests

def deploy_with_circuit_breaker(endpoint, max_failures=3, timeout=60):
    failures = 0
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{endpoint}/health")
            if response.status_code == 200:
                return True
            failures += 1
        except requests.RequestException:
            failures += 1

        if failures >= max_failures:
            raise Exception("Circuit breaker opened - too many failures")

        time.sleep(5)

    return False
```

## Advanced Patterns

### GitOps Integration
```yaml
gitops-deploy:
  steps:
    - name: Update GitOps Repository
      run: |
        # Clone GitOps repo
        git clone https://github.com/org/gitops-repo.git
        cd gitops-repo

        # Update image tag
        yq e '.spec.template.spec.containers[0].image = "myapp:${{ github.sha }}"' \
          -i environments/prod/deployment.yaml

        # Commit and push
        git add .
        git commit -m "Update prod to ${{ github.sha }}"
        git push origin main
```

### Multi-Cloud Deployment
```yaml
deploy-multi-cloud:
  strategy:
    matrix:
      cloud: [aws, azure, gcp]
  steps:
    - name: Deploy to ${{ matrix.cloud }}
      run: |
        case "${{ matrix.cloud }}" in
          aws)
            aws ecs update-service --service myapp --task-definition myapp:${{ github.sha }}
            ;;
          azure)
            az container create --resource-group rg --name myapp --image myapp:${{ github.sha }}
            ;;
          gcp)
            gcloud run deploy myapp --image gcr.io/project/myapp:${{ github.sha }}
            ;;
        esac
```

### Feature Flag Integration
```yaml
- name: Deploy with Feature Flags
  run: |
    # Deploy code
    kubectl apply -f deployment.yaml

    # Update feature flags
    curl -X PUT https://feature-flags.example.com/api/flags/new-feature \
      -H "Authorization: Bearer ${{ secrets.FEATURE_FLAG_TOKEN }}" \
      -d '{"enabled": true, "rollout": 10}'
```

This comprehensive CI/CD guide covers modern practices for reliable, secure, and efficient software delivery pipelines.
