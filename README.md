# 🛡️ GitSentinel

> **Autonomous Pre-Flight Security Scanner & AI Git Copilot for Developers**  
> *Catch secret leaks, eliminate repo bloat, and generate conventional commit messages before code leaves your machine.*

---

## ⚡ Why GitSentinel?

Every developer makes mistakes before pushing code:
- 🚨 **Accidental Secret Leaks:** Pushing `.env` files, API tokens (OpenAI, Gemini, AWS, Stripe), or SSH private keys.
- 🐘 **Repository Bloat:** Unintentionally tracking `node_modules`, `__pycache__`, or giant binary assets (>10MB).
- 🧩 **Dangerous Code Patterns:** Silent error masking (`except: pass`), `eval()` vulnerabilities, or missing `.gitignore` coverage.
- 📝 **Vague Commit Messages:** Committing with messages like `"update"`, `"fix"`, or `"done"` instead of standardized Conventional Commits.

**GitSentinel** solves this as a lightweight, zero-bloat CLI and git hook that guards your repository.

---

## 🚀 Key Capabilities

### 1. 🔍 Secret & Sensitive File Scanner
Scans your staged files or repository for high-entropy tokens and credentials:
- Google Gemini API Keys (`AIzaSy...`)
- OpenAI / Anthropic Keys (`sk-...`)
- AWS Access Keys (`AKIA...`)
- GitHub Personal Access Tokens (`ghp_...`, `github_pat_...`)
- Stripe / Slack / Cloud Secret assignments
- Private cryptographic keys (`.pem`, `id_rsa`)
- Unprotected `.env` environments

### 2. 🩺 Repository Health Doctor (`gitsentinel doctor`)
Runs a comprehensive diagnostic check:
- `.gitignore` completeness and rule hygiene
- Tracked blob sizes and bloat indicators
- Documentation (`README.md`) and licensing compliance
- Remote origin configuration and branch health
- Computes an actionable **Repository Health Score (0-100)**

### 3. 🤖 AI & Rule-Based Conventional Commit Synthesizer (`gitsentinel commit`)
Inspects your actual `git diff` and change status to synthesize professional Conventional Commit titles:
- Classifies changes as `feat`, `fix`, `docs`, `refactor`, `test`, or `chore`.
- Auto-infers the target module scope.
- Optional integration with **Google Gemini 2.5 Flash** for deep semantic summaries.

### 4. 🪝 One-Command Git Pre-Commit Hook (`gitsentinel install-hook`)
Installs a native `.git/hooks/pre-commit` script that automatically blocks any commit containing critical secrets.

---

## 📦 Installation & Quickstart

```bash
# Clone the repository
git clone https://github.com/Rishabhraj06/GitSentinel.git
cd GitSentinel

# Install locally in editable mode
pip install -e .
```

---

## 💻 Usage Examples

### 1. Scan Current Repository for Risks
```bash
# Scan working directory
gitsentinel scan

# Scan and fail CI/pre-commit on critical secrets
gitsentinel scan --fail-on-critical
```

### 2. Run Repository Health Doctor
```bash
gitsentinel doctor
```

### 3. Generate Conventional Commit
```bash
# Preview suggested commit title and change breakdown
gitsentinel commit

# Supply an optional intent hint
gitsentinel commit --hint "implement user authentication"

# Auto-execute git commit directly
gitsentinel commit --auto
```

### 4. Install Pre-Commit Security Hook
```bash
gitsentinel install-hook
```

---

## 🧪 Real-World Verification

GitSentinel comes with an automated Pytest test suite covering all security detectors, AST parsers, and diagnostic engines:

```bash
python -m pytest tests/ -v
# 9 passed in 0.38s (100% test pass rate)
```

---

## 👤 Author & Architecture

- **Author:** Rishabh Raj ([@Rishabhraj06](https://github.com/Rishabhraj06))
- **Architecture Tenet:** Minimal external dependencies, standard library first, zero bloat, high execution speed.
- **License:** MIT
