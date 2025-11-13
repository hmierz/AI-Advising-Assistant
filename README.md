# AI Advising Assistant

AI Advising Assistant is a local, offline Streamlit dashboard for reviewing student plans and answering advising FAQs related to Saint Louis University's Physical Therapy program. The app is designed to be FERPA-compliant, using only CSV inputs without sending any data to external servers.

This project includes a student plan validator, a table viewer for policies and contacts, and an AI-style FAQ assistant. It is a lightweight prototype for advisor-facing automation.

## AI FAQ Assistant

The sidebar includes an FAQ Assistant that uses local keyword and fuzzy matching to answer common advising questions. It reads from `faq.csv` and requires no API calls.

You can ask questions such as:
- When should I take anatomy?
- How do I study abroad?

The assistant searches based on exact words and tags, then returns the best matching answer from the file. This is designed to mimic chatbot functionality in an offline environment.

## Plan Validator

Users can upload a student course plan as a CSV file. The app will:
- Validate required fields such as credit hours and category
- Flag missing or duplicate entries
- Sum total credits by category
- Optionally check for prerequisites and corequisites if included

## Other Features

- CSV uploads for student plan, core map, policies, and contacts
- One-click export for Advisor Notes or full session report
- Custom UI styling applied via `ui_theme.py` with soft pink tones

## CSV File Structure

These are the expected files and required columns:

- `faq.csv`: Question, Answer, Tags (optional)
- `core_map_simplified.csv`: Category, RequiredCredits
- `policies_simplified.csv`: Any columns; displayed as-is
- `contacts.csv`: Any columns; displayed as-is
- Student Plan upload: Requires Credits and Category fields (aliases accepted: Credit Hours, Cr, Area, Type, Requirement, etc.)

Optional student plan columns: CourseID, Status (Planned or Completed), Days, Start, End, Term

## Future Development

Planned features include:
- A student-facing version with form input instead of CSV
- Prerequisite/corequisite logic based on scraped catalog data
- Rule-based engine to flag program-specific advising issues
- Transcript parsing from PDF or DegreeWorks export
- Enhanced UI with buttons, tooltips, and layout improvements
- Export capability for integration with advisor systems

## Demo

A live or recorded demo will be added soon.

## Local Setup Instructions

1. Clone this repository or download it as a ZIP
2. Create a virtual environment  
   `python -m venv advisor-env`
3. Activate the environment  
   `advisor-env\Scripts\activate`
4. Install dependencies  
   `pip install -r requirements.txt`
5. Launch the app  
   `streamlit run streamlit_app.py`

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
