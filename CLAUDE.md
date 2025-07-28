# 🧠 CLAUDE.md: Your Guide to the TEL3SIS Codebase

Welcome, Claude Code! This document is your specialized interface to the **TEL3SIS** repository, designed to provide you with a high-fidelity understanding of our project's architecture, development patterns, and operational nuances. Consider this your direct neural link to the heart of our voice-first AI system.

We've meticulously crafted this guide to empower your code analysis, bug identification, and feature development. Dive in, and let's build the future of intelligent telephony together.

---

## 🌟 Project Overview: The TEL3SIS Vision

**TEL3SIS** is a real-time, voice-first, agentic platform built on `vocode-python`. It's engineered to seamlessly answer incoming phone calls, engage in natural LLM-powered conversations, leverage external tools, record & transcribe audio, and facilitate human handoffs. Our system is designed for robustness, scalability, and intelligent interaction.

---

## 🏗️ Key Architecture Components: The TEL3SIS Blueprint

Understanding our core components is crucial for effective code interaction. Each piece plays a vital role in the symphony of our system.

### Core Services
- **FastAPI Server** (`server/app.py`): The high-performance backbone handling Twilio webhooks, API endpoints, and real-time communication.
- **Celery Workers**: Our asynchronous task masters, diligently processing background operations like transcription, notifications, and cleanup.
- **Redis**: The lightning-fast memory for session state management, real-time data caching, and Celery message brokering.
- **PostgreSQL/SQLite**: Our reliable long-term memory, storing call history, user preferences, and critical application data.
- **ChromaDB**: The semantic powerhouse, enabling vector embeddings for intelligent memory retrieval and long-term conversational context.

### Agent System
- **Core Agent** (`agents/core_agent.py`): The brain of our conversational AI, orchestrating interactions and managing dialogue flow.
- **Tool Integration**: Our dynamic gateway to external capabilities, allowing the agent to intelligently select and execute tools based on user intent.
- **State Machine** (`agents/dialog_state_machine.py`): The meticulous conductor of multi-turn conversations, ensuring coherent and context-aware dialogue flow.
- **Safety Oracle** (`agents/safety_oracle.py`): Our vigilant guardian, performing pre-execution risk checks on LLM responses to ensure safe and ethical interactions (see Issue #442, #437).

### Tools & Integrations
Our agent's capabilities are extended through a rich suite of external integrations:
- **Calendar** (`tools/calendar.py`): Seamless Google Calendar integration with OAuth2 for scheduling and managing events (see Issue #433).
- **Weather** (`tools/weather.py`): Provides real-time weather information via OpenWeatherMap API (see Issue #459).
- **Notifications** (`tools/notifications.py`): Enables SMS and email communication via Twilio/SendGrid.
- **Translation** (`tools/translation.py`): Facilitates multi-language support for diverse user interactions (see Issue #355).
- **Sentiment Analysis** (`tools/sentiment.py`): Analyzes and scores call sentiment for deeper insights (see Issue #370).

---

## 🚀 Development Commands: Your Toolkit for Contribution

These commands are your daily drivers for setting up, running, testing, and maintaining the TEL3SIS codebase.

### Setup & Installation
```bash
# Initialize your development environment with all necessary dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install

# Configure your environment variables (essential for external API access)
cp .env.example .env
# Edit .env with your specific credentials (Twilio, OpenAI, ElevenLabs, etc.)
```

### Running the Application
```bash
# The recommended way to launch the full TEL3SIS stack
docker compose up --build

# For lightweight local development and debugging (non-Docker)
uvicorn server.app:create_app --factory --reload --host 0.0.0.0 --port 3000

# To run background workers for asynchronous tasks
celery -A server.celery_app worker --loglevel=info
celery -A server.celery_app beat --loglevel=info
```

### Testing: Ensuring Robustness
Our comprehensive test suite guarantees code quality and prevents regressions.
```bash
# Execute the full test suite (fast and reliable)
pytest -q

# Run tests with code coverage analysis
pytest --cov=server --cov=agents --cov=tools

# Focus on integration tests for end-to-end flow validation
pytest tests/integration/

# Simulate a full end-to-end call to verify real-time interactions
tel3sis dev-call

# Explore CLI commands and their functionalities
tel3sis --help
tel3sis manage --help
```

### Code Quality & Linting: Maintaining High Standards
Automated checks ensure our codebase remains clean, consistent, and secure.
```bash
# Pre-commit hooks run automatically on every commit (configured in .pre-commit-config.yaml)
pre-commit run --all-files

# Manually format code with Black
black .

# Manually lint and fix issues with Ruff
ruff check --fix .

# Perform static type checking with MyPy
mypy server/ agents/ tools/
```

### Database Operations: Managing Persistence
Commands for schema management and data integrity.
```bash
# Apply pending database migrations
alembic upgrade head

# Generate a new migration script after schema changes
alembic revision --autogenerate -m "description"

# Create and upload a database backup (e.g., to S3)
tel3sis backup --s3

# Restore the database from an archive
tel3sis restore backups/latest.tar.gz
```

### Admin UI (React Frontend): The Control Center
Commands for developing and running the administrative dashboard.
```bash
cd admin-ui
npm install
npm run dev  # Launches development server on localhost:5173
npm run build  # Creates a production-ready build
```

---

## ⚙️ Configuration Management: The Heart of Adaptability

Our configuration is centralized and robust, managed through `server.settings.Settings` (a Pydantic BaseSettings model). This ensures type safety and clear definition of all configurable parameters.

-   Environment variables are loaded from the `.env` file.
-   Critical variables (e.g., `SECRET_KEY`, `BASE_URL`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`) are strictly enforced; the application will fail fast if they are missing.
-   Refer to `CONFIGURATION.md` for a complete and up-to-date reference of all configuration options.

---

## 💡 Important Development Patterns: Our Engineering Philosophy

These patterns define how we build and maintain TEL3SIS, ensuring resilience, security, and maintainability.

### Error Handling: Building for Resilience
-   External API calls are meticulously wrapped in `try/except` blocks with specific exception types.
-   User-friendly fallback messages are provided for tool failures, enhancing the user experience.
-   Structured logging with rich context (e.g., `call_id`) is implemented for efficient debugging and operational insights.

### State Management: Orchestrating Data Flow
-   **Redis** is utilized for short-term session state, managing real-time call context and user actions.
-   **PostgreSQL/SQLite** serves as our mid-term memory, storing call history, user preferences, and other persistent data.
-   **ChromaDB** powers our long-term semantic memory, enabling intelligent retrieval from conversation summaries and factual knowledge bases.

### Security Considerations: Our Unwavering Commitment
Security is paramount in TEL3SIS. We embed security best practices at every layer:
-   OAuth tokens are encrypted using AES-GCM before storage, protecting sensitive user credentials.
-   All secrets are loaded exclusively from environment variables, never hardcoded or committed to the repository.
-   The Safety Oracle actively filters potentially harmful LLM outputs, acting as a critical safeguard.
-   Rate limiting is applied to API endpoints and call ingress to protect against abuse and ensure service availability.

### Testing Strategy: Our Quality Assurance Blueprint
Our testing strategy is comprehensive, ensuring reliability and correctness:
-   `USE_FAKE_SERVICES=true` enables efficient offline testing by mocking external services.
-   Vocode components are meticulously mocked in `tests/utils/vocode_mocks.py` for isolated testing.
-   Integration tests simulate full end-to-end call flows, validating system behavior across components.
-   Property-based testing is employed to uncover edge cases and unexpected behaviors.

---

## ⚡ CLI Tools: Power at Your Fingertips

Our command-line interface provides powerful utilities for development, testing, and system management.

### Main CLI (`tel3sis`)
```bash
tel3sis serve              # Start the web server
tel3sis dev-call           # Simulate a test call
tel3sis warmup             # Pre-load Whisper models for reduced latency
tel3sis red-team           # Run adversarial prompt testing against the agent
tel3sis backup --s3        # Create and upload a database backup to S3
tel3sis restore <archive>  # Restore the database from a specified backup archive
```

### Management CLI (`tel3sis manage`)
```bash
tel3sis manage create-user <username> <password> --role admin # Create a new user with a specified role
tel3sis manage list-users                                    # List all registered users
tel3sis manage update-user <username> --password <new_password> # Update a user's password or role
tel3sis manage delete-user <username>                        # Delete a user
tel3sis manage generate-api-key <username>                   # Generate an API key for a user
tel3sis manage migrate                                       # Apply database migrations
tel3sis manage cleanup --days 30                             # Clean up old call records and data
```

---

## 🎯 Common Development Tasks: Your Contribution Playbook

This section provides actionable steps for common development scenarios, guiding you through the process of extending and maintaining TEL3SIS.

### Adding New Tools: Expanding Agent Capabilities
1.  Create a new tool module in the `tools/` directory (e.g., `tools/new_tool.py`).
2.  Implement your tool class, inheriting from `tools.base.BaseTool`.
3.  Register the tool's JSON schema in the agent configuration for dynamic invocation.
4.  Add comprehensive unit tests covering both success and failure cases for your new tool.
5.  Update relevant documentation (e.g., `README.md`, `docs/api_usage.md`).

### Modifying Agent Behavior: Fine-Tuning Intelligence
-   Agent prompts are primarily defined and managed in `agents/core_agent.py`.
-   Tool selection logic resides in `agents/dialog_state_machine.py`.
-   Safety filtering mechanisms are implemented in `agents/safety_oracle.py`.
-   Always test your agent behavior changes thoroughly with `tel3sis dev-call` before deployment.

### Database Schema Changes: Evolving Data Structures
1.  Modify your models in `server/database.py` to reflect schema changes.
2.  Generate a new migration script: `alembic revision --autogenerate -m "Your descriptive message"`.
3.  Carefully review and edit the generated migration file if necessary.
4.  Apply the migration: `alembic upgrade head`.
5.  Update relevant tests and documentation to reflect the schema changes.

### Adding API Endpoints: Extending Connectivity
-   FastAPI routes are defined in `server/fast_app.py`.
-   Utilize Pydantic models for robust request and response validation.
-   Implement proper error handling and appropriate HTTP status codes.
-   Ensure authentication is applied if required (refer to `server/validation.py`).
-   API documentation is automatically generated from FastAPI annotations.

---

## 📈 Monitoring & Observability: Gaining Insights

Our monitoring infrastructure provides deep insights into system performance and health.

### Metrics & Dashboards
-   Prometheus metrics are exposed at the `/metrics` endpoint.
-   A comprehensive Grafana dashboard is available at `http://localhost:3000/d/tel3sis-latency` for real-time visualization.
-   Custom metrics track call latency, tool usage, error rates, and other critical KPIs.

### Logging
-   Structured logging with `loguru` is configured in `logging_config.py`, ensuring consistent and parseable log output.
-   Log levels include: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
-   Log context includes `call_id`, `user_id`, and detailed operation specifics for enhanced traceability.

### Health Checks
-   A basic `/health` endpoint provides quick service status.
-   A `/readyz` endpoint is available for Kubernetes readiness probes, ensuring services are fully operational before receiving traffic.
-   Individual service health checks are integrated into our monitoring setup.

---

## ☁️ Deployment & Operations: Bringing TEL3SIS to Life

Our deployment strategy focuses on efficiency, reliability, and security.

### Docker Deployment
-   A multi-stage `Dockerfile` optimizes image size and build times.
-   Only production dependencies are included in the final runtime image.
-   Health checks are configured within Docker for robust container orchestration.

### CI/CD Pipeline
-   GitHub Actions workflows in `.github/workflows/` automate our build, test, and deployment processes.
-   `pre-commit` hooks are rigorously enforced in CI, maintaining code quality.
-   Security scanning with Trivy and `git-secrets` is integrated to prevent vulnerabilities.
-   Automated dependency updates are managed via Dependabot.

### Production Considerations
-   Environment-specific configuration is managed through `.env` files and secure secrets management.
-   Database connection pooling and robust migration strategies ensure data integrity.
-   Celery worker scaling is implemented to adapt to varying load.
-   Rate limiting and abuse protection mechanisms safeguard our API and call ingress.
-   Centralized log aggregation and alerting systems provide proactive issue detection.

---

## 🤖 Agent Collaboration System: Our Autonomous Workforce

This repository is actively managed and enhanced by an autonomous agent system (detailed further in `AGENTS.md`). These agents streamline our development workflow and ensure continuous quality.

-   **CoordinatorAgent**: Orchestrates task assignment and manages merge processes.
-   **CodeGenius**: Our primary development agent, assisting with code generation and refactoring.
-   **TestCrafterPro**: Dedicated to test suite maintenance and coverage verification.
-   **SafetyOracle**: Our security and safety expert, reviewing code and LLM outputs for risks.
-   The entire task lifecycle is managed through `tasks.yml`.
-   A multi-agent review process is in place before any code is merged.

---

## 🔗 External Dependencies: Our Extended Ecosystem

### Required Services
-   **Twilio**: Essential for phone calls and SMS communication.
-   **OpenAI**: Powers our LLM and embedding capabilities.
-   **ElevenLabs**: Provides high-quality text-to-speech synthesis.
-   **Google Cloud**: Enables Google Calendar API access for scheduling.
-   **SendGrid**: Facilitates email notifications.

### Optional Services
-   **Deepgram**: An alternative STT provider.
-   **Slack**: For alert notifications and team communication.
-   **PagerDuty**: For critical incident management.
-   **AWS S3**: For secure backup storage.

---

## 🩹 Troubleshooting Common Issues: Your First Aid Kit

Encounter a snag? This section provides quick solutions to common development and operational challenges.

### Call Quality Problems
-   **Check Metrics:** Review STT/TTS latency metrics in Grafana (`http://localhost:3000/d/tel3sis-latency`).
-   **Connectivity:** Verify network connectivity to external APIs (Twilio, OpenAI, ElevenLabs).
-   **Logs:** Examine call logs for specific error patterns or warnings.
-   **Warm-up:** Use `tel3sis warmup` to pre-load models and reduce initial latency.

### Authentication Failures
-   **OAuth Credentials:** Double-check your OAuth credentials in `.env`.
-   **Encryption Key:** Ensure `TOKEN_ENCRYPTION_KEY` is properly set and valid.
-   **User Permissions:** Review user roles and permissions in the admin dashboard.
-   **API Keys:** Test external API keys directly with the respective service to isolate issues.

### Performance Issues
-   **Redis:** Monitor Redis memory usage and connection limits.
-   **Celery:** Check Celery worker queue lengths and resource utilization.
-   **Database:** Review database query performance and optimize slow queries.
-   **Scaling:** Consider scaling up Celery workers or FastAPI instances based on call volume.

---

This project is built on a foundation of security best practices, comprehensive test coverage, and extensive monitoring capabilities. When making changes, always consider the impact on call quality, security, and system reliability.

---

> Crafted with ♥ by **Adrian Wedd** & the TEL3SIS Swarm. Contributions welcome!
