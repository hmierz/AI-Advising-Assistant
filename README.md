# AI-Advising-Assistant
Local Streamlit app for validating student plans and answering program FAQs. Offline, FERPA-friendly demo with CSV inputs. This is a lightweight, FERPA-friendly demo built for portfolio use that runs 100% locally.

A local, offline advisor dashboard that:
- Uploads a **student plan CSV** and validates it (credits, categories, prereqs/coreqs if provided).
- Shows **Policies** and **Contacts** from simple CSVs.
- Provides a **sidebar FAQ Assistant** that answers common questions from `app/faq.csv` (no external APIs).

## Features
- CSV uploads: plan, catalog, category requirements
- Validator: missing fields, credit totals, category checks, prereqs/coreqs (if defined)
- FAQ Assistant: instant Q&A with keyword+fuzzy matching (supports optional `Tags`)
- Notes: one-click **Advisor Notes** export and **Full Report** export
- Clean **pink theme** via `ui_theme.py`

**CSV Specs**
- `app/faq.csv` → columns: `Question`, `Answer`, `Tags` (optional)
- `app/core_map_simplified.csv` → columns: `Category`, `RequiredCredits`
- `app/policies_simplified.csv` → any columns; displayed as a table
- `app/contacts.csv` → any columns; displayed as a table
- **Plan CSV** (upload): must include `Credits` and `Category` (synonyms accepted: “Credit Hours”, “Cr”, “Area/Type/Requirement”, etc.). Optional: `CourseID`, `Status` (“Planned” or “Completed”), `Days`, `Start`, `End`, `Term`.
