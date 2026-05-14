import os

from ensemble_extractor import extract_with_ensemble

from validations import (
    validate_units,
    validate_amounts,
    validate_consumer_number
)


def extract_bill_data(
    image_path,
    mistral_api_key=None,
    groq_api_key=None
):
    """
    Orchestrates bill extraction using:

    1. Mistral Vision
    2. Llama Vision
    3. Compare + Merge

    Returns exact extracted bill values.
    """

    print(
        f"--- Starting Ensemble AI Extraction for {image_path} ---"
    )

    # =====================================================
    # ENSEMBLE EXTRACTION
    # =====================================================

    data = extract_with_ensemble(
        image_path,
        mistral_key=mistral_api_key,
        groq_key=groq_api_key
    )

    # =====================================================
    # ERROR CHECK
    # =====================================================

    if "error" in data:

        return data

    # =====================================================
    # VALIDATIONS ONLY
    # =====================================================

    data["valid_units"] = validate_units(
        data.get("current_reading"),
        data.get("previous_reading"),
        data.get("units")
    )

    data["valid_amounts"] = validate_amounts(
        data.get("bill_amount"),
        data.get("late_amount")
    )

    data["valid_consumer"] = validate_consumer_number(
        data.get("consumer_number")
    )

    # =====================================================
    # PRINT RESULT
    # =====================================================

    print("\n========== FINAL EXTRACTED DATA ==========\n")

    for k, v in data.items():

        if k != "monthly_history":

            print(f"{k}: {v}")

    print(
        f"monthly_history: {len(data.get('monthly_history', []))} items"
    )

    print(
        "────────────────────────────────────────────\n"
    )

    return data