import streamlit as st
import random
import io
import zipfile
import getindianname as gname
import pandas as pd

# ========== CONFIG ==========
PASSWORD = "Naresh@41952"   # 🛡️ change this to any password you want
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

# ========== MAIN APP ==========
st.title("📱 iCloud VCF Generator")
st.caption("Generate realistic Indian contact files (.vcf and .csv) for testing or import.")

num_files = st.number_input("Number of VCF files to generate", 1, 50, 5)
min_contacts = st.number_input("Minimum contacts per file", 10, 1000, 500)
max_contacts = st.number_input("Maximum contacts per file", 10, 1000, 600)
vcf_base_name = st.text_input("Base file name", "contacts")

def generate_icloud_vcf(num_files, min_contacts, max_contacts, vcf_base_name="contacts"):
    used_numbers = set()

    def random_indian_number():
        while True:
            start_digit = random.choice(["7", "8", "9"])
            num = start_digit + ''.join(random.choices("0123456789", k=9))
            if num in used_numbers:
                continue
            prefix_type = random.choice(["plain", "+91",])
            if prefix_type == "91":
                formatted = f"91{num}"
            elif prefix_type == "+91":
                formatted = f"+91{num}"
            elif prefix_type == "0":
                formatted = f"0{num}"
            else:
                formatted = num
            used_numbers.add(num)
            return formatted

    relationship_names = [
        "Papa", "Mummy", "Bhai", "Didi", "Bhabhi", "Chacha", "Chachi",
        "Mama", "Mami", "Bua", "Fufa", "Nana", "Nani", "Dada", "Dadi",
        "Baby", "Janu", "Darling", "Hubby", "Wifey", "Bestie", "Dost"
    ]
    service_suffixes = [
        "Kirana Store", "Tailor", "Maid", "Watchman", "Driver", "Electrician",
        "Plumber", "Gas Agency", "Internet Guy", "Mechanic", "Doctor", "Lawyer",
        "CA", "Mobile Shop", "Car Wash", "Laundry", "Cleaning", "Garage",
        "Delivery", "Courier", "Dudhvala", "Majdoor"
    ]
    locations = [
        "Surat", "Ahmedabad", "Mumbai", "Delhi", "Rajkot", "Vadodara", "Dahod",
        "Gota", "Paldi", "Anand", "Gandhinagar", "Memnagar", "Mahmedabad",
        "Sanand", "Akota", "Gorwa", "Manjalpur", "Bhayli"
    ]

    all_data = []
    memory_zip = io.BytesIO()
    with zipfile.ZipFile(memory_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for i in range(1, num_files + 1):
            count = random.randint(min_contacts, max_contacts)
            numbers = [random_indian_number() for _ in range(count)]
            rename_indices = random.sample(range(count), min(180, count))
            used_relationships = set()
            names_list = []

            for idx in range(count):
                if idx in rename_indices and len(used_relationships) < len(relationship_names):
                    available = list(set(relationship_names) - used_relationships)
                    selected = random.choice(available)
                    names_list.append(selected)
                    used_relationships.add(selected)
                else:
                    random_name = gname.randname().split()[0]
                    service = random.choice(service_suffixes)
                    location = random.choice(locations)
                    names_list.append(f"{random_name} {service} {location}")

            vcf_text = ""
            for name, mobile in zip(names_list, numbers):
                vcf_text += (
                    f"BEGIN:VCARD\r\nVERSION:3.0\r\n"
                    f"N:{name};;;;\r\nFN:{name}\r\n"
                    f"TEL;TYPE=VOICE,CELL;VALUE=text:{mobile}\r\nEND:VCARD\r\n\r\n"
                )
                all_data.append({"Name": name, "Mobile": mobile})
            zipf.writestr(f"{vcf_base_name}_{i}_icloud_realistic.vcf", vcf_text)

    memory_zip.seek(0)
    df = pd.DataFrame(all_data)
    return memory_zip, df

if st.button("🚀 Generate Files"):
    result_zip, result_csv = generate_icloud_vcf(num_files, min_contacts, max_contacts, vcf_base_name)
    st.success("✅ All files generated successfully — ready for download!")

    st.download_button("⬇️ Download ZIP (.vcf)", data=result_zip,
                       file_name="icloud_vcf_files.zip", mime="application/zip")

    csv_bytes = result_csv.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV (.csv)", data=csv_bytes,
                       file_name="icloud_contacts.csv", mime="text/csv")

st.markdown("<div class='footer'>Made with ❤️ by <b>Naresha 💻</b></div>", unsafe_allow_html=True)
