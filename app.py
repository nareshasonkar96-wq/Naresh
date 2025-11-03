import streamlit as st
import random
import io
import zipfile
import pandas as pd
import os

# ========== CONFIG ==========
PASSWORD = "Naresh@41952"
CSV_PATH = "Cleaned_Numbers_Without_91.csv"
COLUMN_NAME = "Phone Number (Without 91)"
NAMES_TXT = "contact_names.txt"

st.set_page_config(page_title="iCloud VCF Generator", page_icon="📱", layout="centered")

# ========== PAGE STYLE ==========
st.markdown("""
    <style>
        body {
            background: linear-gradient(180deg, #007bff 0%, #00bfff 100%);
            color: white;
        }
        .stApp {
            background: linear-gradient(180deg, #007bff 0%, #00bfff 100%);
            color: white;
        }
        div.block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            background-color: rgba(255,255,255,0.1);
            border-radius: 15px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
        }
        h1, h2, h3, h4 {
            color: white !important;
            text-align: center;
        }
        .footer {
            text-align: center;
            color: white;
            margin-top: 50px;
            font-size: 0.9em;
            opacity: 0.8;
        }
    </style>
""", unsafe_allow_html=True)

# ========== PASSWORD LOGIN ==========
st.title("🔐 Secure iCloud VCF Generator")
pwd = st.text_input("Enter password to access:", type="password")
if pwd != PASSWORD:
    st.warning("Please enter the correct password to continue.")
    st.stop()

# ========== LOAD CUSTOM NAMES ==========
if os.path.exists(NAMES_TXT):
    with open(NAMES_TXT, "r", encoding="utf-8") as f:
        custom_names = [line.strip() for line in f if line.strip()]
else:
    st.error(f"❌ Name list file not found: {NAMES_TXT}")
    st.stop()

if len(custom_names) < 10:
    st.warning("⚠️ The name list has very few entries. You may get duplicates if file has fewer names than required contacts.")

# ========== MAIN APP ==========
st.title("📱 iCloud VCF Generator")
st.caption("Generate realistic Indian contact files (.vcf and .csv) using your name list.")

num_files = st.number_input("Number of VCF files to generate", 1, 50, 5)
min_contacts = st.number_input("Minimum contacts per file", 10, 1000, 500)
max_contacts = st.number_input("Maximum contacts per file", 10, 1200, 600)
vcf_base_name = st.text_input("Base file name", "contacts")

# ========== LOAD CSV & SUMMARY ==========
if not os.path.exists(CSV_PATH):
    st.error(f"❌ CSV file not found: {CSV_PATH}")
    st.stop()

df_csv = pd.read_csv(CSV_PATH)

# Clean up number format (avoid .0 issue)
df_csv[COLUMN_NAME] = df_csv[COLUMN_NAME].astype(str).str.replace(r"\.0$", "", regex=True)
df_csv[COLUMN_NAME] = df_csv[COLUMN_NAME].str.replace(r"\D", "", regex=True)

if COLUMN_NAME not in df_csv.columns:
    st.error(f"❌ Column '{COLUMN_NAME}' not found in CSV file.")
    st.stop()

csv_numbers = df_csv[COLUMN_NAME].dropna().astype(str).unique().tolist()
total_csv = len(csv_numbers)

st.markdown(f"""
### 📋 Current CSV Summary
- **Total numbers available:** {total_csv}
- **File:** `{CSV_PATH}`
""")

confirm_overwrite = st.checkbox("🛡️ I confirm to overwrite the CSV file after generation")

# ========== MAIN FUNCTION ==========
def generate_icloud_vcf(num_files, min_contacts, max_contacts, vcf_base_name="contacts"):
    used_numbers = set()
    all_data = []
    global csv_numbers

    memory_zip = io.BytesIO()
    total_used_from_csv = 0
    total_random_generated = 0

    def random_indian_number():
        while True:
            start_digit = random.choice(["7", "8", "9"])
            num = start_digit + ''.join(random.choices("0123456789", k=9))
            if num in used_numbers or num in csv_numbers:
                continue
            used_numbers.add(num)
            return f"+91 {num}"

    with zipfile.ZipFile(memory_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for i in range(1, num_files + 1):
            count = random.randint(min_contacts, max_contacts)
            csv_needed = min(int(count * 0.7), len(csv_numbers))
            random_needed = count - csv_needed
            total_used_from_csv += csv_needed
            total_random_generated += random_needed

            selected_csv = random.sample(csv_numbers, csv_needed) if csv_needed > 0 else []
            if confirm_overwrite:
                csv_numbers = [n for n in csv_numbers if n not in selected_csv]

            # ✅ Format numbers properly: +91 + space + number
            csv_prefixed = []
            for num in selected_csv:
                clean_num = str(num).replace(".0", "").strip()
                clean_num = "".join(filter(str.isdigit, clean_num))
                if not clean_num.startswith("91") and len(clean_num) == 10:
                    csv_prefixed.append(f"+91 {clean_num}")
                elif clean_num.startswith("91") and len(clean_num) == 12:
                    csv_prefixed.append(f"+{clean_num[:2]} {clean_num[2:]}")
                else:
                    csv_prefixed.append(f"+91 {clean_num[-10:]}")

            random_numbers = [random_indian_number() for _ in range(random_needed)]
            all_numbers = csv_prefixed + random_numbers
            random.shuffle(all_numbers)

            # 💡 Unique names per file
            unique_names = random.sample(custom_names, min(count, len(custom_names)))

            vcf_text = ""
            for name, mobile in zip(unique_names, all_numbers):
                vcf_text += (
                    f"BEGIN:VCARD\r\n"
                    f"VERSION:3.0\r\n"
                    f"N:{name};;;\r\n"
                    f"FN:{name}\r\n"
                    f"TEL;TYPE=VOICE,CELL;VALUE=text:{mobile}\r\n"
                    f"END:VCARD\r\n"
                )
                all_data.append({"Name": name, "Mobile": mobile})

            zipf.writestr(f"{vcf_base_name}_{i}_icloud_realistic.vcf", vcf_text)

    if confirm_overwrite:
        df_remaining = pd.DataFrame({COLUMN_NAME: csv_numbers})
        df_remaining.to_csv(CSV_PATH, index=False, encoding="utf-8")

    memory_zip.seek(0)
    df = pd.DataFrame(all_data)
    return memory_zip, df, total_used_from_csv, total_random_generated, len(csv_numbers), total_csv

# ========== RUN BUTTON ==========
if st.button("🚀 Generate Files"):
    result_zip, result_csv, used_csv, generated_new, remaining, total_csv = generate_icloud_vcf(
        num_files, min_contacts, max_contacts, vcf_base_name
    )

    if confirm_overwrite:
        st.success("✅ CSV file updated successfully.")
    else:
        st.info("ℹ️ CSV file NOT modified (Confirm Overwrite was unchecked).")

    st.success(
        f"✅ Used {used_csv} CSV numbers (+91 space format) and generated {generated_new} random numbers.\n\n"
        f"📊 **Summary:**\n"
        f"- Total before: {total_csv}\n"
        f"- Used this run: {used_csv}\n"
        f"- Remaining now: {remaining}"
    )

    st.download_button(
        "⬇️ Download ZIP (.vcf)", data=result_zip,
        file_name="icloud_vcf_files.zip", mime="application/zip"
    )

    csv_bytes = result_csv.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV (.csv)", data=csv_bytes,
        file_name="icloud_contacts.csv", mime="text/csv"
    )

st.markdown("<div class='footer'>Made with ❤️ by <b>Naresha 💻</b></div>", unsafe_allow_html=True)
