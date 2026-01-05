from ui_theme import apply_theme
import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re
from difflib import SequenceMatcher

# ============================================================================
# FAQ SEARCH HELPERS
# ============================================================================

_WORD_RE = re.compile(r"[A-Za-z0-9']+")

def _normalize_text(s: str) -> str:
    """Extract alphanumeric words and lowercase."""
    return " ".join(_WORD_RE.findall(str(s).lower()))

def _tokens(s: str) -> List[str]:
    return _normalize_text(s).split()

def _bigrams(tokens: List[str]) -> List[Tuple[str, str]]:
    """Generate consecutive word pairs for phrase matching."""
    return list(zip(tokens, tokens[1:])) if len(tokens) > 1 else []

def load_faq_csv(path: Path) -> List[Dict[str, str]]:
    """Load FAQ CSV with Question, Answer, and optional Tags columns."""
    try:
        df = pd.read_csv(path)
        cols = {c.lower(): c for c in df.columns}
        qcol = cols.get("question")
        acol = cols.get("answer")
        tcol = cols.get("tags")
        
        if not qcol or not acol:
            return []
        
        out = []
        for _, r in df.iterrows():
            q = str(r[qcol]).strip()
            a = str(r[acol]).strip()
            tags = str(r[tcol]).strip() if tcol and not pd.isna(r[tcol]) else ""
            blob = " ".join([q, a, tags])
            out.append({
                "q": q,
                "a": a,
                "tags": tags,
                "q_norm": _normalize_text(q),
                "all_norm": _normalize_text(blob),
            })
        return out
    except Exception:
        return []

def default_faq() -> List[Dict[str, str]]:
    """Fallback FAQ data if no CSV is provided."""
    base = [
        ("How do I find my registration time?", "Open Banner Self Service → Student → Registration → Check Registration Eligibility.", "registration,time ticket,eligibility"),
        ("What should I do if a class is full?", "Pick a backup course, monitor for openings, and contact the department for overrides.", "class full,closed,override"),
        ("Who clears my advising hold?", "Your advisor clears it after reviewing your plan. The confirmation email means it's cleared.", "advising hold,remove hold"),
        ("How do I withdraw from a course?", "Follow the 'Withdraw in Banner Self Service' PDF in Policies. Deadlines apply.", "withdraw,drop class"),
        ("Can you advise my minor?", "Please contact the minor's department; see Contacts for details.", "minor advising"),
    ]
    out = []
    for q, a, tags in base:
        out.append({
            "q": q, "a": a, "tags": tags,
            "q_norm": _normalize_text(q),
            "all_norm": _normalize_text(" ".join([q, a, tags])),
        })
    return out

def faq_corpus(app_base: Path) -> List[Dict[str, str]]:
    """Load FAQ corpus from CSV or return default."""
    p = app_base / "app" / "faq.csv"
    rows = load_faq_csv(p)
    return rows if rows else default_faq()

def _overlap_score(q_tokens: List[str], t_tokens: List[str]) -> float:
    """Fraction of query words that appear in target."""
    if not q_tokens or not t_tokens:
        return 0.0
    qs, ts = set(q_tokens), set(t_tokens)
    return len(qs & ts) / max(1, len(qs))

def _bigram_score(q_tokens: List[str], t_tokens: List[str]) -> float:
    """Fraction of query bigrams that appear in target."""
    q2 = set(_bigrams(q_tokens))
    t2 = set(_bigrams(t_tokens))
    return len(q2 & t2) / max(1, len(q2)) if q2 else 0.0

def _fuzzy_ratio(a: str, b: str) -> float:
    """String similarity score (0 to 1)."""
    return SequenceMatcher(None, a, b).ratio()

def _score_query(query: str, row: Dict[str, str]) -> float:
    """Score FAQ row relevance using weighted word overlap, bigrams, and fuzzy matching.
    
    Weights favor exact word matches and tag overlap to surface the most relevant FAQs.
    """
    qn = _normalize_text(query)
    qtok = _tokens(query)
    all_tok = _tokens(row.get("all_norm", ""))
    tags_tok = _tokens(row.get("tags", ""))

    return (
        0.40 * _overlap_score(qtok, all_tok)
        + 0.30 * _overlap_score(qtok, tags_tok)
        + 0.15 * _bigram_score(qtok, all_tok)
        + 0.15 * _fuzzy_ratio(qn, row.get("q_norm", ""))
    )

def faq_top_matches(query: str, faqs: List[Dict[str, str]], k: int = 3) -> List[Tuple[Dict[str, str], float]]:
    """Return top k FAQ matches sorted by score."""
    scored = [(row, _score_query(query, row)) for row in faqs]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]

def faq_answer(query: str, faqs: List[Dict[str, str]], threshold: float = 0.38) -> Tuple[Optional[Dict[str, str]], List[Tuple[Dict[str, str], float]]]:
    """Return (best_match_or_None, top3_with_scores)."""
    if not query or not faqs:
        return None, []
    top3 = faq_top_matches(query, faqs, k=3)
    best, best_score = top3[0] if top3 else (None, 0.0)
    if best is not None and best_score >= threshold:
        return best, top3
    return None, top3

# ============================================================================
# PLAN VALIDATION HELPERS
# ============================================================================

def normalize_plan_df(df: pd.DataFrame, *, stop_on_missing: bool = True):
    """Auto-detect and standardize column names for Credits, Category, Course."""
    def _pick_col(df, wanted, aliases=None):
        aliases = aliases or []
        lookup = {str(c).strip().lower(): c for c in df.columns}
        for key in [wanted.lower(), *[a.lower() for a in aliases]]:
            if key in lookup:
                return lookup[key]
        return None

    df = df.copy()
    df.rename(columns=lambda c: str(c).strip(), inplace=True)

    cat_col = _pick_col(df, "Category", ["Core Category", "Cat", "Area", "Type", "Requirement"])
    credits_col = _pick_col(df, "Credits", ["Credit", "Credit Hours", "Hours", "Cr", "Units"])
    course_col = _pick_col(df, "Course", ["Course ID", "CourseID", "Course Code", "Subject+Number"])

    missing = []
    if credits_col is None:
        missing.append("Credits (or Credit Hours/Hours/Cr/Units)")
    if cat_col is None:
        missing.append("Category (or Core Category/Area/Type)")
    
    if missing and stop_on_missing:
        st.error(f"CSV missing required columns: {', '.join(missing)}. Found: {list(df.columns)}")
        st.stop()

    rename_map = {}
    if credits_col and credits_col != "Credits":
        rename_map[credits_col] = "Credits"
    if cat_col and cat_col != "Category":
        rename_map[cat_col] = "Category"
    if course_col and course_col != "Course":
        rename_map[course_col] = "Course"
    
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    if "Credits" in df.columns:
        df["Credits"] = pd.to_numeric(df["Credits"], errors="coerce").fillna(0)

    return df, {"Category": cat_col, "Credits": credits_col, "Course": course_col}

def _safe_read_csv(path: Path) -> Optional[pd.DataFrame]:
    """Safely load CSV, return None on error."""
    try:
        return pd.read_csv(path)
    except Exception:
        return None

def check_requirements(df: pd.DataFrame, program: str, catalog_year: str) -> dict:
    """Basic validation: check for missing data, low credit totals, unknown categories."""
    issues = []
    cols = {c.lower(): c for c in df.columns}
    cat_col = cols.get("category")
    cr_col = cols.get("credits")

    if not cat_col:
        issues.append({"type": "Missing column", "course": "(n/a)", "details": "CSV missing 'Category' column"})
    if not cr_col:
        issues.append({"type": "Missing column", "course": "(n/a)", "details": "CSV missing 'Credits' column"})

    if cat_col and cr_col:
        for i, row in df.iterrows():
            if pd.isna(row[cat_col]) or str(row[cat_col]).strip() == "":
                issues.append({"type": "Blank category", "course": str(row.get("Course", f"row {i+1}")), "details": "Category is empty"})
            try:
                float(row[cr_col])
            except Exception:
                issues.append({"type": "Bad credits", "course": str(row.get("Course", f"row {i+1}")), "details": f"Credits '{row[cr_col]}' not numeric"})

        try:
            total = float(pd.to_numeric(df[cr_col], errors="coerce").fillna(0).sum())
            if total < 12:
                issues.append({"type": "Low load", "course": "(overall)", "details": f"Total credits {total:.1f} < 12"})
        except Exception:
            pass

    return {"issues": issues, "summary": {"program": program, "catalog_year": catalog_year}}

# ============================================================================
# MAIN APP
# ============================================================================

apply_theme(page_title="Advisor Assistant — Full Bundle", page_icon="💗", layout="wide")

BASE = Path(__file__).parent
CORE_MAP_PATH = BASE / "app" / "core_map_simplified.csv"
POLICIES_PATH = BASE / "app" / "policies_simplified.csv"
CONTACTS_PATH = BASE / "app" / "contacts.csv"

FAQ_ROWS = faq_corpus(BASE)

core_map_df = _safe_read_csv(CORE_MAP_PATH)
policies_df = _safe_read_csv(POLICIES_PATH)
contacts_df = _safe_read_csv(CONTACTS_PATH)

# ============================================================================
# HEADER
# ============================================================================

st.title("Advisor Assistant — Full Bundle")
st.caption("Built in Streamlit • Local Demo")
st.caption("Plan check, policies, and resources in one place.")

with st.container():
    st.subheader("Session Overview")
    st.write(f"**Logged in as:** Haley (Advisor 1) | Session active")
    st.write(f"**Date:** {datetime.now().strftime('%B %d, %Y  %I:%M %p')}")
    st.caption("Tip: Use the sample plan toggle if you don't have a CSV yet.")

st.divider()

# ============================================================================
# SIDEBAR: FAQ & FILE UPLOADS
# ============================================================================

st.sidebar.title("FAQ Assistant")
st.sidebar.caption("SLU • Doisy College")
st.sidebar.caption("Ask questions like "How do I drop a class?" or "When can I register?"")

program = st.sidebar.selectbox("Program", ["Physical Therapy", "Occupational Therapy", "Athletic Training", "Nutrition & Dietetics", "Other"], index=0)
catalog_year = st.sidebar.selectbox("Catalog Year", ["2025-2026", "2024-2025", "2023-2024", "Other"], index=0)

st.sidebar.subheader("Upload Files")
plan_file = st.sidebar.file_uploader("Student Plan CSV", type=["csv"], key="plan")
catalog_file = st.sidebar.file_uploader("Catalog CSV (optional)", type=["csv"], key="catalog")
req_totals_file = st.sidebar.file_uploader("Category Requirements CSV (optional)", type=["csv"], key="reqtot")

st.sidebar.markdown("---")
st.sidebar.subheader("FAQ Assistant")

if "faq_chat" not in st.session_state:
    st.session_state.faq_chat = []

faq_q = st.sidebar.text_input("Ask a question", placeholder="ex: when can I register?")
ask = st.sidebar.button("Ask")

if ask and faq_q.strip():
    q = faq_q.strip()
    st.session_state.faq_chat.append({"role": "user", "text": q})
    hit, top3 = faq_answer(q, FAQ_ROWS)

    if hit:
        st.sidebar.success("Found a match")
        st.sidebar.write(f"**Answer:** {hit['a']}")
        st.session_state.faq_chat.append({"role": "bot", "text": hit["a"]})
        st.sidebar.caption(f"Matched FAQ: "{hit['q']}"")
    else:
        st.sidebar.warning("No exact match. Did you mean:")
        for row, score in top3:
            st.sidebar.write(f"- **{row['q']}**")
        st.session_state.faq_chat.append({"role": "bot", "text": "No exact match. Try one of the suggested questions or rephrase."})

for msg in st.session_state.faq_chat[-6:]:
    prefix = "🧑‍💻" if msg["role"] == "user" else "🤖"
    st.sidebar.write(f"{prefix} {msg['text']}")

if not FAQ_ROWS:
    st.sidebar.caption("Add app/faq.csv with columns: Question, Answer[, Tags]")

# Sample plan toggle
if st.sidebar.toggle("Use sample plan", value=False):
    plan_file = StringIO(
        "CourseID,Title,Credits,Category,Days,Start,End,Term,Status\n"
        "ANAT 1000,Intro Anatomy,3,Core,MWF,09:00,09:50,Fall 2025,Completed\n"
        "MATH 1200,Statistics,3,Core,TR,10:00,11:15,Fall 2025,Completed\n"
        "BIO 1060,Biology,3,Core,MWF,11:00,11:50,Spring 2026,Completed\n"
        "BIO 1065,Biology Lab,1,Lab,W,13:00,14:50,Spring 2026,Completed\n"
        "PSY 1010,Behavioral Sci,3,Core,TR,12:00,13:15,Spring 2026,Completed\n"
        "DPT 2213,Movement Science,4,Core,MWF,09:00,10:40,Fall 2026,Planned\n"
        "IPE 4200,IP Seminar,1,IP,T,14:00,15:15,Fall 2026,Planned\n"
    )

# ============================================================================
# LOAD PLAN DATA
# ============================================================================

plan_df = None
if plan_file is not None:
    try:
        plan_df = pd.read_csv(plan_file)
        plan_df, resolved_cols = normalize_plan_df(plan_df, stop_on_missing=True)
    except Exception as e:
        st.error(f"Error loading plan: {e}")

# ============================================================================
# DATASET SUMMARY
# ============================================================================

courses_rows = plan_df.shape[0] if plan_df is not None else 0
catalog_rows = 0
req_rows = 0
contact_rows = contacts_df.shape[0] if contacts_df is not None else 0

with st.container():
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Courses loaded", f"{courses_rows}")
    m2.metric("Catalog entries", f"{catalog_rows}")
    m3.metric("Req categories", f"{req_rows}")
    m4.metric("Contacts", f"{contact_rows}")

# ============================================================================
# PLAN PREVIEW
# ============================================================================

st.divider()
st.subheader("Plan Preview & Overview")

if plan_df is not None and not plan_df.empty:
    st.dataframe(plan_df.head(25), use_container_width=True)

    total_credits = float(pd.to_numeric(plan_df.get("Credits", 0), errors="coerce").fillna(0).sum())
    status_s = plan_df.get("Status", None)
    planned = int((status_s == "Planned").sum()) if status_s is not None else 0
    completed = int((status_s == "Completed").sum()) if status_s is not None else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total credits", f"{total_credits:.1f}")
    col2.metric("Completed courses", f"{completed}")
    col3.metric("Planned courses", f"{planned}")
else:
    st.info("Upload a Student Plan CSV to begin (needs at least: Credits, Category).")

# ============================================================================
# PLAN VALIDATION
# ============================================================================

st.divider()
st.subheader("Plan Validation")

if plan_df is None or plan_df.empty:
    st.info("Upload a Student Plan CSV to run validation.")
else:
    st.caption("Click 'Validate schedule' to check for missing data and low credit totals.")
    validate_clicked = st.button("Validate schedule")
    
    if validate_clicked:
        result = check_requirements(plan_df, program, catalog_year)
        issues = result["issues"]

        if issues:
            st.error(f"{len(issues)} issue(s) found.")
            issues_df = pd.DataFrame(issues)
            st.dataframe(issues_df, use_container_width=True)

            st.download_button(
                label="Download issues (.csv)",
                data=issues_df.to_csv(index=False).encode("utf-8"),
                file_name="validation_issues.csv",
                mime="text/csv",
            )
        else:
            st.success("All checks passed! Your student plan meets basic requirements.")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        note_lines = [
            f"Advisor Assistant validation note ({timestamp})",
            f"Program: {program} | Catalog: {catalog_year}",
            f"Issue count: {len(issues)}",
            "-" * 40,
        ]
        if issues:
            for i, it in enumerate(issues, 1):
                note_lines.append(f"{i}. {it.get('type','?')} — {it.get('course','?')}: {it.get('details','')}")
        else:
            note_lines.append("No issues detected.")
        
        notes_text = "\n".join(note_lines)
        st.session_state["validation_notes"] = notes_text

        st.download_button(
            label="Download advisor note (.txt)",
            data=notes_text.encode("utf-8"),
            file_name="advisor_note.txt",
            mime="text/plain",
        )

# ============================================================================
# ADVISOR NOTES & EXPORT
# ============================================================================

st.divider()
st.subheader("Advisor Notes & Export")

notes_input = st.text_area(
    "Advisor notes",
    value=st.session_state.get("advisor_notes", ""),
    placeholder="Type advisor notes here…",
    height=150,
)
st.session_state["advisor_notes"] = notes_input

if notes_input.strip():
    st.download_button(
        label="Download notes (.txt)",
        data=notes_input.encode("utf-8"),
        file_name="advisor_notes.txt",
        mime="text/plain",
    )

full_report_parts = []
if "validation_notes" in st.session_state:
    full_report_parts.append(st.session_state["validation_notes"])
if "advisor_notes" in st.session_state and st.session_state["advisor_notes"].strip():
    full_report_parts.append("Advisor Notes:\n" + st.session_state["advisor_notes"].strip())

if full_report_parts:
    combined_report = "\n\n".join(full_report_parts)
    st.download_button(
        label="Download full report (.txt)",
        data=combined_report.encode("utf-8"),
        file_name="advisor_full_report.txt",
        mime="text/plain",
    )
else:
    st.info("No notes or validation results to export yet.")

# ============================================================================
# ADDITIONAL INFORMATION
# ============================================================================

st.divider()
st.subheader("Additional Information")

with st.expander("Policies"):
    if policies_df is not None and not policies_df.empty:
        st.write("University or program policies relevant to advising:")
        st.dataframe(policies_df, use_container_width=True)
    else:
        st.info(f"No policy data found at `{POLICIES_PATH.as_posix()}`.")

with st.expander("Contacts & Resources"):
    st.write("Key contacts from the student handbook:")
    if contacts_df is not None and not contacts_df.empty:
        st.dataframe(contacts_df, use_container_width=True)
    else:
        st.info(f"No contacts found at `{CONTACTS_PATH.as_posix()}`.")

st.caption("© 2025 Advisor Assistant | Haley Mierzejewski")
