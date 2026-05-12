import streamlit as st
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from extract_bill import extract_bill_data
from fill_excel import fill_excel_multi


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="Solar Load Calculator",
    page_icon="⚡",
    layout="wide"
)

# -------------------------------------------------
# TITLE
# -------------------------------------------------

st.title("⚡ Solar Load Calculator")

st.markdown("### MSEDCL Bill Extractor")

st.write(
    "Upload one or more electricity bill images to extract all data."
)

# -------------------------------------------------
# FILE UPLOAD
# -------------------------------------------------

uploaded_files = st.file_uploader(
    "Choose Bill Image(s)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

# -------------------------------------------------
# FIELDS
# -------------------------------------------------

FIELDS = [
    "consumer_number",
    "consumer_name",
    "address",
    "meter_number",
    "load_kw",
    "tariff",
    "bill_date",
    "due_date",
    "current_reading",
    "previous_reading",
    "units",
    "bill_amount",
    "late_amount",
]

# -------------------------------------------------
# MAIN
# -------------------------------------------------

if uploaded_files:

    os.makedirs("assets", exist_ok=True)

    # -------------------------------------------------
    # SIDEBAR
    # -------------------------------------------------

    st.sidebar.markdown("---")

    st.sidebar.subheader(
        "🤖 AI Ensemble Settings"
    )

    use_ai = st.sidebar.toggle(
        "Enable AI Ensemble (Mistral + Llama)",
        value=True
    )

    # Optional Manual API Keys
    mistral_key = st.sidebar.text_input(
        "Mistral API Key",
        type="password",
        help="Optional if already added in Streamlit secrets"
    )

    groq_key = st.sidebar.text_input(
        "Groq API Key",
        type="password",
        help="Optional if already added in Streamlit secrets"
    )

    # -------------------------------------------------
    # STREAMLIT SECRETS SUPPORT
    # -------------------------------------------------

    try:

        default_mistral = st.secrets[
            "MISTRAL_API_KEY"
        ]

        default_groq = st.secrets[
            "GROQ_API_KEY"
        ]

    except:

        default_mistral = None
        default_groq = None

    # -------------------------------------------------
    # FINAL KEYS
    # -------------------------------------------------

    final_mistral_key = (
        mistral_key
        or default_mistral
    )

    final_groq_key = (
        groq_key
        or default_groq
    )

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------

    if use_ai and (
        not final_mistral_key
        or not final_groq_key
    ):

        st.sidebar.error(
            "⚠️ Missing API Keys.\n\n"
            "Add them manually OR use Streamlit secrets."
        )

        st.stop()

    # -------------------------------------------------
    # STORE ALL DATA
    # -------------------------------------------------

    all_data = []

    # -------------------------------------------------
    # PROCESS FILES
    # -------------------------------------------------

    for uploaded_file in uploaded_files:

        # Save Uploaded File
        with open(uploaded_file.name, "wb") as f:

            f.write(
                uploaded_file.getbuffer()
            )

        file_path = os.path.abspath(
            uploaded_file.name
        )

        st.success(
            f"✅ Uploaded: {uploaded_file.name}"
        )

        # -------------------------------------------------
        # EXTRACTION
        # -------------------------------------------------

        with st.spinner(
            f"Extracting data using AI Ensemble ({uploaded_file.name})..."
        ):

            data = extract_bill_data(
                file_path,
                mistral_api_key=final_mistral_key,
                groq_api_key=final_groq_key
            )

            all_data.append(data)

        # -------------------------------------------------
        # SHOW ERRORS
        # -------------------------------------------------

        if "error" in data:

            st.error(data["error"])

            continue

        # -------------------------------------------------
        # FILE HEADER
        # -------------------------------------------------

        st.markdown(
            f"## 📄 {uploaded_file.name}"
        )

        # -------------------------------------------------
        # DEBUG JSON VIEW
        # -------------------------------------------------

        with st.expander(
            "🔍 View Extracted JSON"
        ):

            st.json(data)

        # -------------------------------------------------
        # COLUMNS
        # -------------------------------------------------

        col1, col2 = st.columns(2)

        left_fields = FIELDS[:7]

        right_fields = FIELDS[7:]

        # -------------------------------------------------
        # LEFT SIDE
        # -------------------------------------------------

        with col1:

            for key in left_fields:

                val = data.get(key, "")

                if (
                    key == "consumer_number"
                    and not data.get(
                        "valid_consumer",
                        True
                    )
                ):

                    st.error(
                        f"**{key}:** `{val}` (Invalid Format)"
                    )

                else:

                    st.markdown(
                        f"**{key}:** `{val}`"
                    )

        # -------------------------------------------------
        # RIGHT SIDE
        # -------------------------------------------------

        with col2:

            for key in right_fields:

                val = data.get(key, "")

                if (
                    key == "units"
                    and not data.get(
                        "valid_units",
                        True
                    )
                ):

                    st.warning(
                        f"**{key}:** `{val}` (Unit Mismatch)"
                    )

                elif (
                    key == "late_amount"
                    and not data.get(
                        "valid_amounts",
                        True
                    )
                ):

                    st.warning(
                        f"**{key}:** `{val}` (Amount Mismatch)"
                    )

                else:

                    st.markdown(
                        f"**{key}:** `{val}`"
                    )

        # -------------------------------------------------
        # MONTHLY HISTORY
        # -------------------------------------------------

        monthly_history = data.get(
            "monthly_history",
            []
        )

        if monthly_history:

            st.markdown(
                "### 📊 Monthly Usage History"
            )

            for item in monthly_history:

                st.write(
                    f"{item['month']} : {item['units']} Units"
                )

        else:

            st.warning(
                "No monthly history extracted."
            )

        st.divider()

    # -------------------------------------------------
    # FINAL REPORT
    # -------------------------------------------------

    if all_data:

        st.markdown("---")

        st.subheader("📊 Final Report")

        output_file = fill_excel_multi(
            all_data
        )

        st.success(
            f"✅ Data extracted from {len(all_data)} bill(s)."
        )

        # -------------------------------------------------
        # DOWNLOAD
        # -------------------------------------------------

        with open(output_file, "rb") as f:

            st.download_button(
                label="📥 Download Excel File",
                data=f,
                file_name=os.path.basename(
                    output_file
                ),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )