"""
Complete Iqra LMS Client — scrape AND interact with the LMS.

Capabilities:
  - Scrape courses, assignments, grades, calendar, attendance, quizzes
  - Submit assignments (file upload + text)
  - View submission status
  - Read announcements/forums

All operations use the authenticated Playwright browser context from LMSAuthService.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import BrowserContext, Page

logger = logging.getLogger(__name__)

BASE_URL = "https://lms.iqra.edu.pk"

# ── Date parsing ──────────────────────────────────────────────────────────────

MOODLE_DATE_FORMATS = [
    "%A, %d %B %Y, %I:%M %p",
    "%A, %d %B %Y, %H:%M",
    "%d %B %Y, %I:%M %p",
    "%d %B %Y",
    "%d %B %Y, %H:%M",
]


def parse_date(s: str) -> Optional[datetime]:
    if not s:
        return None
    s = s.strip()
    for fmt in MOODLE_DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


# ── LMS Client ────────────────────────────────────────────────────────────────


class IqraLMSClient:
    """
    Full Iqra LMS client — read and write operations via Playwright.
    """

    def __init__(self, context: BrowserContext):
        self.ctx = context

    # ── Student Profile ───────────────────────────────────────────────────────

    async def get_profile(self) -> Dict[str, str]:
        """Get logged-in student's profile."""
        page = await self.ctx.new_page()
        try:
            await page.goto(f"{BASE_URL}/user/profile.php", wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(500)

            name_el = await page.query_selector("h1, .page-header-headings h1")
            name = (await name_el.inner_text()).strip() if name_el else ""

            email_el = await page.query_selector('[href^="mailto:"]')
            email = (await email_el.inner_text()).strip() if email_el else ""

            # Get user ID from URL or page
            userid_match = re.search(r"id=(\d+)", page.url)
            userid = userid_match.group(1) if userid_match else ""

            return {"name": name, "email": email, "userid": userid}
        finally:
            await page.close()

    # ── Courses ───────────────────────────────────────────────────────────────

    async def get_courses(self) -> List[Dict]:
        """Get all enrolled courses from /my/courses.php."""
        page = await self.ctx.new_page()
        courses = []
        try:
            await page.goto(f"{BASE_URL}/my/courses.php", wait_until="networkidle", timeout=30_000)
            await page.wait_for_timeout(2_000)

            links = await page.query_selector_all('a[href*="/course/view.php?id="]')
            seen = set()
            for link in links:
                href = await link.get_attribute("href") or ""
                m = re.search(r"id=(\d+)", href)
                if not m:
                    continue
                cid = int(m.group(1))
                if cid in seen:
                    continue
                seen.add(cid)
                raw = (await link.inner_text()).strip()
                name = raw.split("\n")[0].strip()
                if not name or name.lower() == "course name":
                    continue

                # Parse course code from name (e.g. "DATABASE SYSTEMS - IUIC_COURSE_SP26_286")
                code_match = re.search(r"IUIC_COURSE_\w+_(\d+)", name)
                code = code_match.group(0) if code_match else ""

                courses.append({
                    "id": cid,
                    "name": name,
                    "code": code,
                    "url": href if href.startswith("http") else f"{BASE_URL}{href}",
                })

            logger.info(f"Found {len(courses)} courses")
            return courses
        finally:
            await page.close()

    # ── Assignments ───────────────────────────────────────────────────────────

    async def get_assignments(self, course_id: int) -> List[Dict]:
        """Get all assignments for a course — fast, no per-assignment page visits."""
        page = await self.ctx.new_page()
        assignments = []
        try:
            url = f"{BASE_URL}/course/view.php?id={course_id}"
            logger.info(f"Loading course page: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30_000)
            await page.wait_for_timeout(2_000)

            current_url = page.url
            logger.info(f"Course page URL after load: {current_url}")
            page_title = await page.title()
            logger.info(f"Page title: {page_title}")

            if "login" in current_url or "microsoftonline" in current_url:
                logger.warning(f"Session expired — redirected to {current_url}")
                return []

            assign_links = await page.query_selector_all('a[href*="/mod/assign/view.php"]')
            logger.info(f"Found {len(assign_links)} assignment links for course {course_id}")

            # Also try alternative selector
            if len(assign_links) == 0:
                alt_links = await page.query_selector_all('li.modtype_assign a.aalink')
                logger.info(f"Alt selector found {len(alt_links)} links")
                if alt_links:
                    assign_links = alt_links
            seen = set()

            title_el = await page.query_selector("h1, .page-header-headings h1")
            course_name = (await title_el.inner_text()).strip() if title_el else f"Course {course_id}"

            for link in assign_links:
                href = await link.get_attribute("href") or ""
                m = re.search(r"id=(\d+)", href)
                if not m:
                    continue
                aid = int(m.group(1))
                if aid in seen:
                    continue
                seen.add(aid)
                raw = (await link.inner_text()).strip()
                name = raw.split("\n")[0].strip()
                if not name:
                    continue

                assignments.append({
                    "id": aid,
                    "name": name,
                    "course_id": course_id,
                    "course_name": course_name,
                    "url": href if href.startswith("http") else f"{BASE_URL}{href}",
                    "due_date": None,
                    "submission_status": "unknown",
                    "grading_status": "unknown",
                    "grade": None,
                    "time_remaining": "",
                    "submitted_files": [],
                    "can_submit": True,
                    "description": "",
                })

            logger.info(f"Returning {len(assignments)} assignments for course {course_id}")
            return assignments

        except Exception as e:
            logger.error(f"Error getting assignments for course {course_id}: {e}", exc_info=True)
            return []
        finally:
            await page.close()

    async def _get_assignment_detail(self, page: Page, assignment: Dict) -> Dict:
        """Get full details of a single assignment."""
        await page.goto(assignment["url"], wait_until="domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(800)

        result = dict(assignment)
        result.update({
            "due_date": None,
            "submission_status": "not_submitted",
            "grading_status": "not_graded",
            "grade": None,
            "time_remaining": "",
            "submitted_files": [],
            "can_submit": False,
            "description": "",
        })

        # Parse status table
        rows = await page.query_selector_all("table.generaltable tr")
        for row in rows:
            cells = await row.query_selector_all("td, th")
            if len(cells) < 2:
                continue
            label = (await cells[0].inner_text()).strip().lower()
            value = (await cells[1].inner_text()).strip()

            if "due date" in label:
                result["due_date"] = parse_date(value)
            elif "submission status" in label:
                result["submission_status"] = value.lower().replace(" ", "_")
            elif "grading status" in label:
                result["grading_status"] = value.lower().replace(" ", "_")
            elif "grade" in label and "grading" not in label:
                m = re.search(r"([\d.]+)\s*/\s*([\d.]+)", value)
                if m:
                    result["grade"] = float(m.group(1))
                    result["max_grade"] = float(m.group(2))
            elif "time remaining" in label:
                result["time_remaining"] = value
            elif "file submissions" in label:
                # Extract submitted file names
                file_links = await cells[1].query_selector_all("a")
                for fl in file_links:
                    fname = (await fl.inner_text()).strip()
                    if fname:
                        result["submitted_files"].append(fname)

        # Description
        desc_el = await page.query_selector(".box.generalbox .no-overflow, .box.generalbox p")
        if desc_el:
            result["description"] = (await desc_el.inner_text()).strip()[:500]

        # Check if submission is possible
        add_btn = await page.query_selector(
            'a:has-text("Add submission"), '
            'a:has-text("Edit submission"), '
            'a[href*="editsubmission"]'
        )
        result["can_submit"] = add_btn is not None
        if add_btn:
            result["submit_btn_text"] = (await add_btn.inner_text()).strip()

        return result

    # ── Submit Assignment ─────────────────────────────────────────────────────

    async def submit_assignment_file(
        self,
        assignment_id: int,
        file_path: str,
        online_text: str = "",
    ) -> Dict:
        """
        Submit a file to an assignment.

        Args:
            assignment_id: Moodle assignment cmid
            file_path: Local path to the file to upload
            online_text: Optional text submission

        Returns:
            dict with success, message
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return {"success": False, "message": f"File not found: {file_path}"}

        page = await self.ctx.new_page()
        try:
            # Navigate to assignment
            assign_url = f"{BASE_URL}/mod/assign/view.php?id={assignment_id}"
            await page.goto(assign_url, wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(1_000)

            # Click "Add submission" or "Edit submission"
            add_btn = await page.query_selector(
                'a:has-text("Add submission"), '
                'a:has-text("Edit submission"), '
                'a[href*="editsubmission"]'
            )
            if not add_btn:
                return {"success": False, "message": "No submission button found — assignment may be closed or already submitted"}

            async with page.expect_navigation():
                await add_btn.click()
            await page.wait_for_timeout(2_000)

            logger.info(f"Submission form URL: {page.url}")

            # Get the draft item ID for file upload
            draft_input = await page.query_selector('input[name="files_filemanager"]')
            if not draft_input:
                return {"success": False, "message": "File manager input not found"}

            draft_id = await draft_input.get_attribute("value")
            sesskey_input = await page.query_selector('input[name="sesskey"]')
            sesskey = await sesskey_input.get_attribute("value") if sesskey_input else ""

            logger.info(f"Draft ID: {draft_id}, Sesskey: {sesskey}")

            # Upload file via Moodle's file picker
            # Method: use the file input that appears when clicking "Add file" in filemanager
            # First try direct file input approach
            file_input = await page.query_selector('input[type="file"]')

            if file_input:
                # Direct file input available
                await file_input.set_input_files(str(file_path))
                await page.wait_for_timeout(2_000)
                logger.info(f"File set via direct input: {file_path.name}")
            else:
                # Use Moodle's repository upload API
                upload_result = await self._upload_file_via_api(
                    page, draft_id, sesskey, file_path
                )
                if not upload_result["success"]:
                    return upload_result
                logger.info(f"File uploaded via API: {file_path.name}")

            # Fill online text if provided
            if online_text:
                text_editor = await page.query_selector(
                    '.editor_atto_content[contenteditable="true"], '
                    'textarea[name*="onlinetext"]'
                )
                if text_editor:
                    await text_editor.click()
                    await text_editor.fill(online_text)
                    await page.wait_for_timeout(500)

            # Submit the form
            save_btn = await page.query_selector('input[name="submitbutton"][value="Save changes"]')
            if not save_btn:
                save_btn = await page.query_selector('input[type="submit"][value="Save changes"]')

            if not save_btn:
                return {"success": False, "message": "Save button not found"}

            await save_btn.click()
            await page.wait_for_load_state("domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(2_000)

            # Verify submission
            current_url = page.url
            if "editsubmission" not in current_url:
                # Check for success indicators
                status_el = await page.query_selector("table.generaltable")
                if status_el:
                    status_text = (await status_el.inner_text()).strip()
                    if "submitted" in status_text.lower():
                        logger.info(f"Assignment {assignment_id} submitted successfully")
                        return {"success": True, "message": "Assignment submitted successfully"}

            # Check for error messages
            error_el = await page.query_selector(".alert-danger, .error")
            if error_el:
                error_text = (await error_el.inner_text()).strip()
                return {"success": False, "message": f"Submission error: {error_text}"}

            return {"success": True, "message": "Submission completed"}

        except Exception as e:
            logger.error(f"Error submitting assignment {assignment_id}: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
        finally:
            await page.close()

    async def _upload_file_via_api(
        self, page: Page, draft_id: str, sesskey: str, file_path: Path
    ) -> Dict:
        """Upload a file to Moodle's draft file area via the repository API."""
        try:
            # Click the "Add file" button in the file manager
            add_file_btn = await page.query_selector(
                '.fp-btn-add, button.fp-btn-add, [title="Add..."], '
                'a.fp-btn-add, .filemanager .fp-btn-add'
            )
            if add_file_btn:
                await add_file_btn.click()
                await page.wait_for_timeout(1_000)

                # File picker dialog should open
                # Look for "Upload a file" tab
                upload_tab = await page.query_selector(
                    '[data-tabname="upload"], '
                    'a:has-text("Upload a file"), '
                    '.fp-repo-area a[href*="upload"]'
                )
                if upload_tab:
                    await upload_tab.click()
                    await page.wait_for_timeout(500)

                # Find file input in the dialog
                file_input = await page.query_selector(
                    '.fp-upload-form input[type="file"], '
                    'input[name="repo_upload_file"]'
                )
                if file_input:
                    await file_input.set_input_files(str(file_path))
                    await page.wait_for_timeout(500)

                    # Click upload button
                    upload_btn = await page.query_selector(
                        '.fp-upload-btn, button:has-text("Upload this file")'
                    )
                    if upload_btn:
                        await upload_btn.click()
                        await page.wait_for_timeout(3_000)
                        return {"success": True, "message": "File uploaded"}

            return {"success": False, "message": "Could not find file upload interface"}
        except Exception as e:
            return {"success": False, "message": f"Upload error: {e}"}

    # ── Grades ────────────────────────────────────────────────────────────────

    async def get_grades_overview(self) -> List[Dict]:
        """Get grade overview for all courses."""
        page = await self.ctx.new_page()
        grades = []
        try:
            await page.goto(
                f"{BASE_URL}/grade/report/overview/index.php",
                wait_until="domcontentloaded",
                timeout=20_000,
            )
            await page.wait_for_timeout(1_000)

            rows = await page.query_selector_all("table.generaltable tbody tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) < 2:
                    continue
                link = await cells[0].query_selector("a")
                name = (await link.inner_text()).strip() if link else (await cells[0].inner_text()).strip()
                href = (await link.get_attribute("href")) if link else ""
                cid_match = re.search(r"id=(\d+)", href or "")
                cid = int(cid_match.group(1)) if cid_match else 0
                grade_str = (await cells[1].inner_text()).strip()

                try:
                    grade_val = float(grade_str.replace("%", "").strip())
                except ValueError:
                    grade_val = None

                if name:
                    grades.append({
                        "course_id": cid,
                        "course_name": name,
                        "grade": grade_val,
                        "grade_str": grade_str,
                    })

            return grades
        finally:
            await page.close()

    async def get_course_grades(self, course_id: int) -> List[Dict]:
        """Get detailed grade report for a specific course."""
        page = await self.ctx.new_page()
        grades = []
        try:
            await page.goto(
                f"{BASE_URL}/grade/report/user/index.php?id={course_id}",
                wait_until="domcontentloaded",
                timeout=20_000,
            )
            await page.wait_for_timeout(1_000)

            rows = await page.query_selector_all("table tr")
            for row in rows:
                cells = await row.query_selector_all("td, th")
                if len(cells) < 2:
                    continue
                item = (await cells[0].inner_text()).strip()
                grade = (await cells[1].inner_text()).strip() if len(cells) > 1 else ""
                max_g = (await cells[2].inner_text()).strip() if len(cells) > 2 else ""
                pct = (await cells[3].inner_text()).strip() if len(cells) > 3 else ""

                if item and item not in ("Grade item", "Calculated weight"):
                    def safe_float(s):
                        try:
                            return float(s.replace("%", "").replace("-", "").strip() or "nan")
                        except ValueError:
                            return None

                    grades.append({
                        "course_id": course_id,
                        "item_name": item,
                        "grade": safe_float(grade),
                        "max_grade": safe_float(max_g),
                        "percentage": safe_float(pct),
                    })

            return grades
        finally:
            await page.close()

    # ── Calendar / Events ─────────────────────────────────────────────────────

    async def get_upcoming_events(self) -> List[Dict]:
        """Get upcoming calendar events."""
        page = await self.ctx.new_page()
        events = []
        try:
            await page.goto(
                f"{BASE_URL}/calendar/view.php?view=upcoming",
                wait_until="domcontentloaded",
                timeout=20_000,
            )
            await page.wait_for_timeout(1_500)

            event_els = await page.query_selector_all(".event")
            for el in event_els:
                # Event name
                name_el = await el.query_selector(".referer a, h3 a, .name a")
                name = (await name_el.inner_text()).strip() if name_el else ""
                href = (await name_el.get_attribute("href")) if name_el else ""

                # Date
                date_el = await el.query_selector("time")
                date_str = ""
                if date_el:
                    date_str = await date_el.get_attribute("datetime") or await date_el.inner_text()

                # Course
                course_el = await el.query_selector(".course a, [data-region='course-name']")
                course_name = (await course_el.inner_text()).strip() if course_el else ""

                # Event type
                event_type = "other"
                if href:
                    if "assign" in href:
                        event_type = "assignment_due"
                    elif "quiz" in href:
                        event_type = "quiz"
                    elif "attendance" in href:
                        event_type = "attendance"

                # Full text for context
                full_text = (await el.inner_text()).strip()

                if name or full_text:
                    events.append({
                        "name": name or full_text.split("\n")[0],
                        "event_type": event_type,
                        "course_name": course_name,
                        "date_str": date_str,
                        "date": parse_date(date_str),
                        "url": href if href.startswith("http") else (f"{BASE_URL}{href}" if href else ""),
                        "full_text": full_text[:200],
                    })

            return events
        finally:
            await page.close()

    # ── Announcements ─────────────────────────────────────────────────────────

    async def get_announcements(self, course_id: int) -> List[Dict]:
        """Get announcements from a course's forum."""
        page = await self.ctx.new_page()
        announcements = []
        try:
            await page.goto(
                f"{BASE_URL}/course/view.php?id={course_id}",
                wait_until="domcontentloaded",
                timeout=20_000,
            )
            await page.wait_for_timeout(800)

            forum_links = await page.query_selector_all('a[href*="/mod/forum/view.php"]')
            for link in forum_links:
                text = (await link.inner_text()).strip().lower()
                if "announcement" in text or "news" in text:
                    href = await link.get_attribute("href") or ""
                    forum_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                    await page.goto(forum_url, wait_until="domcontentloaded", timeout=15_000)
                    await page.wait_for_timeout(500)

                    rows = await page.query_selector_all("table.forumheaderlist tbody tr.discussion")
                    for row in rows:
                        title_el = await row.query_selector("td.topic a")
                        title = (await title_el.inner_text()).strip() if title_el else ""
                        href2 = (await title_el.get_attribute("href")) if title_el else ""

                        author_el = await row.query_selector("td.author a")
                        author = (await author_el.inner_text()).strip() if author_el else ""

                        date_el = await row.query_selector("td.lastpost time")
                        date_str = ""
                        if date_el:
                            date_str = await date_el.get_attribute("datetime") or await date_el.inner_text()

                        if title:
                            announcements.append({
                                "course_id": course_id,
                                "title": title,
                                "author": author,
                                "date_str": date_str,
                                "date": parse_date(date_str),
                                "url": href2 if href2.startswith("http") else f"{BASE_URL}{href2}",
                            })
                    break

            return announcements
        finally:
            await page.close()

    # ── Attendance ────────────────────────────────────────────────────────────

    async def get_attendance(self, course_id: int) -> Dict:
        """Get attendance record for a course."""
        page = await self.ctx.new_page()
        try:
            await page.goto(
                f"{BASE_URL}/course/view.php?id={course_id}",
                wait_until="domcontentloaded",
                timeout=20_000,
            )
            await page.wait_for_timeout(500)

            attend_links = await page.query_selector_all('a[href*="/mod/attendance/view.php"]')
            if not attend_links:
                return {"course_id": course_id, "records": []}

            href = await attend_links[0].get_attribute("href") or ""
            attend_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            await page.goto(attend_url, wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(1_000)

            records = []
            rows = await page.query_selector_all("table.generaltable tbody tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 3:
                    date_str = (await cells[0].inner_text()).strip()
                    status = (await cells[1].inner_text()).strip()
                    records.append({"date": date_str, "status": status})

            # Summary
            summary_el = await page.query_selector(".attendancesummary, .generaltable")
            summary = {}
            if summary_el:
                summary_text = (await summary_el.inner_text()).strip()
                pct_match = re.search(r"(\d+\.?\d*)\s*%", summary_text)
                if pct_match:
                    summary["percentage"] = float(pct_match.group(1))

            return {"course_id": course_id, "records": records, "summary": summary}
        finally:
            await page.close()

    # ── Full Scrape ───────────────────────────────────────────────────────────

    async def scrape_all(self) -> Dict[str, Any]:
        """Scrape all available data from the LMS."""
        logger.info("Starting full LMS scrape...")
        result = {}

        # Profile
        result["profile"] = await self.get_profile()
        logger.info(f"Profile: {result['profile']}")

        # Courses
        courses = await self.get_courses()
        result["courses"] = courses
        logger.info(f"Courses: {len(courses)}")

        # Grades overview
        result["grades_overview"] = await self.get_grades_overview()

        # Calendar
        result["upcoming_events"] = await self.get_upcoming_events()
        logger.info(f"Events: {len(result['upcoming_events'])}")

        # Per-course data
        result["assignments"] = []
        result["announcements"] = []
        result["attendance"] = []
        result["course_grades"] = []

        for course in courses:
            cid = course["id"]
            logger.info(f"Scraping course {cid}: {course['name'][:40]}")

            # Assignments
            try:
                assigns = await self.get_assignments(cid)
                result["assignments"].extend(assigns)
            except Exception as e:
                logger.warning(f"Assignments error for {cid}: {e}")

            # Announcements
            try:
                anns = await self.get_announcements(cid)
                result["announcements"].extend(anns)
            except Exception as e:
                logger.warning(f"Announcements error for {cid}: {e}")

            # Detailed grades
            try:
                cg = await self.get_course_grades(cid)
                result["course_grades"].extend(cg)
            except Exception as e:
                logger.warning(f"Course grades error for {cid}: {e}")

        logger.info(
            f"Scrape complete: {len(result['assignments'])} assignments, "
            f"{len(result['announcements'])} announcements, "
            f"{len(result['course_grades'])} grade items"
        )
        return result
