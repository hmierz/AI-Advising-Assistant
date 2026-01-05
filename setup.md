# Setup Guide

Step-by-step instructions for running the AI Advising Assistant locally.

## Prerequisites

- Python 3.8 or higher
- pip (comes with Python)
- Command Prompt or Git Bash access

## Installation

### 1. Clone the Repository

Open Command Prompt and run:
```bash
git clone https://github.com/hmierz/AI-Advising-Assistant.git
cd AI-Advising-Assistant
```

### 2. Create Virtual Environment
```bash
python -m venv advisor-env
```

### 3. Activate Virtual Environment

**On Windows (Command Prompt):**
```bash
advisor-env\Scripts\activate
```

**On Windows (PowerShell):**
```bash
advisor-env\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
source advisor-env/bin/activate
```

You should see `(advisor-env)` appear in your terminal prompt.

### 4. Install Dependencies
```bash
pip install streamlit pandas
```

That's it - just two packages needed!

### 5. Run the Application
```bash
streamlit run streamlit_app.py
```

The app will automatically open in your browser at `http://localhost:8501`

## Quick Start After First Setup

Once installed, you only need these steps:
```bash
# Navigate to project folder
cd AI-Advising-Assistant

# Activate environment
advisor-env\Scripts\activate

# Run app
streamlit run streamlit_app.py
```

## Common Issues

### "streamlit: command not found"

Make sure your virtual environment is activated. Look for `(advisor-env)` in your prompt.
```bash
# Reactivate it
advisor-env\Scripts\activate  # Windows
source advisor-env/bin/activate  # Mac/Linux
```

### "File does not exist: streamlit_app.py"

You're not in the correct folder. Navigate to the project directory:
```bash
cd AI-Advising-Assistant
```

Then check if you're in the right place:
```bash
# Windows
dir

# Mac/Linux
ls
```

You should see `streamlit_app.py` in the list.

### Port 8501 Already in Use

If another Streamlit app is running:
```bash
streamlit run streamlit_app.py --server.port 8502
```

Then navigate to `http://localhost:8502`

### Permission Denied (Windows PowerShell)

If you get "Execution Policy" errors on Windows PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or use Command Prompt instead of PowerShell.

### Python Version Issues

This app requires Python 3.8+. Check your version:
```bash
python --version
```

If you have an older version, download the latest from [python.org](https://www.python.org/downloads/)

## Using the App

### Try the Sample Data

1. In the sidebar, toggle "Use sample plan" to ON
2. Click "Validate schedule" to see validation in action
3. Type questions in the FAQ box like "when can I register?" or "how do I drop a class?"

### Upload Your Own Data

Upload a CSV with these required columns:
- `Credits` (or aliases: Credit Hours, Cr, Hours, Units)
- `Category` (or aliases: Core Category, Area, Type, Requirement)

Optional columns:
- `Course`, `Status`, `Days`, `Start`, `End`, `Term`

The app auto-detects common column name variations!

### FAQ Data

The app includes default FAQs, but you can customize by creating `app/faq.csv`:
```csv
Question,Answer,Tags
How do I register?,Go to Banner Self Service,registration
When is add/drop deadline?,Check academic calendar,deadline
```

## Stopping the App

Press `Ctrl+C` in the terminal where Streamlit is running.

## Deactivating Virtual Environment

When you're done:
```bash
deactivate
```

## Uninstalling
```bash
# Remove virtual environment
rmdir /s advisor-env  # Windows
rm -rf advisor-env     # Mac/Linux

# Remove the cloned repo (optional)
cd ..
rmdir /s AI-Advising-Assistant  # Windows
rm -rf AI-Advising-Assistant     # Mac/Linux
```

## Getting Help

- Check the [README](README.md) for feature documentation
- Open an issue on GitHub if you find bugs
- Review Streamlit docs: https://docs.streamlit.io/

## Project Structure
```
AI-Advising-Assistant/
├── app/                      # Data files
│   ├── faq.csv
│   ├── core_map_simplified.csv
│   ├── policies_simplified.csv
│   └── contacts.csv
├── streamlit_app.py          # Main application
├── ui_theme.py               # UI styling
├── requirements.txt          # Python dependencies
└── README.md                 # Documentation
```
