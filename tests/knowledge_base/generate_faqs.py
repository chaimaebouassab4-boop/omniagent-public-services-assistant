import os
import json
from pathlib import Path

# Force UTF-8
import sys
sys.stdout.reconfigure(encoding='utf-8')

KB_DIR = Path(__file__).resolve().parent

folders = [
    "administrative",
    "birth",
    "criminal_record",
    "death",
    "good_conduct",
    "life",
    "marriage",
    "non_property",
    "residence",
    "single_status"
]

for folder in folders:
    folder_path = KB_DIR / folder
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Skipping {folder}, not a dir")
        continue
    
    # Find JSON file
    json_files = list(folder_path.glob("*.json"))
    if not json_files:
        print(f"No JSON in {folder}")
        continue
    
    # Assume the first one is the target json
    json_path = json_files[0]
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        service_name = data.get("title_ar") or data.get("service_name_ar", "الخدمة")
        faq_list = data.get("faq", [])
        
        md_content = f"# FAQ - {service_name}\n\n"
        md_content += f"<!-- Compatibility mirror. Canonical structured content: {json_path.name} -->\n\n"
        md_content += "**محدث: مارس 2026**\n\n"
        
        for i, item in enumerate(faq_list, start=1):
            q = item.get("question", "")
            a = item.get("answer", "")
            md_content += f"{i}. **{q}**  \n   {a}\n\n"
            
        faq_md_path = folder_path / "faq.md"
        with open(faq_md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"✅ Created faq.md in {folder}")
    except Exception as e:
        print(f"❌ Error processing {folder}: {e}")
