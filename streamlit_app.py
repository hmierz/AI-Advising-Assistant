from ui_theme import apply_theme
import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime
from pathlib import Path
from app import rules  # gives you rules.load_catalog, etc. if you add them later
from app.rules import check_requirements, RULES_VERSION

# ---- FAQ helpers (smarter, still no external libs) ----
from typing import List, Dict, Optional, Tuple
import re
from difflib import SequenceMatcher

_WORD_RE = re.compile(r"[A-Za-z0-9']+")

def _normalize_text(s: str) -> str:
    return " ".join(_WORD_RE.findall(str(s).lower()))

def _tokens(s: str) -> List[str]:
    return _normalize_text(s).split()

def _bigrams(tokens: List[str]) -> List[Tuple[str, str]]:
    return list(zip(tokens, tokens[1:])) if len(tokens) > 1 else []

def load_faq_csv(path: Path) -> List[Dict[str, str]]:
    try:
        import pandas as pd
        df = pd.read_csv(path)
        cols = {c.lower(): c for c in df.columns}
        qcol = cols.get("question")
        acol = cols.get("answer")
        tcol = cols.get("tags")  # optional synonyms/keywords
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
    base = [
        ("How do I find my registration time?", "Open Banner Self Service → Student → Registration → Check Registration Eligibility. You can also use the Time Ticket flyer in Policies.", "registration time,ticket,eligibility,when can I register"),
        ("What should I do if a class is full?", "Pick a back-up from your guide, monitor for opens, and contact the department for overrides.", "class full,closed,override,capacity"),
        ("Who clears my advising hold?", "Your advisor clears it after you review your guide or meet. The confirmation email means it’s clear.", "advising hold,remove hold,clear hold"),
        ("How do I withdraw from a course?", "Follow the 'Withdraw in Banner Self Service' PDF in Policies. Deadlines apply.", "withdraw,drop class,deadline"),
        ("Can you advise my minor?", "Please contact the minor’s department; see Contacts for details.", "minor advising,minor questions"),
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
    p = app_base / "app" / "faq.csv"
    rows = load_faq_csv(p)
    return rows if rows else default_faq()

def _overlap_score(q_tokens: List[str], t_tokens: List[str]) -> float:
    if not q_tokens or not t_tokens:
        return 0.0
    qs, ts = set(q_tokens), set(t_tokens)
    return len(qs & ts) / max(1, len(qs))

def _bigram_score(q_tokens: List[str], t_tokens: List[str]) -> float:
    q2 = set(_bigrams(q_tokens))
    t2 = set(_bigrams(t_tokens))
    return len(q2 & t2) / max(1, len(q2)) if q2 else 0.0

def _fuzzy_ratio(a: str, b: str) -> float:
    # 0..1
    return SequenceMatcher(None, a, b).ratio()

def _score_query(query: str, row: Dict[str, str]) -> float:
    """Score the similarity between a user query and a FAQ row.

    This function computes a weighted blend of exact word overlap,
    bigram overlap and fuzzy matching. It additionally boosts overlap
    on the FAQ row's ``tags`` column, so that synonyms and alternative
    phrasings in the CSV are more likely to match. All weights sum to 1.

    Args:
        query: The question posed by the user.
        row: A single FAQ entry with keys 'all_norm', 'tags' and 'q_norm'.

    Returns:
        A float score between 0.0 and 1.0.
    """
    qn = _normalize_text(query)
    qtok = _tokens(query)

    # Tokenize the full row text and the tags separately
    all_tok  = _tokens(row.get("all_norm", ""))
    tags_tok = _tokens(row.get("tags", ""))

    # Tunable weights: emphasize tags and exact overlaps
    w_overlap_all = 0.40
    w_overlap_tag = 0.30
    w_bigram_all  = 0.15
    w_fuzzy_q     = 0.15

    return (
        w_overlap_all * _overlap_score(qtok, all_tok)
        + w_overlap_tag * _overlap_score(qtok, tags_tok)
        + w_bigram_all  * _bigram_score(qtok, all_tok)
        + w_fuzzy_q     * _fuzzy_ratio(qn, row.get("q_norm", ""))
    )

def faq_top_matches(query: str, faqs: List[Dict[str, str]], k: int = 3) -> List[Tuple[Dict[str, str], float]]:
    scored = []
    for row in faqs:
        s = _score_query(query, row)
        scored.append((row, s))
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

# ---- Robust column normalizer (safe to paste near top) ----
def normalize_plan_df(df, *, stop_on_missing=True):
    import pandas as pd
    import streamlit as st

    def _pick_col(df, wanted, aliases=None):
        aliases = aliases or []
        lookup = {str(c).strip().lower(): c for c in df.columns}
        for key in [wanted.lower(), *[a.lower() for a in aliases]]:
            if key in lookup:
                return lookup[key]
        return None

    # Trim header whitespace
    df = df.copy()
    df.rename(columns=lambda c: str(c).strip(), inplace=True)

    # Find columns (tolerate synonyms)
    cat_col     = _pick_col(df, "Category", ["Core Category", "Cat", "Area", "Type", "Requirement"])
    credits_col = _pick_col(df, "Credits",  ["Credit", "Credit Hours", "Hours", "Cr", "Units"])
    course_col  = _pick_col(df, "Course",   ["Course ID", "CourseID", "Course Code", "Subject+Number", "Course Title", "Course Name"])

    # Friendly error if missing
    missing = []
    if credits_col is None: missing.append("Credits (or Credit Hours/Hours/Cr/Units)")
    if cat_col is None:     missing.append("Category (or Core Category/Area/Type)")
    if missing and stop_on_missing:
        st.error("Your CSV is missing required column(s): " + ", ".join(missing) + f". Found columns: {list(df.columns)}")
        st.stop()

    # Standardize names only if found
    rename_map = {}
    if credits_col and credits_col != "Credits": rename_map[credits_col] = "Credits"
    if cat_col and cat_col != "Category":        rename_map[cat_col]     = "Category"
    if course_col and course_col != "Course":    rename_map[course_col]  = "Course"
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    # Make Credits numeric if present
    if "Credits" in df.columns:
        df["Credits"] = pd.to_numeric(df["Credits"], errors="coerce").fillna(0)

    # Return df and what we resolved
    return df, {"Category": cat_col, "Credits": credits_col, "Course": course_col}


# Version string (shown in the sidebar)
RULES_VERSION = "0.1-simplified"

BASE = Path(__file__).parent
CORE_MAP_PATH   = BASE / "core_map_simplified.csv"
POLICIES_PATH   = BASE / "policies_simplified.csv"
CONTACTS_PATH   = BASE / "contacts.csv"

def _safe_read_csv(path: Path) -> pd.DataFrame | None:
    try:
        return pd.read_csv(path)
    except Exception:
        return None

def summarize_sources() -> dict:
    core_df = _safe_read_csv(CORE_MAP_PATH)
    pol_df  = _safe_read_csv(POLICIES_PATH)
    con_df  = _safe_read_csv(CONTACTS_PATH)
    return {
        "core_rows": 0 if core_df is None else len(core_df),
        "policy_rows": 0 if pol_df is None else len(pol_df),
        "contact_rows": 0 if con_df is None else len(con_df),
    }

def check_requirements(df: pd.DataFrame, program: str, catalog_year: str) -> dict:
    """
    Simplified validator:
      - checks total credits >= 12 for a term-like plan
      - flags rows with missing Category or Credits
      - if core_map exists: warns if any 'Category' not recognized
    """
    issues = []

    # Normalize column names we expect
    cols = {c.lower(): c for c in df.columns}
    cat_col = cols.get("category")
    cr_col  = cols.get("credits")

    if not cat_col:
        issues.append({"type": "Missing column", "course": "(n/a)", "details": "CSV missing 'Category' column"})
    if not cr_col:
        issues.append({"type": "Missing column", "course": "(n/a)", "details": "CSV missing 'Credits' column"})

    if cat_col and cr_col:
        # Row-level checks
        for i, row in df.iterrows():
            if pd.isna(row[cat_col]) or str(row[cat_col]).strip() == "":
                issues.append({"type": "Blank category", "course": str(row.get("Course", f"row {i+1}")), "details": "Category is empty"})
            try:
                float(row[cr_col])
            except Exception:
                issues.append({"type": "Bad credits", "course": str(row.get("Course", f"row {i+1}")), "details": f"Credits '{row[cr_col]}' is not numeric"})

        # Total credits quick sanity
        try:
            total = float(pd.to_numeric(df[cr_col], errors="coerce").fillna(0).sum())
            if total < 12:
                issues.append({"type": "Low load", "course": "(overall)", "details": f"Total credits {total:.1f} < 12"})
        except Exception:
            pass

        # Cross-check with core map if present
        core_df = _safe_read_csv(CORE_MAP_PATH)
        if core_df is not None and "Category" in core_df.columns:
            valid_cats = set(c.strip().lower() for c in core_df["Category"].dropna().astype(str))
            for i, row in df.iterrows():
                cat = str(row.get(cat_col, "")).strip().lower()
                if cat and valid_cats and cat not in valid_cats:
                    issues.append({
                        "type": "Unknown category",
                        "course": str(row.get("Course", f"row {i+1}")),
                        "details": f"'{row[cat_col]}' not found in core_map_simplified.csv"
                    })

    return {
        "issues": issues,
        "summary": {
            "program": program,
            "catalog_year": catalog_year,
            **summarize_sources()
        }
    }
# ---- Theme (pink) ----
apply_theme(page_title="Advisor Assistant — Full Bundle", page_icon="💗", layout="wide")

# ---- Import your rules module ----
try:
    import rules  # uses rules.py in project root
except Exception as e:
    rules = None

BASE = Path(__file__).parent

# Optional resources (for the Resources/Policies cards)
CORE_MAP_PATH   = BASE / "app" / "core_map_simplified.csv"    # just shown as a table if present
POLICIES_PATH   = BASE / "app" / "policies_simplified.csv"
CONTACTS_PATH   = BASE / "app" / "contacts.csv"
# FAQ corpus (from app/faq.csv if present, else defaults)
FAQ_ROWS = faq_corpus(BASE)

def load_csv_optional(p: Path):
    try:
        return pd.read_csv(p)
    except Exception:
        return None

core_map_df = load_csv_optional(CORE_MAP_PATH)
policies_df = load_csv_optional(POLICIES_PATH)
contacts_df = load_csv_optional(CONTACTS_PATH)

# -----------------------------------------------------------------------------
# Main page header and session overview
#
# The header introduces the app, then a session overview summarizes who is
# logged in and the current timestamp. A tip encourages new users to toggle
# the sample plan if they do not yet have a CSV available.

st.title("Advisor Assistant — Full Bundle")
st.caption("Built in Streamlit • Local Demo")
st.caption("Plan check, policies, and resources in one place.")

with st.container():
    st.subheader("Session Overview")
    st.write(f"**Logged in as:** Haley (Advisor 1) | Session active")
    st.write(f"**Date:** {datetime.now().strftime('%B %d, %Y  %I:%M %p')}")
    st.caption("Tip: Use the sample plan toggle if you don’t have a CSV yet.")

st.divider()

# =======================
#      SIDEBAR
# =======================
st.sidebar.title("FAQ Assistant")
st.sidebar.caption("SLU • Doisy College")
st.sidebar.caption("Ask things like “How do I drop a class?” or “When can I register?”")

program = st.sidebar.selectbox(
    "Program",
    ["Physical Therapy", "Occupational Therapy", "Athletic Training", "Nutrition & Dietetics", "Other"],
    index=0,
)
catalog_year = st.sidebar.selectbox(
    "Catalog Year",
    ["2025-2026", "2024-2025", "2023-2024", "Other"],
    index=0,
)

# Uploads
st.sidebar.subheader("Upload Files")
plan_file = st.sidebar.file_uploader("Student Plan CSV", type=["csv"], key="plan")
catalog_file = st.sidebar.file_uploader("Catalog CSV (optional)", type=["csv"], key="catalog")
req_totals_file = st.sidebar.file_uploader("Category Requirements CSV (optional)", type=["csv"], key="reqtot")

# ---- FAQ Assistant (Sidebar) ----
st.sidebar.markdown("---")
st.sidebar.subheader("FAQ Assistant")

if "faq_chat" not in st.session_state:
    st.session_state.faq_chat = []  # [{"role":"user"/"bot","text":..., "score":float, "q":str}]

faq_q = st.sidebar.text_input("Ask a question", placeholder="ex: when can I register?")
ask = st.sidebar.button("Ask")

if ask and faq_q.strip():
    q = faq_q.strip()
    st.session_state.faq_chat.append({"role": "user", "text": q})
    hit, top3 = faq_answer(q, FAQ_ROWS)

    if hit:
        st.sidebar.success("Found a match")
        st.sidebar.write(f"**Answer:** {hit['a']}")
        # keep in chat
        st.session_state.faq_chat.append({"role": "bot", "text": hit["a"]})
        # small disclosure of which Q matched
        st.sidebar.caption(f"Matched FAQ: “{hit['q']}”")
    else:
        st.sidebar.warning("I couldn’t find an exact answer. Did you mean:")
        for row, score in top3:
            st.sidebar.write(f"- **{row['q']}**")
        st.session_state.faq_chat.append({"role": "bot", "text": "No exact match. Try one of the suggested questions above or rephrase."})

# show last ~6 messages
for msg in st.session_state.faq_chat[-6:]:
    prefix = "🧑‍💻" if msg["role"] == "user" else "🤖"
    st.sidebar.write(f"{prefix} {msg['text']}")

# tiny hint
if not FAQ_ROWS:
    st.sidebar.caption("Add app/faq.csv with columns: Question, Answer[, Tags]")


# Load plan_df
plan_df = None
if plan_file is not None:
    try:
        plan_df = pd.read_csv(plan_file)
    except Exception:
        plan_file.seek(0)
        plan_df = pd.read_csv(plan_file)

# ---------- NORMALIZE & MAP COLUMNS (paste right after you load plan_df) ----------
if plan_df is not None:
    plan_df = plan_df.copy()
    plan_df.columns = [str(c).strip() for c in plan_df.columns]

    def _pick_col(df, wanted, aliases):
        lookup = {str(c).strip().lower(): c for c in df.columns}
        for key in [wanted.lower(), *[a.lower() for a in aliases]]:
            if key in lookup:
                return lookup[key]
        return None

    aliases = {
        "Category": ["Core Category", "Cat", "Area", "Type", "Requirement", "Req Area"],
        "Credits":  ["Credit", "Credit Hours", "Hours", "Cr", "Units", "Cr Hrs", "CrHrs", "Credit_Hours"],
        "Course":   ["Course ID", "CourseID", "Course Code", "Subject+Number", "Course Title", "Course Name", "Title"],
        "Status":   ["Planned/Completed", "State", "PlanStatus"],
    }

    # Try to auto-detect first
    cat_col     = _pick_col(plan_df, "Category", aliases["Category"])
    credits_col = _pick_col(plan_df, "Credits",  aliases["Credits"])
    course_col  = _pick_col(plan_df, "Course",   aliases["Course"])
    status_col  = _pick_col(plan_df, "Status",   aliases["Status"])

    # Sidebar mapping if missing
    with st.sidebar.expander("Map your CSV columns (use if headers differ)"):
        cols = list(plan_df.columns)
        if credits_col is None:
            credits_col = st.selectbox("Which column is Credits?", [None] + cols, index=0)
        if cat_col is None:
            cat_col = st.selectbox("Which column is Category?", [None] + cols, index=0)
        if course_col is None and "Course" not in plan_df.columns:
            course_col = st.selectbox("Optional: Which column is Course?", [None] + cols, index=0)
        if status_col is None and "Status" not in plan_df.columns:
            status_col = st.selectbox("Optional: Which column is Status?", [None] + cols, index=0)

    # Apply renames for any we found/mapped
    rename_map = {}
    if credits_col and credits_col != "Credits": rename_map[credits_col] = "Credits"
    if cat_col and cat_col != "Category":        rename_map[cat_col]     = "Category"
    if course_col and course_col != "Course":    rename_map[course_col]  = "Course"
    if status_col and status_col != "Status":    rename_map[status_col]  = "Status"
    if rename_map:
        plan_df.rename(columns=rename_map, inplace=True)

    # If still missing, allow quick defaults so you can proceed
    if "Credits" not in plan_df.columns or "Category" not in plan_df.columns:
        with st.sidebar.expander("No Credits/Category in your CSV? Set quick defaults"):
            if "Credits" not in plan_df.columns:
                default_cr = st.number_input("Default Credits for all rows", min_value=0.0, max_value=30.0, value=3.0, step=0.5)
                plan_df["Credits"] = default_cr
            if "Category" not in plan_df.columns:
                default_cat = st.text_input("Default Category for all rows", value="Elective")
                plan_df["Category"] = default_cat

    # Final guard — if still missing after defaults, stop with a helpful message
    missing = [c for c in ["Credits", "Category"] if c not in plan_df.columns]
    if missing:
        st.error(f"Your CSV is missing required column(s): {', '.join(missing)}. Found columns: {list(plan_df.columns)}")
        st.stop()

    # Make Credits numeric and clean up
    plan_df["Credits"] = pd.to_numeric(plan_df["Credits"], errors="coerce").fillna(0)
# ---------- END NORMALIZE & MAP COLUMNS ----------

# Ensure Status exists so later code never KeyErrors
if plan_df is not None and "Status" not in plan_df.columns:
    plan_df["Status"] = ""  # or "Planned" if you prefer


if plan_df is not None:
    plan_df, resolved_cols = normalize_plan_df(plan_df, stop_on_missing=True)
    # Optional: see what got mapped
    # st.caption(f"Resolved → Category='{resolved_cols['Category']}', Credits='{resolved_cols['Credits']}', Course='{resolved_cols['Course']}'")


# ==== NORMALIZE COLUMNS (run only if plan_df exists) ====
if plan_df is not None:
    # --- Normalize columns so we handle synonyms like "Credit Hours", "Cr", etc. ---
    def _pick_col(df, wanted, aliases=None):
        aliases = aliases or []
        lookup = {str(c).strip().lower(): c for c in df.columns}
        for key in [wanted.lower(), *[a.lower() for a in aliases]]:
            if key in lookup:
                return lookup[key]
        return None

    # Trim header whitespace
    plan_df.rename(columns=lambda c: str(c).strip(), inplace=True)

    # Find the key columns with fallbacks
    cat_col     = _pick_col(plan_df, "Category", ["Core Category", "Cat", "Area", "Type", "Requirement"])
    credits_col = _pick_col(plan_df, "Credits",  ["Credit", "Credit Hours", "Hours", "Cr", "Units"])
    course_col  = _pick_col(plan_df, "Course",   ["Course ID", "CourseID", "Course Code", "Subject+Number", "Course Title", "Course Name"])

    # Hard-stop with a friendly message if missing
    missing = []
    if credits_col is None: missing.append("Credits (or Credit Hours/Hours/Cr/Units)")
    if cat_col is None:     missing.append("Category (or Core Category/Area/Type)")
    if missing:
        st.error("Your CSV is missing required column(s): " + ", ".join(missing) + f". Found columns: {list(plan_df.columns)}")
        st.stop()

    # Standardize column names for the rest of the app
    rename_map = {}
    if credits_col != "Credits": rename_map[credits_col] = "Credits"
    if cat_col     != "Category": rename_map[cat_col]     = "Category"
    if course_col and course_col != "Course": rename_map[course_col] = "Course"
    if rename_map:
        plan_df.rename(columns=rename_map, inplace=True)

    # Ensure Credits are numeric
    plan_df["Credits"] = pd.to_numeric(plan_df["Credits"], errors="coerce").fillna(0)



# Sample plan toggle (quick test)
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
        "Elective A,Elective,3,Elective,TR,15:30,16:45,Spring 2027,Planned\n"
        "CHEM 1080,Chemistry,3,Core,MWF,10:00,10:50,Spring 2027,Planned\n"
        "CHEM 1085,Chem Lab,1,Lab,W,12:00,13:50,Spring 2027,Planned\n"
    )

# Default catalog (if user doesn’t upload one) — minimal demo entries
default_catalog = StringIO(
    "CourseID,Title,Credits,Category,Requires,Coreqs\n"
    "ANAT 1000,Intro Anatomy,3,Core,,\n"
    "MATH 1200,Statistics,3,Core,,\n"
    "BIO 1060,Biology,3,Core,,BIO 1065\n"
    "BIO 1065,Biology Lab,1,Lab,BIO 1060,\n"
    "PSY 1010,Behavioral Sci,3,Core,,\n"
    "DPT 2213,Movement Science,4,Core,ANAT 1000;\n"
    "IPE 4200,IP Seminar,1,IP,,IPE 4900\n"
    "IPE 4900,IP Capstone,1,IP,,IPE 4200\n"
    "Elective A,Elective,3,Elective,,\n"
    "CHEM 1080,Chemistry,3,Core,,CHEM 1085\n"
    "CHEM 1085,Chem Lab,1,Lab,CHEM 1080,\n"
)

# Default req totals (if user doesn’t upload one)
default_req_totals = StringIO(
    "Category,RequiredCredits\n"
    "Core,60\n"
    "Lab,2\n"
    "IP,2\n"
    "Elective,6\n"
)


# =======================
#   LOAD/SHOW DATA
# =======================

# Catalog source
if catalog_file is not None:
    try:
        catalog_df = pd.read_csv(catalog_file)
    except Exception:
        catalog_file.seek(0)
        catalog_df = pd.read_csv(catalog_file)
else:
    default_catalog.seek(0)
    catalog_df = pd.read_csv(default_catalog)

# Req totals source
if req_totals_file is not None:
    try:
        req_totals_df = pd.read_csv(req_totals_file)
    except Exception:
        req_totals_file.seek(0)
        req_totals_df = pd.read_csv(req_totals_file)
else:
    default_req_totals.seek(0)
    req_totals_df = pd.read_csv(default_req_totals)

# -----------------------------------------------------------------------------
# Dataset summary
#
# Show how many rows are loaded from each source. This helps the user
# understand the size of their plan, catalog and requirement inputs, even
# before a plan file is uploaded. Courses loaded will be zero until a
# Student Plan CSV is uploaded or the sample plan is toggled.

courses_rows = plan_df.shape[0] if plan_df is not None else 0
catalog_rows = catalog_df.shape[0]
req_rows     = req_totals_df.shape[0]
contact_rows = contacts_df.shape[0] if contacts_df is not None else 0

with st.container():
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Courses loaded", f"{courses_rows}")
    m2.metric("Catalog entries", f"{catalog_rows}")
    m3.metric("Req categories", f"{req_rows}")
    m4.metric("Contacts", f"{contact_rows}")

# -----------------------------------------------------------------------------
# Plan preview & overview
#
# When a Student Plan CSV is loaded (or the sample plan is toggled), show a
# preview of the first 25 rows and summarise the credit load and status
# distribution. Otherwise, prompt the user to upload a CSV with the
# required columns.

st.divider()
st.subheader("Plan Preview & Overview")

if plan_df is not None and not plan_df.empty:
    # Display a preview of the plan
    st.dataframe(plan_df.head(25), use_container_width=True)

    # Summarise credits and statuses
    total_credits = float(pd.to_numeric(plan_df.get("Credits", 0), errors="coerce").fillna(0).sum())
    status_s = plan_df.get("Status", None)
    planned   = int((status_s == "Planned").sum())   if status_s is not None else 0
    completed = int((status_s == "Completed").sum()) if status_s is not None else 0

    # Show plan metrics beneath the table
    col1, col2, col3 = st.columns(3)
    col1.metric("Total credits", f"{total_credits:.1f}")
    col2.metric("Completed courses", f"{completed}")
    col3.metric("Planned courses", f"{planned}")
else:
    st.info("Upload a Student Plan CSV to begin (needs at least: CourseID, Credits, Category).")

# -----------------------------------------------------------------------------
# Plan validation
#
# This section allows users to validate their plan against prerequisites,
# corequisites, time conflicts and credit requirements. When no plan is
# loaded, a helpful message is displayed. Otherwise, the user can click a
# button to run checks. Results are displayed in a table and a summary, and
# a downloadable advisor note is generated automatically.

st.divider()
st.subheader("Plan Validation")

if plan_df is None or plan_df.empty:
    st.info("Upload a Student Plan CSV to run validation.")
else:
    st.caption("Click 'Validate schedule' to check prerequisites, corequisites, time conflicts and category credit minimums.")
    validate_clicked = st.button("Validate schedule")
    if validate_clicked:
        issues: list[dict] = []

        # Build catalog from DataFrame via your rules
        catalog: dict = {}
        if rules and hasattr(rules, "load_catalog"):
            try:
                catalog = rules.load_catalog(catalog_df)
            except Exception as e:
                st.warning(f"Catalog load failed: {e}")

        # Collect the course IDs from the plan for prereq/coreq checks
        plan_ids = [str(x) for x in plan_df.get("CourseID", pd.Series([], dtype=str)).fillna("").tolist() if str(x).strip()]

        if rules:
            # Prerequisite checks
            if hasattr(rules, "check_prereqs"):
                try:
                    issues += rules.check_prereqs(plan_ids, catalog)
                except Exception as e:
                    st.warning(f"Prereq check failed: {e}")

            # Corequisite checks
            if hasattr(rules, "check_coreqs"):
                try:
                    issues += rules.check_coreqs(plan_ids, catalog)
                except Exception as e:
                    st.warning(f"Coreq check failed: {e}")

            # Time conflict checks
            if hasattr(rules, "check_time_conflicts"):
                try:
                    issues += rules.check_time_conflicts(plan_df)
                except Exception as e:
                    st.warning(f"Time conflict check failed: {e}")

            # Category credit minimums
            if hasattr(rules, "check_category_credits"):
                try:
                    issues += rules.check_category_credits(plan_ids, catalog, req_totals_df)
                except Exception as e:
                    st.warning(f"Category credit check failed: {e}")

        # Present results to the user
        if issues:
            st.error(f"{len(issues)} issue(s) found.")
            issues_df = pd.DataFrame(issues)
            st.dataframe(issues_df, use_container_width=True)

            # Grouped summary (if your rules provide summarize_results)
            if rules and hasattr(rules, "summarize_results"):
                try:
                    buckets = rules.summarize_results(issues)
                    with st.expander("Grouped summary"):
                        for k, v in buckets.items():
                            st.write(f"**{k}**: {len(v)}")
                except Exception:
                    pass

            # Offer CSV download of issues
            st.download_button(
                label="Download issues (.csv)",
                data=issues_df.to_csv(index=False).encode("utf-8"),
                file_name="validation_issues.csv",
                mime="text/csv",
            )
        else:
            st.success("All checks passed! Your student plan meets credit and category rules.")

        # Compose an advisor note summarising the validation outcome
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        note_lines: list[str] = [
            f"Advisor Assistant validation note ({timestamp})",
            f"Program: {program} | Catalog: {catalog_year}",
            f"Issue count: {0 if not issues else len(issues)}",
            "-" * 40,
        ]
        if issues:
            for i, it in enumerate(issues, 1):
                note_lines.append(f"{i}. {it.get('type','?')} — {it.get('course','?')}: {it.get('details','')}")
        else:
            note_lines.append("No issues detected.")
        notes_text = "\n".join(note_lines)

        # Store validation notes in session state for later export
        st.session_state["validation_notes"] = notes_text

        # Provide download button for advisor note
        st.download_button(
            label="Download advisor note (.txt)",
            data=notes_text.encode("utf-8"),
            file_name="advisor_note.txt",
            mime="text/plain",
        )

# -----------------------------------------------------------------------------
# Notes & export
#
# This section provides a persistent text area for advisor notes and
# consolidated export options. Notes are saved in ``st.session_state``
# so they persist across reruns. Users can download their notes alone or
# a full report that includes validation notes and advisor notes.

st.divider()
st.subheader("Advisor Notes & Export")

# Text area for advisor notes; persists across reruns
notes_input = st.text_area(
    "Advisor notes",
    value=st.session_state.get("advisor_notes", ""),
    placeholder="Type advisor notes here…",
    height=150,
)
st.session_state["advisor_notes"] = notes_input

# Allow download of individual notes
if notes_input.strip():
    st.download_button(
        label="Download notes (.txt)",
        data=notes_input.encode("utf-8"),
        file_name="advisor_notes.txt",
        mime="text/plain",
    )

# Assemble full report from validation notes and advisor notes
full_report_parts: list[str] = []
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

# -----------------------------------------------------------------------------
# Additional information
#
# Policies, contacts and other resources are presented in expanders to
# declutter the main interface. Users can open the sections they need
# without being overwhelmed by large tables.

st.divider()
st.subheader("Additional Information")

with st.expander("Policies"):
    if policies_df is not None and not policies_df.empty:
        st.write("University or program policies relevant to advising:")
        st.dataframe(policies_df, use_container_width=True)
    else:
        st.info(f"No policy data found at `{POLICIES_PATH.as_posix()}`.")

with st.expander("Contacts & Resources"):
    st.write("Key contacts from the student handbook and other resources:")
    if contacts_df is not None and not contacts_df.empty:
        st.dataframe(contacts_df, use_container_width=True)
    else:
        st.info(f"No contacts found at `{CONTACTS_PATH.as_posix()}`.")

with st.expander("Additional Support"):
    total_contacts = contacts_df.shape[0] if contacts_df is not None else 0
    st.write(f"This application includes **{total_contacts}** contacts for further assistance.")

# Footer
st.caption("© 2025 Advisor Assistant | SLU Doisy College")

