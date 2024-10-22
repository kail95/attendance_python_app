import re

def generate_registration_number(email: str) -> str:
    email = email.lower()  # Make it case-insensitive

    # Pattern 1: ag18031@agri.pdn.ac.lk => AG/18/031
    match_1 = re.match(r"ag(\d{2})(\d{3})@agri\.pdn\.ac\.lk", email)
    if match_1:
        return f"AG/{match_1.group(1)}/{match_1.group(2)}"

    # Pattern 2: asf18025@agri.pdn.ac.lk => AG/18/ASF/025
    match_2 = re.match(r"asf(\d{2})(\d{3})@agri\.pdn\.ac\.lk", email)
    if match_2:
        return f"AG/{match_2.group(1)}/ASF/{match_2.group(2)}"

    # Pattern 3: fst18002@agri.pdn.ac.lk => AG/18/FT/002
    match_3 = re.match(r"fst(\d{2})(\d{3})@agri\.pdn\.ac\.lk", email)
    if match_3:
        return f"AG/{match_3.group(1)}/FT/{match_3.group(2)}"

    raise ValueError("Invalid email format")
