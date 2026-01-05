# Setup Guide

Step-by-step instructions for running the AI Advising Assistant locally.

## Prerequisites

- Python 3.8 or higher
- pip (comes with Python)
- Terminal/Command Prompt access

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/hmierz/AI-Advising-Assistant.git
cd AI-Advising-Assistant
```

### 2. Create Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv advisor-env
source advisor-env/bin/activate
```

**On Windows (Command Prompt):**
```bash
python -m venv advisor-env
advisor-env\Scripts\activate
```

**On Windows (PowerShell):**
```bash
python -m venv advisor-env
advisor-env\Scripts\Activate.ps1
```

You should see `(advisor-env)` in your terminal prompt when activated.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

This installs Streamlit, Pandas, and other required packages.

### 4. Verify Installation
```bash
streamlit --version
```

Should output something like: `Streamlit, version 1.28.0`

## Running the App

### Start the Dashboard
```bash
streamlit run streamlit_app.py
```

The terminal will show:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

### Open in Browser

Navigate to `http://localhost:8501` in your web browser (Chrome, Firefox, Safari, etc.)

### Stop the App

Press `Ctrl+C` in the terminal where Streamlit is running.

## Common Issues

### "python3: command not found"

Try `python` instead of `python3`:
```bash
python -m venv advisor-env
```

### "streamlit: command not found"

Your virtual environment might not be activated. Look for `(advisor-env)` in your prompt. If missing:
```bash
# Reactivate it
source advisor-env/bin/activate  # macOS/Linux
advisor-env\Scripts\activate      # Windows
```

### "ModuleNotFoundError: No module named 'streamlit'"

Make sure you're in the virtual environment and run:
```bash
pip install -r requirements.txt
```

### Port 8501 Already in Use

If another Streamlit app is running:
```bash
streamlit run streamlit_app.py --server.port 8502
```

Then navigate to `http://localhost:8502`

### CSV Files Not Found

The app creates sample data automatically. If you want to add your own:
1. Create `app/` folder if it doesn't exist
2. Add these files:
   - `faq.csv` (Question, Answer, Tags columns)
   - `core_map_simplified.csv` (Category, RequiredCredits)
   - `policies_simplified.csv` (any columns)
   - `contacts.csv` (any columns)

### Permission Denied (Windows)

If you get "Execution Policy" errors on Windows PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Using Your Own Data

### Student Plan CSV

Upload via the sidebar. Required columns:
- `Credits` (or aliases: Credit Hours, Cr, Hours, Units)
- `Category` (or aliases: Core Category, Area, Type, Requirement)

Optional columns:
- `Course` (CourseID, Course Code)
- `Status` (Planned, Completed)
- `Days`, `Start`, `End`, `Term`

### FAQ CSV

Create `app/faq.csv`:
```csv
Question,Answer,Tags
How do I register?,Go to Banner Self Service,registration
When is add/drop deadline?,Check academic calendar,deadline
```

## Deactivating Virtual Environment

When you're done:
```bash
deactivate
```

## Uninstalling
```bash
# Remove virtual environment
rm -rf advisor-env  # macOS/Linux
rmdir /s advisor-env  # Windows

# Remove the cloned repo
cd ..
rm -rf AI-Advising-Assistant
```

## Getting Help

- Check the [README](README.md) for feature documentation
- Open an issue on GitHub if you find bugs
- Review Streamlit docs: https://docs.streamlit.io/
```

### 3. LICENSE file
```
MIT License

Copyright (c) 2025 Haley Mierzejewski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
