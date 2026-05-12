def validate_units(current, previous, units):
    try:
        cur = float(current)
        prev = float(previous)
        u = float(units)
        return abs((cur - prev) - u) < 0.01
    except:
        return False

def validate_amounts(bill_amount, late_amount):
    try:
        ba = float(bill_amount)
        la = float(late_amount)
        return la >= ba
    except:
        return False

def validate_consumer_number(consumer_number):
    if not consumer_number:
        return False
    return consumer_number.startswith("43") and len(consumer_number) == 12

def clean_data(data):
    """
    Cleans and formats extracted data.
    """
    # Example: ensuring strings are stripped
    for key in data:
        if isinstance(data[key], str):
            data[key] = data[key].strip()
    return data
