# 🚀 Contributing to TEL3SIS: Join the Swarm!

Welcome, fellow architect of intelligent systems! Your interest in contributing to **TEL3SIS** means you're ready to shape the future of voice-first AI. We're building something truly impactful, and your code, ideas, and insights are the bedrock of our success. This guide is your launchpad into our collaborative universe.

We believe in empowering our contributors. Every line of code, every thoughtful comment, every bug squashed, and every piece of documentation polished directly enhances the power and reach of TEL3SIS. Let's build something extraordinary, together.

---

## 🛠️ Getting Started: Your Local TEL3SIS Lab

Getting your local TEL3SIS lab ready is straightforward. Follow these steps to set up your development environment and join the ranks of our contributors:

1.  **Clone the repository** and create a Python 3.11 virtual environment:
    ```bash
    git clone https://github.com/yourname/TEL3SIS.git
    cd TEL3SIS
    python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements-dev.txt
    ```
    *Why `requirements-dev.txt`?* This ensures you have all the tools our core team uses for testing, linting, and development.

2.  **Install `git-secrets`**: This crucial tool prevents accidental credential leaks. Install it **before running pre-commit** to safeguard our codebase.
    ```bash
    # For Debian/Ubuntu
    sudo apt-get install -y git-secrets
    # For macOS (using Homebrew)
    # brew install git-secrets
    git secrets --install -f
    ```

---

## ✨ Guardians of Quality: Pre-commit Hooks

Our `pre-commit` hooks aren't just rules; they're your first line of defense for code quality and security. They ensure every line you commit aligns with our high standards, catching issues before they even think about reaching a Pull Request.

Install the hooks and make them your trusted companions before every push:

```bash
pre-commit install
pre-commit run --all-files
```

*Troubleshooting:* If `git-secrets` isn't found, ensure you've completed step 2 above. The `build-docs` hook requires **MkDocs** version 1.5.3 or newer; if needed, install it with `pip install "mkdocs>=1.5.3"`.

These hooks will automatically format your code with **Black**, lint with **Ruff**, scan for secrets with **git-secrets**, and build the documentation to catch rendering issues.

---

## 🧪 The Crucible of Code: Running Tests

Tests are our safety net, our truth serum, and our promise of stability. Before you even think about opening a PR, make sure our test suite sings a symphony of success. Execute the full test suite locally to catch regressions and validate your changes:

```bash
pytest -q
```

We leverage `USE_FAKE_SERVICES=true` in our test suite (configured in `tests/conftest.py`) to allow for offline testing without external API dependencies, ensuring fast and reliable feedback.

---

## 🗺️ Navigating Contributions: Branching & Pull Requests

Precision in naming is key to our collective clarity. Our branching and Pull Request conventions are designed to keep our development flow as smooth as a perfectly transcribed conversation.

-   **Branch Naming:** Follow the workflow defined in `tasks.yml` and our `README.md`.
    Branches use the format `<phase>/<task_id>-slug`.
    Example:
    ```bash
    git checkout -b core-mvp/CORE-01-setup
    ```
-   **Commit Messages:** We adhere strictly to the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification: `type(scope): summary`.
-   **Pull Requests:** Every PR must reference its associated task ID from `tasks.yml` and utilize our comprehensive PR template. This ensures clarity, traceability, and a streamlined review process.

**Crucially:** Ensure all `pre-commit` checks pass and `pytest` runs clean before opening a PR. Your PR must pass CI and receive at least one approval before it can be merged.

---

## ♻️ Keeping Dependencies Sharp

Keeping our dependencies sharp and secure is a team effort. Runtime packages are managed in `requirements.in`, and development tools in `requirements-dev.in`. When you introduce new packages or update existing ones, remember to regenerate the lock files:

```bash
pip-compile requirements.in
pip-compile requirements-dev.in
```
Commit the updated `.txt` files alongside your code changes.

---

## 🔒 Security First: Local Scans

Security isn't an afterthought; it's baked into our DNA. While all pull requests run automated Trivy scans via `security.yml`, you can be our first line of defense by running local checks:

```bash
docker build -t tel3sis .
trivy image --severity HIGH --no-progress tel3sis
```

---

## 🌟 What We're Looking For: Impactful Contributions

We're always on the lookout for contributions that align with our mission and enhance TEL3SIS in meaningful ways. We prioritize contributions that:

-   **Address Critical Bugs:** Stability and reliability are paramount.
-   **Complete Features:** Help us bring existing features to full fruition.
-   **Enhance Documentation:** Clarity is a superpower. Improve our guides, comments, and explanations.
-   **Boost Performance & Scalability:** Optimize our systems for speed and efficiency.
-   **Strengthen Security:** Fortify our defenses against vulnerabilities.
-   **Introduce Innovative Tools:** Expand TEL3SIS's capabilities with new integrations.
-   **Improve Developer Experience:** Make it easier and more enjoyable for others to contribute.

---

Ready to make your mark? Dive in, explore, and let's build the future of voice-first AI, one exceptional contribution at a time. We're excited to see what you bring to the TEL3SIS Swarm!