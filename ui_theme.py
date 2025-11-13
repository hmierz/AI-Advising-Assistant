import streamlit as st


def apply_theme(page_title: str = "Advisor Assistant", page_icon: str = "💗", layout: str = "wide") -> None:
    """Apply a cohesive, modern theme to the Streamlit app.

    Args:
        page_title: The text shown in the browser tab.
        page_icon: The favicon emoji.
        layout: The Streamlit layout mode (e.g., "wide").

    This function configures the page and injects custom CSS to
    standardize colors, typography and component appearance across
    the application. The palette favors muted lilac and deep purple
    tones on a light background, paired with the Montserrat font for
    clean readability.
    """
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state="expanded",
    )

    # Define CSS variables and component styles. Using CSS variables
    # makes it easy to adjust the overall palette in one place.
    st.markdown(
        """
        <style>
            :root {
                /* Base colors */
                --aa-bg: #f7f7fb;          /* Off‑white page background */
                --aa-card: #ffffff;        /* Card and container backgrounds */
                --aa-muted: #e7e3f5;       /* Muted lilac for subtle highlights */
                --aa-text: #27215b;        /* Dark navy text */
                --aa-accent: #6c5dd1;      /* Primary purple accent */
                --aa-accent-2: #5848a3;    /* Secondary accent for hover */
                --aa-border: #ded9ec;      /* Soft border color */
                --aa-radius: 12px;         /* Corner radius for components */
                --aa-shadow: 0 2px 12px rgba(0,0,0,0.05); /* Subtle card shadow */
            }

            /* Base application styles */
            .stApp {
                background: var(--aa-bg);
                color: var(--aa-text);
                font-family: 'Montserrat', 'Segoe UI', sans-serif;
            }

            /* Headings adopt the primary text color and spacing */
            h1, h2, h3, h4, h5, h6 {
                color: var(--aa-text);
                font-family: 'Montserrat', 'Segoe UI', sans-serif;
                letter-spacing: 0.2px;
                margin-bottom: 0.5rem;
            }

            /* Buttons: consistent shape, colors and hover states */
            div.stButton > button,
            .stDownloadButton button,
            .stDownloadButton button:hover,
            .stDownloadButton button:focus {
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

            /* Form inputs: unify look and feel */
            .stTextInput input,
            .stTextArea textarea,
            .stSelectbox div[data-baseweb="select"] > div,
            .stDateInput input {
                background: #ffffff;
                border: 1px solid var(--aa-border);
                border-radius: 6px;
                padding: 0.4rem 0.6rem;
                box-shadow: none;
            }
            .stTextInput input:focus,
            .stTextArea textarea:focus,
            .stDateInput input:focus {
                border-color: var(--aa-accent);
                outline: 2px solid var(--aa-accent);
            }

            /* DataFrame tables: remove default grid lines for cleaner look */
            .stDataFrame div[data-testid="stTable"] table {
                border-collapse: separate;
                border-spacing: 0;
            }

            /* Generic block spacing */
            .stBlock {
                margin-bottom: 1.25rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
