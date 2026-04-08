"""Test assignments directly with the LMS client."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, "services/lms-scraper")

os.environ["MS_EMAIL"] = "muhammad.141510.isb@iqra.edu.pk"
os.environ["MS_PASSWORD"] = "Bree@4u4u"
os.environ["SESSION_STORAGE_PATH"] = str(Path("lms_session_test.json").absolute())
os.environ["LMS_BASE_URL"] = "https://lms.iqra.edu.pk"
os.environ["API_GATEWAY_URL"] = "http://localhost:5000"
os.environ["DATABASE_URL"] = "postgresql://edupilot:password@localhost:5432/edupilot"
os.environ["OPENAI_API_KEY"] = "sk-placeholder"
os.environ["EMBEDDING_MODEL"] = "text-embedding-3-small"


async def test():
    from app.services.lms_auth import get_lms_auth_service
    from app.services.lms_client import IqraLMSClient

    auth = get_lms_auth_service()
    ctx = await auth.get_authenticated_context()
    client = IqraLMSClient(ctx)

    print("Testing assignments for course 10673...")
    assigns = await client.get_assignments(10673)
    print(f"Found {len(assigns)} assignments")
    for a in assigns:
        print(f"  [{a['id']}] {a['name']} - status={a.get('submission_status','?')} can_submit={a.get('can_submit','?')}")

    print("\nTesting all courses...")
    courses = await client.get_courses()
    print(f"Found {len(courses)} courses")

    print("\nTesting all assignments across all courses...")
    all_assigns = []
    for course in courses:
        try:
            ca = await client.get_assignments(course["id"])
            all_assigns.extend(ca)
            print(f"  Course {course['id']}: {len(ca)} assignments")
        except Exception as e:
            print(f"  Course {course['id']}: ERROR - {e}")

    print(f"\nTotal assignments: {len(all_assigns)}")
    for a in all_assigns:
        print(f"  [{a.get('course_id')}] {a.get('name','?')[:50]} - {a.get('submission_status','?')}")

    await auth.close()


asyncio.run(test())
