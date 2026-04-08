"""Test assignments endpoint directly."""
import urllib.request, json

# Test assignments for Computer Architecture course (id=10673)
url = "http://localhost:8002/api/lms/assignments/10673"
try:
    r = urllib.request.urlopen(url, timeout=60)
    data = json.loads(r.read().decode())
    print(f"Assignments for course 10673: {len(data)} items")
    for a in data:
        print(f"  [{a.get('id')}] {a.get('name','?')[:50]}")
        print(f"       Status: {a.get('submission_status','?')} | Due: {a.get('due_date','?')} | Can submit: {a.get('can_submit','?')}")
except Exception as e:
    print(f"Error: {e}")

# Test all assignments
url2 = "http://localhost:8002/api/lms/assignments/all"
try:
    r2 = urllib.request.urlopen(url2, timeout=120)
    data2 = json.loads(r2.read().decode())
    print(f"\nAll assignments: {len(data2)} total")
    for a in data2[:10]:
        print(f"  [{a.get('course_id')}] {a.get('name','?')[:45]} — {a.get('submission_status','?')}")
except Exception as e:
    print(f"All assignments error: {e}")
