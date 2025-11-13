# AI Advising Assistant

A local Streamlit app for validating student plans and answering advising FAQs related to Saint Louis University's Physical Therapy program. This is an offline, FERPA-friendly demo using CSV inputs. The project is ongoing with plans for future improvements. It was devloped as both a passion project and a practical endeavor to increase efficency for students and staff alike.

## Overview

This local advisor dashboard allows users to:

- Upload a student plan CSV and validate it for credit requirements, categories, and optional prerequisites/corequisites
- Display policies and contacts from structured CSV files
- Use a sidebar FAQ Assistant to answer common questions (no external APIs)
- Export one-click advising notes and full plan reports

## Features

- **CSV Uploads**: student plan, course catalog, credit categories
- **Validation Engine**: identifies missing fields, credit totals, category mismatches, and (optionally) prereqs/coreqs
- **FAQ Assistant**: instant Q&A with keyword and fuzzy matching based on a local `faq.csv` file
- **Notes Export**: downloadable advising notes and full student report
- **Custom UI**: theme implemented via `ui_theme.py`

## CSV Structure

The app expects the following CSVs:

- `faq.csv` — Columns: `Question`, `Answer`, `Tags` (optional)
- `core_map_simplified.csv` — Columns: `Category`, `RequiredCredits`
- `policies_simplified.csv` — Any columns; displayed as a table
- `contacts.csv` — Any columns; displayed as a table
- **Student Plan Upload** — Required columns: `Credits`, `Category`  
  Synonyms accepted: "Credit Hours", "Cr", "Area/Type/Requirement", etc.  
  Optional columns: `CourseID`, `Status` ("Planned" or "Completed"), `Days`, `Start`, `End`, `Term`

## Future Development

Planned enhancements include:

- Student-facing version with form input instead of CSV
- Prerequisite/corequisite enforcement using scraped catalog data
- Department-specific advising rules engine (e.g., auto-flagging issues)
- Integration with PDF transcript parsing or DegreeWorks exports
- Cleaner UI with buttons, hover tips, and dynamic layout
- Optional export to DegreeWorks or advisor-facing systems

## Demo

A live or video demo will be added soon.

## Running the App

To launch the app locally:

```bash
streamlit run streamlit_app.py
