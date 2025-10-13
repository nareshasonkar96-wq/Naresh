#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mobile_number_variant.py
----------------------------------
- Reads XML text
- Maps all real mobile numbers inside:
    • address="..."  (only if ends with 10 digits)
    • service_center="..."
    • body="..."
- Normalizes formats so +91/91/0/plain are treated as the same number
- Skips alphanumeric sender IDs like VM-HDFCBK, CP-UDDDST, etc.
- Returns updated XML text and mapping dictionary
- Prints summary and logs detailed mapping to a text file
"""

import re, random, os

def apply_mobile_number_variant(xml_text: str, seed: int = None, verbose: bool = True):
    rng = random.Random(seed or random.randint(1000, 999999))
    phone_map = {}
    replacement_count = 0
    skipped_senders = 0
    log_entries = []   # store for file output

    # --- normalize number for comparison ---
    def normalize(num: str) -> str:
        num = num.strip()
        num = re.sub(r'^(?:\+91|91|0)', '', num)  # remove +91 / 91 / 0 prefix
        return num

    # --- main mapping function ---
    def map_number(old_num, tag=""):
        nonlocal replacement_count, skipped_senders

        # ✅ Only process if it ends with 10 digits (real mobile)
        if not re.search(r'([6-9]\d{9})$', old_num.strip()):
            skipped_senders += 1
            return old_num  # Skip alphanumeric or short sender IDs

        norm = normalize(old_num)
        if norm in phone_map:
            new_core = phone_map[norm]
        else:
            new_core = str(rng.randint(7000000000, 9999999999))
            phone_map[norm] = new_core

        replacement_count += 1

        # preserve prefix style or sender prefix
        if old_num.startswith("+91"):
            new_num = "+91" + new_core
        elif old_num.startswith("91"):
            new_num = "91" + new_core
        elif old_num.startswith("0"):
            new_num = "0" + new_core
        else:
            # keep prefix part if it has letters or dashes before the digits
            prefix_match = re.match(r'^(.*?)([6-9]\d{9})$', old_num)
            if prefix_match and prefix_match.group(1):
                new_num = prefix_match.group(1) + new_core
            else:
                new_num = new_core

        if tag:
            log_entries.append(f"{tag}: {old_num} → {new_num}")

        return new_num

    # --- Replace inside address attribute ---
    xml_text = re.sub(
        r'address="([^"]+)"',
        lambda m: f'address="{map_number(m.group(1), "address")}"',
        xml_text,
    )

    # --- Replace inside service_center attribute ---
    xml_text = re.sub(
        r'service_center="([^"]+)"',
        lambda m: f'service_center="{map_number(m.group(1), "service_center")}"',
        xml_text,
    )

    # --- Replace mobile numbers inside body ---
    def replace_body_numbers(match):
        body_text = match.group(1)

        def repl(m):
            return map_number(m.group(0), "body")

        body_text = re.sub(r'\+91[6-9]\d{9}\b', repl, body_text)
        body_text = re.sub(r'\b91[6-9]\d{9}\b', repl, body_text)
        body_text = re.sub(r'\b0[6-9]\d{9}\b', repl, body_text)
        body_text = re.sub(r'(?<!\d)[6-9]\d{9}(?!\d)', repl, body_text)

        return f'body="{body_text}"'

    xml_text = re.sub(r'body="(.*?)"', replace_body_numbers, xml_text, flags=re.DOTALL)

    # --- Summary print ---
    if verbose:
        print(f"📱 {len(phone_map)} unique mobile numbers mapped ({replacement_count} total replacements)")
        print(f"🚫 {skipped_senders} non-mobile sender IDs skipped")

    # --- Write mapping log file ---
    log_path = os.path.join(os.getcwd(), "mobile_number_mapping.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("MOBILE NUMBER MAPPING LOG\n")
        f.write("=========================\n\n")
        for entry in log_entries:
            f.write(entry + "\n")
        f.write(f"\nTotal unique numbers: {len(phone_map)}\n")
        f.write(f"Total replacements: {replacement_count}\n")
        f.write(f"Skipped non-mobile sender IDs: {skipped_senders}\n")

    if verbose:
        print(f"📝 Mapping log saved to: {log_path}")

    return xml_text, phone_map


# ===== Example test run =====
if __name__ == "__main__":
    sample = '''<sms address="CP-UDDDST"
        body="Payment sent to 9876543210, received from 0919876543210, and confirmed with 919876543210."
        service_center="+919812345678"/>
<sms address="AD-9876543210" />
<sms address="VM-HDFCBK" />'''

    out, mapping = apply_mobile_number_variant(sample)
    print("\nUpdated XML:\n", out)
    print("\nMapping:\n", mapping)
