# sms_variant_tools.py
# Full verbose utilities for generating SMS XML variants
# Python 3.8+

import re, random
from datetime import datetime, timedelta

# ======================
# Helpers
# ======================

def _case_like(sample: str, repl_title_case: str) -> str:
    """Match case style of sample"""
    if sample.isupper():
        return repl_title_case.upper()
    if sample.islower():
        return repl_title_case.lower()
    return repl_title_case

DEFAULT_FIRST_NAMES = [
    "Aarav","Vivaan","Aditya","Vihaan","Arjun","Reyansh","Mohit","Rohan","Ishaan","Kunal",
    "Priya","Ananya","Isha","Riya","Aditi","Shreya","Kritika","Meera","Anushka","Kavya",
    "Harsh","Sarthak","Nikhil","Siddharth","Yuvraj","Om","Dev","Krish","Dhruv","Kabir",
    "Neha","Sneha","Pooja","Tanya","Nidhi","Mansi","Ritika","Sangeeta","Tarun","Varun"
]

DEFAULT_LAST_NAMES = [
    "Sharma","Verma","Patel","Gupta","Singh","Yadav","Mehta","Kapoor","Rao","Iyer",
    "Agarwal","Jain","Chaudhary","Nair","Das","Reddy","Bose","Khan","Malhotra","Bhat"
]

DEFAULT_COMPANIES = [
    "Triveni Traders","Mahadev Industries","Shubhlaxmi Enterprises","Omkar Exim","Sunrise Infotech",
    "Kaveri Agro Tech","Aarav Global Exports","Navkar Steel & Alloys","Suryansh Impex","Vardhman Logistics",
    "Nirmal Poly Pack","Shree Laxmi Textiles","Zenith Buildcon","Kundan Food Products","Skyline Retail Pvt Ltd",
    "Orion Tech Solutions","Shree Ganesh Metals","Evergreen Enterprises","Pacific Pharma Distributors",
    "Bluewave Ecommerce","Prime Auto Spares","Vertex Engineering Works","Sai Siddhi Infra","Lotus Fashions"
]

DEFAULT_UPI_LOCALS = [
    "rohanpatel12","shreyasharma07","vishalraj9","priyanshi88",
    "meghamehta21","aaravk2000","riyakapoor3","kabirsingh11"
]

# ======================
# Core extract
# ======================

def _rand_indian_name(rng, first_names=None, last_names=None):
    first_names = first_names or DEFAULT_FIRST_NAMES
    last_names = last_names or DEFAULT_LAST_NAMES
    return f"{rng.choice(first_names)} {rng.choice(last_names)}"

def _extract_blocks(xml_text: str):
    return re.findall(r'(<sms\b[^>]*/>)', xml_text, flags=re.DOTALL)

def _extract_mms_blocks(xml_text: str):
    """Extract MMS blocks (<mms ...>...</mms>) from the XML"""
    return re.findall(r'(<mms\b.*?</mms>)', xml_text, flags=re.DOTALL)

def _header_footer(xml_text: str):
    header_m = re.search(r'^(.*?<smses[^>]*>)', xml_text, flags=re.DOTALL)
    footer_m = re.search(r'(</smses>.*)$', xml_text, flags=re.DOTALL)
    return (header_m.group(1) if header_m else ""), (footer_m.group(1) if footer_m else "")

# ======================
# Shuffle + Shift helpers
# ======================

def _shuffle_within_days(blocks):
    """Shuffle SMS within the same day and reassign random times (01:00–23:00)."""
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
    """Shift all SMS dates by exact gap between last SMS date and today"""
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

    # Force last SMS = current run time
    new_ts = int(now.timestamp() * 1000)
    last_block = shifted[-1]
    last_block = re.sub(r'date="\d{10,}"', f'date="{new_ts}"', last_block)
    last_block = re.sub(r'date_sent="\d{10,}"', f'date_sent="{new_ts}"', last_block)
    shifted[-1] = last_block

    return shifted
def _replace_to_from_names(text, rng, first_names, last_names):
    def repl(m):
        full_name = m.group(2).strip()
        parts = full_name.split()
        if len(parts) == 1:
            # single word → just replace with random first name
            return m.group(1) + " " + rng.choice(first_names).upper()
        else:
            # replace only the first word with a random first name
            new_first = rng.choice(first_names).upper()
            return m.group(1) + " " + new_first + " " + " ".join(parts[1:])
    pattern = r'\b(to|from)\s+(?!REF\s*NO\b)(?!REFNO\b)([A-Z][A-Z\s]{2,})'
    return re.sub(pattern, repl, text, flags=re.IGNORECASE)
def _final_text_fixes(text, dt=None):
    """
    Apply final cleanup fixes:
    - Ensure 'Refno' always has a space before number
    - Ensure 'Rs' and 'INR' have a space before amount
    - Sync body date formats like 06Oct23 with SMS timestamp
    """
    # --- Fix Refno spacing ---
    text = re.sub(r'(\bRefno)\s*(\d{6,})',
                  lambda m: m.group(1) + " " + m.group(2),
                  text, flags=re.IGNORECASE)

    # --- Fix Rs / INR spacing ---
    text = re.sub(r'\b(Rs\.?|INR)\s*(\d+(\.\d+)?)',
                  lambda m: m.group(1).rstrip(".") + " " + m.group(2),
                  text, flags=re.IGNORECASE)

    # --- Fix body date if dt is given ---
    if dt is not None:
        date_formats = [
            dt.strftime("%d-%m-%Y"),   # 06-10-2023
            dt.strftime("%d/%m/%Y"),   # 06/10/2023
            dt.strftime("%d%b%y"),     # 06Oct23
            dt.strftime("%d-%b-%Y"),   # 06-Oct-2023
        ]
        time_str = dt.strftime("%H:%M:%S")

        def body_repl(match):
            body_txt = match.group(1)
            body_txt = re.sub(r"\b\d{1,2}[-/][A-Za-z0-9]{2,}[-/]\d{2,4}\b", date_formats[0], body_txt)
            body_txt = re.sub(r"\b\d{1,2}[A-Za-z]{3}\d{2}\b", date_formats[2], body_txt)  # 06Oct23
            body_txt = re.sub(r"\b\d{1,2}[:]\d{2}[:]\d{2}\b", time_str, body_txt)
            return f'body="{body_txt}"'

        text = re.sub(r'body="(.*?)"', body_repl, text)

    return text

# ======================
# Build Variant
# ======================

def build_variant(xml_text: str,
                  seed: int = 12345,
                  cutoff_epoch_ms: int = None,
                  min_jitter_ms: int = 3600_000,
                  max_jitter_ms: int = 7200_000,
                  upi_locals=None,
                  first_names=None,
                  last_names=None,
                  company_names=None):
    """
    Return transformed XML per rules.
    """

    rng = random.Random(seed)
    upi_locals = list(upi_locals or DEFAULT_UPI_LOCALS)
    rng.shuffle(upi_locals)
    upi_locals = upi_locals[:rng.randint(5,8)]
    first_names = first_names or DEFAULT_FIRST_NAMES
    last_names = last_names or DEFAULT_LAST_NAMES
    company_names = company_names or DEFAULT_COMPANIES

    # Extract SMS blocks
    blocks = _extract_blocks(xml_text)

    # Step 1: shuffle within same day
    blocks = _shuffle_within_days(blocks)

    # Step 2: cutoff filter
    def _keep_block(b):
        if cutoff_epoch_ms is None:
            return True
        m = re.search(r'date="(\d{10,})"', b)
        if not m:
            return True
        ts = int(m.group(1))
        return ts <= cutoff_epoch_ms - min_jitter_ms

    kept = [b for b in blocks if _keep_block(b)]

    # Step 3: shift all SMS dates forward to today
    kept = _shift_dates_to_today(kept)

    scan_xml = "".join(kept)

    # Gather masked suffixes
    suffix3, suffix4 = set(), set()
    for mm in re.finditer(r'([Xx\*]+)(\d{3,4})', scan_xml):
        s = mm.group(2)
        (suffix3 if len(s)==3 else suffix4).add(s)

    def _build_suffix_map(suffixes, n):
        mapping, used = {}, set()
        for s in sorted(suffixes):
            while True:
                cand = "".join(str(rng.randint(0,9)) for _ in range(n))
                if cand != s and cand not in used:
                    mapping[s] = cand
                    used.add(cand)
                    break
        return mapping

    map3, map4 = _build_suffix_map(suffix3, 3), _build_suffix_map(suffix4, 4)

    # Maps & helpers
    upi_local_map = {}
    def _map_upi_local(local):
        if local not in upi_local_map:
            upi_local_map[local] = rng.choice(upi_locals)
        return upi_local_map[local]

    inside_map = {}
    def _map_core10_inside(core10):
        if core10 in inside_map: return inside_map[core10]
        new = core10[:4] + "".join(str(rng.randint(0,9)) for _ in range(6))
        inside_map[core10] = new
        return new

    used_addresses = set()
    def _gen_unique(prefix, first2):
        while True:
            rest = "".join(str(rng.randint(0,9)) for _ in range(8))
            cand = prefix + first2 + rest
            if cand not in used_addresses:
                used_addresses.add(cand); return cand



  

    # ======================
    # Text replacements
    # ======================

 

    def _replace_masked(text):
        def repl(m):
            prefix, d = m.group(1), m.group(2)
            return prefix + (map3.get(d, d) if len(d)==3 else map4.get(d, d))
        return re.sub(r'([Xx\*]+)(\d{3,4})', repl, text)

    def _bump_amounts(text):
        inc = rng.randint(100,999)
        pats = [
            r'(Avl\.?\s*Bal(?: INR)?[^0-9]*)(\d+(\.\d+)?)',
            r'(Avail\.?\.?bal(?: INR)?[^0-9]*)(\d+(\.\d+)?)',
            r'(\bBal INR\s*)(\d+(\.\d+)?)',
            r'(Available Credit limit is INR\s*)(\d+(\.\d+)?)',
            r'(The Available Balance is INR\s*)(\d+(\.\d+)?)',
            r'(\bTotal Avail\.?bal(?: INR)?[^0-9]*)(\d+(\.\d+)?)',
            r'(credited(?: to| with)?[^0-9]{0,30}(?:Rs\.?|INR)\s*)(\d+(\.\d+)?)',
            r'(received[^0-9]{0,30}(?:Rs\.?|INR)\s*)(\d+(\.\d+)?)',
            r'(Payment of\s*(?:Rs\.?|INR)\s*)(\d+(\.\d+)?)',
            r'((?:Rs\.?|INR)\s*)(\d+(\.\d+)?)(?=[^0-9]{0,12}\bcredited\b)',
            r'((?:Rs\.?|INR)\s*)(\d+(\.\d+)?)(?=[^0-9]{0,12}\breceived\b)',
            r'((?:Rs\.?|INR)\s*)(\d+(\.\d+)?)(?=[^0-9]{0,12}\bsent\b)',
            r'(debited(?: from| by)?[^0-9]{0,30}(?:Rs\.?|INR)\s*)(\d+(\.\d+)?)',
            r'(\bdebited INR\s*)(\d+(\.\d+)?)',
            r'((?:Rs\.?|INR)\s*)(\d+(\.\d+)?)(?=[^0-9]{0,12}\bdebited\b)',
            r'((?:Rs\.?|INR)\s*)(\d+(?:\.\d+)?)'
            r'(debited by\s*)(\d+(\.\d+)?)',
            # 🔥 NEW catch-all – matches Rs / INR amounts anywhere (even decimals like 450.00)
            r'((?:Rs\.?|INR)\s*)(\d{1,7}(?:[.,]\d{1,2})?)'

        ]
        def add_amt(num):
            clean = num.replace(",", "")
            if "." in clean:
                a, b = clean.split(".", 1)
                return str(int(a) + inc) + "." + b
            else:
                return str(int(clean) + inc)
           
        for pat in pats:
            text = re.sub(pat, lambda m: m.group(1)+add_amt(m.group(2)), text, flags=re.IGNORECASE)
        return text

    def _replace_txn_ids(text):
        text = re.sub(r'(\bIMPS Ref[:\.]?\s*)(\d{6,})', lambda m: m.group(1) + "".join(str(rng.randint(0,9)) for _ in range(len(m.group(2)))), text, flags=re.IGNORECASE)
        text = re.sub(r'(\bUPI:)(\d{6,})', lambda m: m.group(1) + "".join(str(rng.randint(0,9)) for _ in range(len(m.group(2)))), text)
        text = re.sub(r'(\bUPI Ref No\s*)(\d{6,})', lambda m: m.group(1) + "".join(str(rng.randint(0,9)) for _ in range(len(m.group(2)))), text, flags=re.IGNORECASE)
        def utr_repl(m):
            prefix, body = m.group(1), m.group(2)
            if body.isdigit() and len(body) >= 12:
                keep = body[:4]  # first 4 digit same rakho
                rand_part = "".join(str(rng.randint(0,9)) for _ in range(len(body)-4))
                return prefix + keep + rand_part
            else:
                body2 = re.sub(r'\d', lambda _: str(rng.randint(0,9)), body)
                return prefix + body2
            
        text = re.sub(r'(\bUTR\b[^A-Za-z0-9]*)(\w{8,})', utr_repl, text, flags=re.IGNORECASE)
        text = re.sub(r'(\bRef no\.\s*)(\d{6,})', lambda m: m.group(1) + "".join(str(rng.randint(0,9)) for _ in range(len(m.group(2)))), text, flags=re.IGNORECASE)
        text = re.sub(r'(\bRefno\s*)(\d{6,})', lambda m: m.group(1) + "".join(str(rng.randint(0,9)) for _ in range(len(m.group(2)))), text, flags=re.IGNORECASE)
        text = re.sub(r'(\bRef[:\.]?\s*)(\d{6,})',
                      lambda m: m.group(1) + "".join(str(random.randint(0,9)) for _ in range(len(m.group(2)))),
                      text, flags=re.IGNORECASE)
        text = re.sub(r'(\bRef no\.\s*)(\d{6,})',
                      lambda m: m.group(1) + "".join(str(random.randint(0,9)) for _ in range(len(m.group(2)))),
                      text, flags=re.IGNORECASE)
        ext = re.sub(r'(\bRefno\s*)(\d{6,})',
                     lambda m: m.group(1) + "".join(str(random.randint(0,9)) for _ in range(len(m.group(2)))),
                     text, flags=re.IGNORECASE)
        return text

    def _replace_ipbmsg_by(text, address_attr):
        if "VM-IPBMSG" not in address_attr:
            return text
        return re.sub(
            r'by\s+[A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+\.?\s+IMPS Ref',
            lambda m: "by " + _rand_indian_name(rng, first_names, last_names) + ". IMPS Ref",
            text
        )

    def _replace_sbi_trf_to(text, address_attr):
        if not re.search(r'SBI', address_attr):
            return text
        return re.sub(
            r'trf to\s+[A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+(?=\s+Refno)',
            lambda m: "trf to " + _rand_indian_name(rng, first_names, last_names),
            text,
            flags=re.IGNORECASE
        )

    def _sync_body_date(block):
        m = re.search(r'date="(\d{10,})"', block)
        if not m:
            return block
        ts = int(m.group(1))
        dt = datetime.fromtimestamp(ts/1000)
        date_str1 = dt.strftime("%d-%m-%Y")
        time_str  = dt.strftime("%H:%M:%S")

        def body_repl(match):
            text = match.group(1)
            text = re.sub(r"\b\d{1,2}[-/][A-Za-z0-9]{2,}[-/]\d{2,4}\b", date_str1, text)
            text = re.sub(r"\b\d{1,2}[:]\d{2}[:]\d{2}\b", time_str, text)
            return f'body="{text}"'

        return re.sub(r'body="(.*?)"', body_repl, block)

    def _replace_loan_numbers(text):
        def scramble_loan(match):
            s = match.group(0)
            return re.sub(r'\d', lambda _: str(rng.randint(0,9)), s)
        text = re.sub(r'\bWB[A-Za-z0-9]+\b', scramble_loan, text)
        text = re.sub(r'\bGL[A-Za-z0-9]+\b', scramble_loan, text)
        return text

    specific_name_map = {}
    def _replace_specific_names(text):
        text = re.sub(r'\bYash Kapoor\b', lambda m: specific_name_map.setdefault("Yash Kapoor", _rand_indian_name(rng, first_names, last_names)), text)
        text = re.sub(r'\bAkash\b', lambda m: specific_name_map.setdefault("Akash", rng.choice([fn for fn in first_names if fn!="Akash"])), text)
        return text

    def _replace_upi_handles(text):
        return re.sub(r'\b([a-z0-9]+)@([a-z]+)\b', lambda m: f"{_map_upi_local(m.group(1))}@{m.group(2)}", text)

    def _replace_companies(text):
        variants = ["LALJI ENTERPRISES","Lalji Enterprises","lalji enterprises",
                    "SHREEEMAHAVIRJEWELLERS","Shreeemahavirjewellers","shreeemahavirjewellers"]
        def choose(sample): return _case_like(sample, rng.choice(company_names))
        for v in variants:
            if v in text: text = text.replace(v, choose(v))
        return re.sub(r'(by\s+)([A-Z][A-Za-z &\.]+?)(,?\s*INFO\b)',
                      lambda m: m.group(1)+_case_like(m.group(2), rng.choice(company_names))+m.group(3), text)

    # ======================
    # Apply all
    # ======================

    out_blocks = []
    for b in kept:
        block = b
        block = _bump_amounts(block)
        block = _replace_specific_names(block)
        block = _replace_companies(block)
        block = _replace_upi_handles(block)
        block = _replace_masked(block)
        block = _replace_txn_ids(block)
        block = _replace_loan_numbers(block)
        maddr = re.search(r'address="([^"]+)"', block)
        addr = maddr.group(1) if maddr else ""
        if 'IPBMSG' in addr:
            block = _replace_ipbmsg_by(block, addr)
        if 'SBI' in addr:
            block = _replace_sbi_trf_to(block, addr)
        block = _sync_body_date(block)
        block = _replace_to_from_names(block, rng, first_names, last_names)
        mdate = re.search(r'date="(\d{10,})"', block)
        dt = datetime.fromtimestamp(int(mdate.group(1))/1000) if mdate else None
        block = _final_text_fixes(block, dt)
        out_blocks.append(block)
    
    header, footer = _header_footer(xml_text)
    count = len(out_blocks)

    if header.strip():
        header = re.sub(r'count="\d+"', f'count="{count}"', header)
    else:
        header = f"<?xml version='1.0' encoding='utf-8'?>\n<smses count=\"{count}\">"

    if not footer.strip():
        footer = "</smses>"

    xml_out = header + "\n  " + "\n  ".join(out_blocks) + "\n" + footer
    return xml_out
