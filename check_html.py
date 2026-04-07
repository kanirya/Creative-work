from pathlib import Path
import re

html = Path("dashboard_debug.html").read_text(encoding="utf-8")
print(f"HTML size: {len(html)} chars")

# Find course links
matches = re.findall(r'href="(/course/view\.php[^"]*)"', html)
print(f"Course links found: {len(matches)}")
for m in matches[:5]:
    print(f"  {m}")

# Check for myoverview
idx = html.find("myoverview")
print(f"\nmyoverview found: {idx > 0}")
if idx > 0:
    print(html[idx:idx+300])

# Check for course-related JS data
for kw in ["coursename", "course-content", "data-courseid", "course_overview"]:
    idx = html.find(kw)
    if idx > 0:
        print(f"\n'{kw}' at {idx}:")
        print(html[max(0,idx-50):idx+200])
        break

# Check for Moodle web service calls
ws_matches = re.findall(r'wsfunction.*?core_course', html)
print(f"\nWeb service course calls: {ws_matches[:3]}")

# Check for enrolled courses in page source
enrolled = re.findall(r'"fullname"\s*:\s*"([^"]+)"', html)
print(f"\nCourse fullnames in JSON: {enrolled[:5]}")
