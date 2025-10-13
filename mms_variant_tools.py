# mms_variant_tools.py
# Utilities for generating MMS-only XML variants
# Python 3.8+

import re, random
from datetime import datetime

# ======================
# Extract helpers
# ======================

def _extract_mms_blocks(xml_text: str):
    """Extract MMS blocks (<mms ...>...</mms>)"""
    return re.findall(r'(<mms\b.*?</mms>)', xml_text, flags=re.DOTALL)

def _header_footer(xml_text: str):
    """Preserve XML header/footer"""
    header_m = re.search(r'^(.*?<smses[^>]*>)', xml_text, flags=re.DOTALL)
    footer_m = re.search(r'(</smses>.*)$', xml_text, flags=re.DOTALL)
    return (header_m.group(1) if header_m else ""), (footer_m.group(1) if footer_m else "")

# ======================
# Shuffle + Shift helpers
# ======================

def _shuffle_within_days(blocks):
    """Shuffle MMS within the same day and reassign random times (01:00–23:00)."""
    if not blocks:
        return blocks

    groups = {}
    for b in blocks:
        m = re.search(r'date="(\d{10,})"', b)
        if not m:
            continue
        ts = int(m.group(1))
        dt = datetime.fromtimestamp(ts/1000)
        key = dt.strftime("%Y-%m-%d")
        groups.setdefault(key, []).append(b)

    shuffled_blocks = []
    for key, day_blocks in groups.items():
        random.shuffle(day_blocks)  # order shuffle

        start = datetime.strptime(key + " 01:00:00", "%Y-%m-%d %H:%M:%S")
        end   = datetime.strptime(key + " 23:00:00", "%Y-%m-%d %H:%M:%S")

        for b in day_blocks:
            new_dt = start + (end - start) * random.random()
            new_ts = int(new_dt.timestamp()*1000)
            b = re.sub(r'date="\d{10,}"', f'date="{new_ts}"', b)
            b = re.sub(r'date_sent="\d{10,}"', f'date_sent="{new_ts}"', b)
            shuffled_blocks.append(b)

    return shuffled_blocks

def _shift_dates_to_today(blocks):
    """Shift all MMS dates by gap between last MMS and today"""
    if not blocks:
        return blocks

    dates = []
    for b in blocks:
        m = re.search(r'date="(\d{10,})"', b)
        if m:
            dates.append(int(m.group(1)))
    if not dates:
        return blocks

    last_ts = max(dates)
    last_dt = datetime.fromtimestamp(last_ts/1000)
    now = datetime.now()

    gap_days = (now.date() - last_dt.date()).days
    if gap_days <= 0:
        return blocks

    shifted = []
    for b in blocks:
        def repl_date(m):
            old_val = int(m.group(1))
            new_val = old_val + gap_days * 24 * 3600 * 1000
            return f'date="{new_val}"'

        def repl_sent(m):
            old_val = int(m.group(1))
            new_val = old_val + gap_days * 24 * 3600 * 1000
            return f'date_sent="{new_val}"'

        nb = re.sub(r'date="(\d{10,})"', repl_date, b)
        nb = re.sub(r'date_sent="(\d{10,})"', repl_sent, nb)
        shifted.append(nb)

    # Force last MMS = now
    new_ts = int(now.timestamp() * 1000)
    last_block = shifted[-1]
    last_block = re.sub(r'date="\d{10,}"', f'date="{new_ts}"', last_block)
    last_block = re.sub(r'date_sent="\d{10,}"', f'date_sent="{new_ts}"', last_block)
    shifted[-1] = last_block

    return shifted

# ======================
# Build Variant (MMS only)
# ======================

def build_mms_variant(xml_text: str):
    """Return XML with only MMS processed (shuffle + shift)."""

    # Extract MMS blocks
    mms_blocks = _extract_mms_blocks(xml_text)

    # Shuffle & shift
    mms_blocks = _shuffle_within_days(mms_blocks)
    mms_blocks = _shift_dates_to_today(mms_blocks)

    # Sort by date
    def _sort_by_date(blocks):
        def extract_ts(b):
            m = re.search(r'date="(\d{10,})"', b)
            return int(m.group(1)) if m else 0
        return sorted(blocks, key=extract_ts)

    mms_blocks = _sort_by_date(mms_blocks)

    # Rebuild XML with only MMS
    header, footer = _header_footer(xml_text)
    count = len(mms_blocks)

    if header.strip():
        header = re.sub(r'count="\d+"', f'count="{count}"', header)
    else:
        header = f"<?xml version='1.0' encoding='utf-8'?>\n<smses count=\"{count}\">"

    if not footer.strip():
        footer = "</smses>"

    xml_out = header + "\n  " + "\n  ".join(mms_blocks) + "\n" + footer
    return xml_out 