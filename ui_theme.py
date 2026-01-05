import streamlit as st


def apply_theme(page_title: str = "Advisor Assistant", page_icon: str = "💗", layout: str = "wide") -> None:
    """Apply custom styling to the Streamlit app.

    Configures page metadata and injects CSS for a cohesive purple/lilac
    color scheme with rounded corners and subtle shadows. Uses Montserrat
    font for readability.

    Args:
        page_title: Text shown in browser tab.
        page_icon: Emoji favicon.
        layout: Streamlit layout mode ("wide" or "centered").
    """
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
            :root {
                --aa-bg: #f7f7fb;          /* Light background */
                --aa-card: #ffffff;        /* Card containers */
                --aa-muted: #e7e3f5;       /* Subtle lilac highlights */
                --aa-text: #27215b;        /* Dark navy text */
                --aa-accent: #6c5dd1;      /* Primary purple */
                --aa-accent-2: #5848a3;    /* Hover state */
                --aa-border: #ded9ec;      /* Borders */
                --aa-radius: 12px;         /* Corner radius */
                --aa-shadow: 0 2px 12px rgba(0,0,0,0.05);
            }

            .stApp {
                background: var(--aa-bg);
                color: var(--aa-text);
                font-family: 'Montserrat', 'Segoe UI', sans-serif;
            }

            h1, h2, h3, h4, h5, h6 {
                color: var(--aa-text);
                font-family: 'Montserrat', 'Segoe UI', sans-serif;
                letter-spacing: 0.2px;
            }

            /* Buttons */
            div.stButton > button,
            .stDownloadButton button {
                background: var(--aa-accent) !important;
                color: #ffffff !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 0.45rem 0.9rem !important;
                font-weight: 600 !important;
            }
            div.stButton > button:hover,
            .stDownloadButton button:hover {
                background: var(--aa-accent-2) !important;
            }

            /* Form inputs */
            .stTextInput input,
            .stTextArea textarea,
            .stSelectbox div[data-baseweb="select"] > div,
            .stDateInput input {
                background: #ffffff;
                border: 1px solid var(--aa-border);
                border-radius: 6px;
                padding: 0.4rem 0.6rem;
            }
            .stTextInput input:focus,
            .stTextArea textarea:focus {
                border-color: var(--aa-accent);
                outline: 2px solid var(--aa-accent);
            }

            /* DataFrames */
            .stDataFrame div[data-testid="stTable"] table {
                border-collapse: separate;
                border-spacing: 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
