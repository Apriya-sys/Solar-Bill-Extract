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
# SIDEBAR
# -------------------------------------------------

with st.sidebar:

    st.markdown("---")

    st.subheader("⚙️ AI Settings")

    groq_key = st.text_input(
        "Groq API Key",
        type="password"
    )

    mistral_key = st.text_input(
        "Mistral API Key",
        type="password"
    )
    if not groq_key:
        groq_key = st.secrets.get("GROQ_API_KEY", "")

# -------------------------------------------------
# FIELDS
# -------------------------------------------------

FIELDS = [
    "consumer_name",
    "consumer_number",
    "meter_number",
    "contract_demand",
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

    if not groq_key or not mistral_key:

        st.error(
            "Please enter both Groq and Mistral API Keys"
        )

        st.stop()

    process_btn = st.button(
        "🚀 Extract Data",
        use_container_width=True
    )

    if process_btn:

        os.makedirs(
            "assets",
            exist_ok=True
        )

        all_data = []

        # -------------------------------------------------
        # PROCESS FILES
        # -------------------------------------------------

        for uploaded_file in uploaded_files:

            with open(
                uploaded_file.name,
                "wb"
            ) as f:

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
                f"Extracting data ({uploaded_file.name})..."
            ):

                data = extract_bill_data(
                file_path,
                mistral_api_key=mistral_key,
                groq_api_key=groq_key
           )

                all_data.append(data)

            # -------------------------------------------------
            # ERROR
            # -------------------------------------------------

            if "error" in data:

                st.error(
                    data["error"]
                )

                continue

            # -------------------------------------------------
            # HEADER
            # -------------------------------------------------

            st.markdown(
                f"## 📄 {uploaded_file.name}"
            )

            # -------------------------------------------------
            # JSON VIEW
            # -------------------------------------------------

            with st.expander(
                "🔍 View Extracted JSON"
            ):

                st.json(data)

            # -------------------------------------------------
            # DISPLAY FIELDS
            # -------------------------------------------------

            col1, col2 = st.columns(2)

            left_fields = FIELDS[:7]

            right_fields = FIELDS[7:]

            with col1:

                for key in left_fields:

                    st.markdown(
                        f"**{key}:** `{data.get(key, '')}`"
                    )

            with col2:

                for key in right_fields:

                    st.markdown(
                        f"**{key}:** `{data.get(key, '')}`"
                    )

            # -------------------------------------------------
            # MONTH HISTORY
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