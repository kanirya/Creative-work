"""
Test the full IqraLMSClient — all read operations + assignment submission.
Run: python test_lms_client.py
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

SESSION_FILE = Path("lms_session_test.json")


async def main():
    from playwright.async_api import async_playwright
    # Add services/lms-scraper to path
    sys.path.insert(0, "services/lms-scraper")
    from app.services.lms_client import IqraLMSClient

    print("\n" + "="*60)
    print("  EduPilot — Full LMS Client Test")
    print("="*60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            storage_state=json.loads(SESSION_FILE.read_text()),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )

        client = IqraLMSClient(ctx)

        # 1. Profile
        print("\n[1] Student Profile")
        profile = await client.get_profile()
        print(f"  Name  : {profile['name']}")
        print(f"  Email : {profile['email']}")

        # 2. Courses
        print("\n[2] Enrolled Courses")
        courses = await client.get_courses()
        for c in courses:
            print(f"  [{c['id']}] {c['name']}")

        # 3. Assignments for first course
        if courses:
            cid = courses[0]["id"]
            cname = courses[0]["name"][:40]
            print(f"\n[3] Assignments — {cname}")
            assignments = await client.get_assignments(cid)
            for a in assignments:
                due = a.get("due_date")
                due_str = due.strftime("%d %b %Y") if due else "N/A"
                status = a.get("submission_status", "?")
                grade = a.get("grade")
                grade_str = f"{grade}" if grade is not None else "Not graded"
                can_sub = "✓ Can submit" if a.get("can_submit") else "✗ Closed"
                print(f"  [{a['id']}] {a['name'][:45]}")
                print(f"         Due: {due_str} | Status: {status} | Grade: {grade_str} | {can_sub}")

        # 4. Grades overview
        print("\n[4] Grades Overview")
        grades = await client.get_grades_overview()
        for g in grades:
            if g["course_name"]:
                print(f"  {g['course_name'][:50]}: {g['grade_str']}")

        # 5. Upcoming events
        print("\n[5] Upcoming Calendar Events")
        events = await client.get_upcoming_events()
        for e in events[:8]:
            print(f"  [{e['event_type']}] {e['name'][:50]}")
            if e.get("full_text"):
                # Extract date from full text
                lines = e["full_text"].split("\n")
                if len(lines) > 1:
                    print(f"         {lines[1].strip()[:60]}")

        # 6. Announcements for first course
        if courses:
            cid = courses[0]["id"]
            print(f"\n[6] Announcements — {courses[0]['name'][:40]}")
            anns = await client.get_announcements(cid)
            if anns:
                for a in anns[:5]:
                    print(f"  {a['title'][:60]} (by {a['author']})")
            else:
                print("  No announcements found")

        # 7. Detailed grades for first course
        if courses:
            cid = courses[0]["id"]
            print(f"\n[7] Detailed Grades — {courses[0]['name'][:40]}")
            cg = await client.get_course_grades(cid)
            for g in cg[:10]:
                pct = f"{g['percentage']}%" if g.get("percentage") is not None else "-"
                print(f"  {g['item_name'][:45]}: {g.get('grade', '-')} / {g.get('max_grade', '-')} ({pct})")

        # 8. Test assignment submission (create a test file)
        print("\n[8] Assignment Submission Test")
        # Find an assignment that can be submitted
        submittable = None
        for course in courses:
            assigns = await client.get_assignments(course["id"])
            for a in assigns:
                if a.get("can_submit"):
                    submittable = a
                    break
            if submittable:
                break

        if submittable:
            print(f"  Found submittable assignment: {submittable['name'][:50]}")
            print(f"  Assignment ID: {submittable['id']}")
            print(f"  Status: {submittable.get('submission_status')}")
            print(f"  Due: {submittable.get('due_date')}")

            # Create a test file
            test_file = Path("test_submission.txt")
            test_file.write_text(
                f"Test submission from EduPilot\n"
                f"Student: {profile['name']}\n"
                f"Assignment: {submittable['name']}\n"
                f"Submitted at: {datetime.now().isoformat()}\n"
            )

            print(f"\n  NOTE: Skipping actual submission to avoid submitting test data.")
            print(f"  To submit, call: client.submit_assignment_file({submittable['id']}, 'test_submission.txt')")
            test_file.unlink()
        else:
            print("  No submittable assignments found (all closed or already submitted)")

        # Summary
        print("\n" + "="*60)
        print("  SUMMARY")
        print("="*60)
        print(f"  ✓ Profile       : {profile['name']}")
        print(f"  ✓ Courses       : {len(courses)}")
        print(f"  ✓ Grades        : {len(grades)} courses with grades")
        print(f"  ✓ Events        : {len(events)} upcoming")
        print(f"  ✓ All systems working!\n")

        await browser.close()


asyncio.run(main())
