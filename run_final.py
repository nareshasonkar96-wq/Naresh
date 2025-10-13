#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Multi-Variant Runner for SMS + MMS + Mobile Number Variant (Cloud Version)
---------------------------------------------------------------------------
- Automatically detects any uploaded .xml file in current working directory.
- Runs build_variant(), build_mms_variant(), and mobile number variant mapping.
"""

import os
import sys
from datetime import datetime
from lxml import etree
from sms_variant_tools import build_variant
from mms_variant_tools import build_mms_variant
from mobile_number_variant import apply_mobile_number_variant

# ========= SETTINGS =========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_variants")
NUM_VARIANTS = int(os.environ.get("NUM_VARIANTS", 3))   # ✅ dynamic
FUTURE = False
# ============================


def find_input_xml():
    """Auto-detect the first .xml file (uploaded file)."""
    xml_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(".xml")]
    if not xml_files:
        print("❌ No XML file found in the working directory.")
        sys.exit(1)
    print(f"📄 Using input file: {xml_files[0]}")
    return [os.path.join(BASE_DIR, xml_files[0])]


def merge_xml_files(file_paths):
    combined_root = etree.Element("smses")
    for path in file_paths:
        if not os.path.exists(path):
            print(f"❌ Error: {path} not found.")
            sys.exit(1)
        tree = etree.parse(path)
        root = tree.getroot()
        for child in list(root):
            combined_root.append(child)
    return etree.tostring(combined_root, encoding="utf-8").decode("utf-8")


def remove_future_blocks(xml_text):
    now_ms = int(datetime.now().timestamp() * 1000)
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml_text.encode("utf-8"), parser=parser)
    removed = 0
    for tag in ["sms", "mms"]:
        for elem in list(root.findall(tag)):
            try:
                elem_date = int(elem.attrib.get("date", "0"))
                if elem_date > now_ms:
                    root.remove(elem)
                    removed += 1
            except Exception:
                continue
    if removed > 0:
        print(f"🗑️ Removed {removed} future SMS/MMS")
    return etree.tostring(root, encoding="utf-8").decode("utf-8")


def sort_by_date(xml_text):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml_text.encode("utf-8"), parser=parser)
    elems = list(root)
    elems.sort(key=lambda e: int(e.attrib.get("date", "0")))
    new_root = etree.Element("smses")
    for elem in elems:
        new_root.append(elem)
    return etree.tostring(new_root, encoding="utf-8").decode("utf-8")


def main():
    print("=== SMS + MMS + Mobile Number Variant Runner (Cloud Mode) ===")

    # 🧩 Automatically detect uploaded XML
    input_files = find_input_xml()
    print(f"Input files : {input_files}")
    print(f"Saving {NUM_VARIANTS} variants to: {OUTPUT_DIR}")

    # ✅ Merge or read single file
    if len(input_files) == 1:
        with open(input_files[0], "r", encoding="utf-8") as f:
            xml_text = f.read()
    else:
        xml_text = merge_xml_files(input_files)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ✅ Generate variants
    for i in range(1, NUM_VARIANTS + 1):
        out_file = os.path.join(OUTPUT_DIR, f"variant_{i}.xml")

        sms_result = build_variant(xml_text, seed=12345 + i)
        mms_result = build_mms_variant(xml_text)

        parser = etree.XMLParser(recover=True)
        sms_root = etree.fromstring(sms_result.encode("utf-8"), parser=parser)
        mms_root = etree.fromstring(mms_result.encode("utf-8"), parser=parser)
        combined_root = etree.Element("smses")
        for child in list(sms_root):
            combined_root.append(child)
        for child in list(mms_root):
            combined_root.append(child)
        final_xml = etree.tostring(combined_root, encoding="utf-8").decode("utf-8")

        final_xml = sort_by_date(final_xml)

        if FUTURE:
            final_xml = remove_future_blocks(final_xml)

        final_xml, phone_map = apply_mobile_number_variant(final_xml, seed=5000 + i)
        map_file = out_file.replace(".xml", "_mobile_map.txt")
        with open(map_file, "w", encoding="utf-8") as mf:
            for old, new in phone_map.items():
                mf.write(f"{old} → {new}\n")
        print(f"📱 Mapped {len(phone_map)} unique mobile numbers")

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(final_xml)
        print(f"✅ Saved: {out_file}")

    print("🎉 All variants generated successfully with mobile mapping!")


if __name__ == "__main__":
    main()
