# 🛡️ AssumptionGuard — Find Missing Assumptions & Constraints

**AssumptionGuard** is a developer & product intelligence tool that surfaces silent assumptions, overlooked constraints, and critical stakeholder questions from project briefs and specifications before a single line of code is written.

Powered by Google's **Gemini 1.5 Flash** and **Gemini 2.0 Flash** models.

---

## ✨ Features

- **Automated Risk Analysis**: Uncovers unstated assumptions, operational constraints, and critical architectural/product questions.
- **Impact Prioritization**: Color-coded badges (`High`, `Medium`, `Low`) with evidence quotes and actionable recommendations.
- **Summary Metrics**: High-level impact counter banner for quick risk assessment.
- **Multiple Input Methods**:
  - Direct paste into text area
  - Upload specification files (`.txt`, `.md`)
  - 1-click sample scenarios (Legal DocEditor SaaS, Hyperlocal Marketplace, AI Copilot)
- **Export & Inspection**: Download findings as structured JSON or inspect the raw response.
- **Flexible Secret Management**: Seamlessly uses Streamlit Secrets, environment variables, or sidebar key entry.

---

## 🚀 Quickstart (Local Development)

### 1. Clone the repository
```bash
git clone https://github.com/AishaBhaktani-codes/AssumptionGuard.git
cd AssumptionGuard
```

### 2. Set up a virtual environment (recommended)
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your Gemini API key
Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/).

You can set your key in either of two ways:

**Option A (Recommended for Streamlit):** Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-api-key-here"
```

**Option B:** Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your-api-key-here
```

*(Note: Both `.streamlit/secrets.toml` and `.env` are already included in `.gitignore` to keep your credentials safe.)*

### 5. Run the app
```bash
python -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## ☁️ Deployment on Streamlit Community Cloud (Free)

Follow these steps to deploy the app for free on **Streamlit Community Cloud**:

### Step 1: Push your code to GitHub
Make sure your latest code is committed and pushed to your GitHub repository (see the [Git Commands](#-git-commands-to-push-your-changes) section below).

### Step 2: Create a new app on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
2. Click **"New app"**.
3. Select your repository: `AishaBhaktani-codes/AssumptionGuard`
4. Set **Branch**: `main`
5. Set **Main file path**: `app.py`

### Step 3: Add your API Key in Streamlit Secrets
1. Before clicking Deploy, expand **"Advanced settings..."** (or go to App Settings > Secrets after creating the app).
2. In the **Secrets** text area, paste your Gemini API key in TOML format:
   ```toml
   GEMINI_API_KEY = "AIzaSy..."
   ```
   *(Note: `GOOGLE_API_KEY` is also supported)*
3. Click **"Save"**.

### Step 4: Deploy
Click **"Deploy!"** Streamlit will provision the container, install packages from `requirements.txt`, and launch your live application with a public URL.

---

## 🛠️ Git Commands to Push Your Changes

Run the following commands inside the `AssumptionGuard` folder:

```bash
# 1. Check changed and untracked files
git status

# 2. Stage all project files (secrets.toml and .env are safely ignored)
git add .

# 3. Commit the changes
git commit -m "Prepare AssumptionGuard for Streamlit Community Cloud deployment"

# 4. Push to your GitHub repository
git push origin main
```

---

## 📦 Project Structure

```text
AssumptionGuard/
├── .streamlit/
│   └── secrets.toml.example   # Example template for Streamlit secrets
├── .env.example               # Example template for environment variables
├── .gitignore                 # Excludes secrets.toml, .env, __pycache__, etc.
├── app.py                     # Main Streamlit application
├── requirements.txt           # Minimal dependencies for Streamlit Cloud
└── README.md                  # Project overview & deployment instructions
```

---

## 📄 License
MIT License
