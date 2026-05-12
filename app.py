import streamlit as st
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from extract_bill import extract_bill_data
from fill_excel import fill_excel_multi

st.set_page_config(page_title="Solar Load Calculator", page_icon="⚡", layout="wide")

st.title("⚡ Solar Load Calculator")
st.markdown("### MSEDCL Bill Extractor")
st.write("Upload one or more electricity bill images to extract all data.")

uploaded_files = st.file_uploader(
    "Choose Bill Image(s)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

FIELDS = [
    "consumer_number", "consumer_name", "address",
    "meter_number", "load_kw", "tariff",
    "bill_date", "due_date",
    "current_reading", "previous_reading", "units",
    "bill_amount", "late_amount",
]

if uploaded_files:
    os.makedirs("assets", exist_ok=True)

    all_data = []

    for uploaded_file in uploaded_files:
        file_path = os.path.join("assets", uploaded_file.name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"✅ Uploaded: {uploaded_file.name}")

        with st.spinner(f"Extracting data from {uploaded_file.name}..."):
            data = extract_bill_data(file_path)
            all_data.append(data)

        st.markdown(f"#### 📄 {uploaded_file.name}")

        col1, col2 = st.columns(2)

        left_fields  = FIELDS[:7]
        right_fields = FIELDS[7:]

        with col1:
            for key in left_fields:
                val = data.get(key, '')
                if key == "consumer_number" and not data.get("valid_consumer", True):
                    st.error(f"**{key}:** `{val}` (Invalid Format)")
                else:
                    st.markdown(f"**{key}:** `{val}`")

        with col2:
            for key in right_fields:
                val = data.get(key, '')
                if key == "units" and not data.get("valid_units", True):
                    st.warning(f"**{key}:** `{val}` (Unit Mismatch)")
                elif key == "late_amount" and not data.get("valid_amounts", True):
                    st.warning(f"**{key}:** `{val}` (Amount Mismatch)")
                else:
                    st.markdown(f"**{key}:** `{val}`")

        # -------------------------------------------------
# MONTHLY HISTORY DISPLAY 
# -------------------------------------------------

        monthly_history = data.get("monthly_history", [])

        if monthly_history:

            st.markdown("### Monthly Usage History")

            for item in monthly_history:

                st.write(
                    f"{item['month']} : {item['units']} Units"
                )

                st.divider()

            if all_data:
                output_file = fill_excel_multi(all_data)

                st.success(f"✅ Excel generated with {len(all_data)} bill(s)")

                with open(output_file, "rb") as f:
                    st.download_button(
                        label="📥 Download Excel File",
                        data=f,
                        file_name=os.path.basename(output_file),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )