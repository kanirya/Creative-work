import urllib.request, json

tests = [
    ("http://localhost:8002/api/lms/login/status", "Login status"),
    ("http://localhost:8002/api/lms/assignments/all", "All assignments"),
]

for url, name in tests:
    try:
        r = urllib.request.urlopen(url, timeout=60)
        data = json.loads(r.read().decode())
        if isinstance(data, list):
            print(f"OK  {name}: {len(data)} items")
            for a in data[:5]:
                cid = a.get("course_id", "?")
                aname = a.get("name", "?")[:50]
                status = a.get("submission_status", "?")
                can_sub = "✓ can submit" if a.get("can_submit") else ""
                print(f"    [{cid}] {aname} — {status} {can_sub}")
        else:
            print(f"OK  {name}: {data}")
    except Exception as e:
        print(f"ERR {name}: {e}")
