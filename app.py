import streamlit as st
import random
import os
import io
import zipfile
import getindianname as gname

st.set_page_config(page_title="iCloud VCF Generator", page_icon="📱", layout="centered")

st.title("📱 iCloud VCF Generator")
st.caption("Generate realistic Indian contact .vcf files for testing or import.")

num_files = st.number_input("Number of VCF files to generate", 1, 50, 5)
min_contacts = st.number_input("Minimum contacts per file", 10, 1000, 200)
max_contacts = st.number_input("Maximum contacts per file", 10, 1000, 300)
vcf_base_name = st.text_input("Base file name", "contacts")

def generate_icloud_vcf(num_files, min_contacts, max_contacts, vcf_base_name="contacts"):
    used_numbers = set()

    def random_indian_number():
        while True:
            start_digit = random.choice(["7", "8", "9"])
            num = start_digit + ''.join(random.choices("0123456789", k=9))
            if num in used_numbers:
                continue
            prefix_type = random.choice(["plain", "91", "+91", "0"])
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
            zipf.writestr(f"{vcf_base_name}_{i}_icloud_realistic.vcf", vcf_text)

    memory_zip.seek(0)
    return memory_zip

if st.button("🚀 Generate VCF Files"):
    result = generate_icloud_vcf(num_files, min_contacts, max_contacts, vcf_base_name)
    st.success("✅ All VCF files generated successfully — ready for download!")
    st.download_button("⬇️ Download ZIP", data=result, file_name="icloud_vcf_files.zip", mime="application/zip")
