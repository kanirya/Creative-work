"""Check submission form HTML for file upload fields."""
from pathlib import Path
import re

html = Path("lms_explore/submission_form_52541.html").read_text(encoding="utf-8")
print(f"Form HTML size: {len(html)}")

# Find form action
forms = re.findall(r'<form[^>]*action="([^"]*)"[^>]*>', html)
print(f"Form actions: {forms}")

# Find all input fields
inputs = re.findall(r'<input[^>]*>', html)
for inp in inputs:
    if any(x in inp for x in ['name=', 'type=']):
        name = re.search(r'name="([^"]*)"', inp)
        type_ = re.search(r'type="([^"]*)"', inp)
        value = re.search(r'value="([^"]*)"', inp)
        print(f"  input: type={type_.group(1) if type_ else '?'!r} name={name.group(1) if name else '?'!r} value={value.group(1)[:30] if value else ''!r}")

# Find textareas
textareas = re.findall(r'<textarea[^>]*name="([^"]*)"', html)
print(f"Textareas: {textareas}")

# Find file manager
if 'filemanager' in html.lower():
    idx = html.lower().find('filemanager')
    print(f"Filemanager context: {html[max(0,idx-100):idx+300]}")

# Find sesskey (CSRF)
sesskey = re.search(r'sesskey["\s]*[:=]["\s]*([a-zA-Z0-9]+)', html)
if sesskey:
    print(f"Sesskey: {sesskey.group(1)}")

# Find itemid for file upload
itemid = re.search(r'"itemid"\s*:\s*(\d+)', html)
if itemid:
    print(f"File itemid: {itemid.group(1)}")

# Find draftitemid
draft = re.findall(r'draftitemid[^"]*"[^"]*"(\d+)"', html)
print(f"Draft item IDs: {draft}")

# Find repository info
repo = re.findall(r'"repositorytype"\s*:\s*"([^"]*)"', html)
print(f"Repository types: {repo}")
