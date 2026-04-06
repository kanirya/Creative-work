"""
Moodle scrapers for Iqra University LMS.

All selectors are based on standard Moodle HTML structure (Academi theme).
See docs/moodle-structure.md for full selector reference.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from playwright.async_api import BrowserContext, Page

from app.config import get_settings
from app.models import (
    AnnouncementData,
    AssignmentData,
    CourseData,
    GradeData,
    QuizData,
    ScheduleEvent,
)
from app.utils.retry import retry_on_lms_error

logger = logging.getLogger(__name__)
settings = get_settings()

BASE_URL = "https://lms.iqra.edu.pk"

# ── Date parsing ──────────────────────────────────────────────────────────────

MOODLE_DATE_FORMATS = [
    "%A, %d %B %Y, %I:%M %p",   # Sunday, 15 December 2024, 11:59 PM
    "%A, %d %B %Y, %H:%M",      # Sunday, 15 December 2024, 23:59
    "%d %B %Y, %I:%M %p",       # 15 December 2024, 11:59 PM
    "%d %B %Y",                  # 15 December 2024
]


def parse_moodle_date(date_str: str) -> Optional[datetime]:
    """Parse a Moodle date string into a datetime object."""
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in MOODLE_DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    # Try ISO format from datetime attributes
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        pass
    logger.debug(f"Could not parse date: {date_str!r}")
    return None


# ── Main Scraper Class ────────────────────────────────────────────────────────


class MoodleScrapers:
    """
    Scrapes all student data from Iqra University Moodle LMS.
    Requires an authenticated BrowserContext from LMSAuthService.
    """

    def __init__(self, context: BrowserContext):
        self.context = context

    # ── Courses ───────────────────────────────────────────────────────────────

    @retry_on_lms_error(max_attempts=3)
    async def scrape_courses(self) -> List[CourseData]:
        """Scrape enrolled courses from the Moodle dashboard."""
        logger.info("Scraping courses from dashboard")
        courses: List[CourseData] = []

        page = await self.context.new_page()
        try:
            await page.goto(f"{BASE_URL}/my/", wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(2_000)

            # Try multiple selectors for course cards (Moodle / Academi theme)
            course_links = await page.query_selector_all(
                'a[href*="/course/view.php?id="]'
            )

            seen_ids = set()
            for link in course_links:
                try:
                    href = await link.get_attribute("href") or ""
                    match = re.search(r"id=(\d+)", href)
                    if not match:
                        continue
                    course_id = int(match.group(1))
                    if course_id in seen_ids:
                        continue
                    seen_ids.add(course_id)

                    name = (await link.inner_text()).strip()
                    if not name:
                        continue

                    courses.append(
                        CourseData(
                            course_id=course_id,
                            course_code=self._extract_course_code(name),
                            course_name=name,
                            url=href if href.startswith("http") else f"{BASE_URL}{href}",
                        )
                    )
                except Exception as e:
                    logger.debug(f"Error extracting course link: {e}")
                    continue

            # Enrich each course with details from its page
            enriched = []
            for course in courses:
                try:
                    enriched.append(await self._enrich_course(page, course))
                except Exception as e:
                    logger.warning(f"Could not enrich course {course.course_id}: {e}")
                    enriched.append(course)

            logger.info(f"Scraped {len(enriched)} courses")
            return enriched

        except Exception as e:
            logger.error(f"Error scraping courses: {e}", exc_info=True)
            return courses
        finally:
            await page.close()

    async def _enrich_course(self, page: Page, course: CourseData) -> CourseData:
        """Fetch course page to get instructor and semester info."""
        await page.goto(
            f"{BASE_URL}/course/view.php?id={course.course_id}",
            wait_until="domcontentloaded",
            timeout=20_000,
        )
        await page.wait_for_timeout(1_000)

        # Instructor
        instructor_el = await page.query_selector(
            ".teacher a, .course-contacts a, [data-key='participants'] a"
        )
        if instructor_el:
            course.instructor = (await instructor_el.inner_text()).strip()

        # Category / semester from breadcrumb or header
        cat_el = await page.query_selector(".breadcrumb-item:nth-child(2) a, .coursecat")
        if cat_el:
            course.category = (await cat_el.inner_text()).strip()

        return course

    @staticmethod
    def _extract_course_code(course_name: str) -> str:
        """Extract course code from name like 'CS-301: Data Structures'."""
        match = re.match(r"^([A-Z]{2,4}[-\s]?\d{3,4})", course_name)
        return match.group(1) if match else course_name[:20]

    # ── Assignments ───────────────────────────────────────────────────────────

    @retry_on_lms_error(max_attempts=3)
    async def scrape_assignments(self, courses: List[CourseData]) -> List[AssignmentData]:
        """Scrape all assignments across all enrolled courses."""
        logger.info(f"Scraping assignments for {len(courses)} courses")
        assignments: List[AssignmentData] = []

        page = await self.context.new_page()
        try:
            for course in courses:
                try:
                    course_assignments = await self._scrape_course_assignments(page, course)
                    assignments.extend(course_assignments)
                except Exception as e:
                    logger.warning(f"Error scraping assignments for course {course.course_id}: {e}")
                    continue

            logger.info(f"Scraped {len(assignments)} assignments total")
            return assignments
        finally:
            await page.close()

    async def _scrape_course_assignments(
        self, page: Page, course: CourseData
    ) -> List[AssignmentData]:
        """Scrape assignments from a single course's assignment index page."""
        assignments = []
        url = f"{BASE_URL}/mod/assign/index.php?id={course.course_id}"
        await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(1_000)

        # Assignment rows in the index table
        rows = await page.query_selector_all("table.generaltable tbody tr")
        for row in rows:
            try:
                link_el = await row.query_selector("a[href*='/mod/assign/view.php']")
                if not link_el:
                    continue

                title = (await link_el.inner_text()).strip()
                href = await link_el.get_attribute("href") or ""
                assign_url = href if href.startswith("http") else f"{BASE_URL}{href}"

                # Due date cell (usually 3rd column)
                cells = await row.query_selector_all("td")
                due_date_str = ""
                if len(cells) >= 3:
                    due_date_str = (await cells[2].inner_text()).strip()

                # Scrape individual assignment page for full details
                detail = await self._scrape_assignment_detail(page, assign_url, course, title)
                if detail:
                    assignments.append(detail)
                else:
                    assignments.append(
                        AssignmentData(
                            course_id=course.course_id,
                            course_name=course.course_name,
                            title=title,
                            due_date=parse_moodle_date(due_date_str),
                            url=assign_url,
                        )
                    )
            except Exception as e:
                logger.debug(f"Error extracting assignment row: {e}")
                continue

        return assignments

    async def _scrape_assignment_detail(
        self, page: Page, url: str, course: CourseData, title: str
    ) -> Optional[AssignmentData]:
        """Scrape an individual assignment page for full details."""
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(500)

            # Description
            desc_el = await page.query_selector(".box.generalbox .no-overflow, .box.generalbox")
            description = (await desc_el.inner_text()).strip() if desc_el else ""

            # Parse submission status table
            due_date = None
            submission_status = "not_submitted"
            grading_status = "not_graded"
            grade = None
            max_score = 100.0

            rows = await page.query_selector_all("table.generaltable tr")
            for row in rows:
                cells = await row.query_selector_all("td, th")
                if len(cells) < 2:
                    continue
                label = (await cells[0].inner_text()).strip().lower()
                value = (await cells[1].inner_text()).strip()

                if "due date" in label:
                    due_date = parse_moodle_date(value)
                elif "submission status" in label:
                    submission_status = value.lower().replace(" ", "_")
                elif "grading status" in label:
                    grading_status = value.lower().replace(" ", "_")
                elif label == "grade":
                    # e.g. "85.00 / 100.00"
                    grade_match = re.search(r"([\d.]+)\s*/\s*([\d.]+)", value)
                    if grade_match:
                        grade = float(grade_match.group(1))
                        max_score = float(grade_match.group(2))

            return AssignmentData(
                course_id=course.course_id,
                course_name=course.course_name,
                title=title,
                description=description[:2000],  # cap length
                due_date=due_date,
                max_score=max_score,
                submission_status=submission_status,
                grading_status=grading_status,
                grade=grade,
                url=url,
            )
        except Exception as e:
            logger.debug(f"Error scraping assignment detail {url}: {e}")
            return None

    # ── Grades ────────────────────────────────────────────────────────────────

    @retry_on_lms_error(max_attempts=3)
    async def scrape_grades(self, courses: List[CourseData]) -> List[GradeData]:
        """Scrape grades from the grade overview and per-course grade reports."""
        logger.info("Scraping grades")
        grades: List[GradeData] = []

        page = await self.context.new_page()
        try:
            # Overview page
            await page.goto(
                f"{BASE_URL}/grade/report/overview/index.php",
                wait_until="domcontentloaded",
                timeout=20_000,
            )
            await page.wait_for_timeout(1_000)

            rows = await page.query_selector_all("table.generaltable tbody tr")
            for row in rows:
                try:
                    cells = await row.query_selector_all("td")
                    if len(cells) < 2:
                        continue
                    course_link = await cells[0].query_selector("a")
                    course_name = (await course_link.inner_text()).strip() if course_link else ""
                    href = (await course_link.get_attribute("href")) if course_link else ""
                    cid_match = re.search(r"id=(\d+)", href or "")
                    course_id = int(cid_match.group(1)) if cid_match else 0

                    grade_str = (await cells[1].inner_text()).strip()
                    grade_val = None
                    try:
                        grade_val = float(grade_str.replace("%", "").strip())
                    except ValueError:
                        pass

                    grades.append(
                        GradeData(
                            course_id=course_id,
                            course_name=course_name,
                            item_name="Overall Grade",
                            grade=grade_val,
                            max_grade=100.0,
                            percentage=grade_val,
                        )
                    )
                except Exception as e:
                    logger.debug(f"Error extracting grade row: {e}")
                    continue

            # Detailed per-course grades
            for course in courses:
                try:
                    detail_grades = await self._scrape_course_grades(page, course)
                    grades.extend(detail_grades)
                except Exception as e:
                    logger.warning(f"Error scraping grades for course {course.course_id}: {e}")

            logger.info(f"Scraped {len(grades)} grade items")
            return grades
        finally:
            await page.close()

    async def _scrape_course_grades(
        self, page: Page, course: CourseData
    ) -> List[GradeData]:
        """Scrape detailed grade report for a single course."""
        grades = []
        await page.goto(
            f"{BASE_URL}/grade/report/user/index.php?id={course.course_id}",
            wait_until="domcontentloaded",
            timeout=20_000,
        )
        await page.wait_for_timeout(500)

        rows = await page.query_selector_all("table.user-grade tr, table.generaltable tr")
        for row in rows:
            try:
                # Skip header rows
                if await row.query_selector("th.header"):
                    continue

                cells = await row.query_selector_all("td")
                if len(cells) < 2:
                    continue

                item_el = await cells[0].query_selector("th, td")
                item_name = (await cells[0].inner_text()).strip()
                if not item_name or item_name.lower() in ("course total", ""):
                    continue

                grade_str = (await cells[1].inner_text()).strip() if len(cells) > 1 else ""
                max_str = (await cells[2].inner_text()).strip() if len(cells) > 2 else ""
                pct_str = (await cells[3].inner_text()).strip() if len(cells) > 3 else ""
                feedback = (await cells[4].inner_text()).strip() if len(cells) > 4 else ""

                def safe_float(s: str) -> Optional[float]:
                    try:
                        return float(s.replace("%", "").replace("-", "").strip() or "nan")
                    except ValueError:
                        return None

                grades.append(
                    GradeData(
                        course_id=course.course_id,
                        course_name=course.course_name,
                        item_name=item_name,
                        grade=safe_float(grade_str),
                        max_grade=safe_float(max_str),
                        percentage=safe_float(pct_str),
                        feedback=feedback[:500],
                    )
                )
            except Exception as e:
                logger.debug(f"Error extracting grade row: {e}")
                continue

        return grades

    # ── Announcements ─────────────────────────────────────────────────────────

    @retry_on_lms_error(max_attempts=3)
    async def scrape_announcements(self, courses: List[CourseData]) -> List[AnnouncementData]:
        """Scrape announcements from all course forums."""
        logger.info(f"Scraping announcements for {len(courses)} courses")
        announcements: List[AnnouncementData] = []

        page = await self.context.new_page()
        try:
            for course in courses:
                try:
                    course_announcements = await self._scrape_course_announcements(page, course)
                    announcements.extend(course_announcements)
                except Exception as e:
                    logger.warning(f"Error scraping announcements for course {course.course_id}: {e}")
                    continue

            logger.info(f"Scraped {len(announcements)} announcements")
            return announcements
        finally:
            await page.close()

    async def _scrape_course_announcements(
        self, page: Page, course: CourseData
    ) -> List[AnnouncementData]:
        """Find and scrape the Announcements forum for a course."""
        announcements = []

        # Navigate to course page to find the announcements forum link
        await page.goto(
            f"{BASE_URL}/course/view.php?id={course.course_id}",
            wait_until="domcontentloaded",
            timeout=20_000,
        )
        await page.wait_for_timeout(500)

        # Find forum links (announcements forum is usually named "Announcements")
        forum_links = await page.query_selector_all('a[href*="/mod/forum/view.php"]')
        announcement_url = None
        for link in forum_links:
            text = (await link.inner_text()).strip().lower()
            if "announcement" in text or "news" in text:
                href = await link.get_attribute("href") or ""
                announcement_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                break

        if not announcement_url:
            return announcements

        # Scrape the forum
        await page.goto(announcement_url, wait_until="domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(500)

        rows = await page.query_selector_all("table.forumheaderlist tbody tr.discussion")
        for row in rows:
            try:
                title_el = await row.query_selector("td.topic a")
                title = (await title_el.inner_text()).strip() if title_el else ""
                thread_href = (await title_el.get_attribute("href")) if title_el else ""
                thread_url = thread_href if thread_href.startswith("http") else f"{BASE_URL}{thread_href}"

                author_el = await row.query_selector("td.author a")
                author = (await author_el.inner_text()).strip() if author_el else ""

                date_el = await row.query_selector("td.lastpost time")
                date_str = ""
                if date_el:
                    date_str = await date_el.get_attribute("datetime") or await date_el.inner_text()

                # Fetch thread content
                content = await self._fetch_forum_post_content(page, thread_url)

                priority = "high" if any(
                    kw in title.lower() for kw in ["urgent", "important", "critical", "exam"]
                ) else "normal"

                announcements.append(
                    AnnouncementData(
                        course_id=course.course_id,
                        course_name=course.course_name,
                        title=title,
                        content=content,
                        author=author,
                        posted_date=parse_moodle_date(date_str),
                        url=thread_url,
                        priority=priority,
                    )
                )
            except Exception as e:
                logger.debug(f"Error extracting announcement row: {e}")
                continue

        return announcements

    async def _fetch_forum_post_content(self, page: Page, url: str) -> str:
        """Fetch the content of a forum discussion thread."""
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15_000)
            content_el = await page.query_selector(".posting, .post-content-container")
            if content_el:
                return (await content_el.inner_text()).strip()[:3000]
        except Exception:
            pass
        return ""

    # ── Schedule / Calendar ───────────────────────────────────────────────────

    @retry_on_lms_error(max_attempts=3)
    async def scrape_schedule(self) -> List[ScheduleEvent]:
        """Scrape upcoming events from the Moodle calendar."""
        logger.info("Scraping calendar events")
        events: List[ScheduleEvent] = []

        page = await self.context.new_page()
        try:
            await page.goto(
                f"{BASE_URL}/calendar/view.php?view=upcoming",
                wait_until="domcontentloaded",
                timeout=20_000,
            )
            await page.wait_for_timeout(1_000)

            event_els = await page.query_selector_all(".event, [data-region='event-item']")
            for el in event_els:
                try:
                    name_el = await el.query_selector(".referer a, .name a, h3 a")
                    name = (await name_el.inner_text()).strip() if name_el else ""
                    href = (await name_el.get_attribute("href")) if name_el else ""
                    event_url = href if href.startswith("http") else f"{BASE_URL}{href}"

                    date_el = await el.query_selector("time, .date a")
                    date_str = ""
                    if date_el:
                        date_str = await date_el.get_attribute("datetime") or await date_el.inner_text()

                    course_el = await el.query_selector(".course a, [data-region='course-name']")
                    course_name = (await course_el.inner_text()).strip() if course_el else ""

                    # Determine event type from URL
                    event_type = "other"
                    if "assign" in event_url:
                        event_type = "assignment"
                    elif "quiz" in event_url:
                        event_type = "quiz"

                    events.append(
                        ScheduleEvent(
                            event_name=name,
                            event_type=event_type,
                            course_name=course_name,
                            start_datetime=parse_moodle_date(date_str),
                            url=event_url,
                        )
                    )
                except Exception as e:
                    logger.debug(f"Error extracting calendar event: {e}")
                    continue

            logger.info(f"Scraped {len(events)} calendar events")
            return events
        finally:
            await page.close()

    # ── Quizzes ───────────────────────────────────────────────────────────────

    @retry_on_lms_error(max_attempts=3)
    async def scrape_quizzes(self, courses: List[CourseData]) -> List[QuizData]:
        """Scrape quiz activities across all courses."""
        logger.info(f"Scraping quizzes for {len(courses)} courses")
        quizzes: List[QuizData] = []

        page = await self.context.new_page()
        try:
            for course in courses:
                try:
                    course_quizzes = await self._scrape_course_quizzes(page, course)
                    quizzes.extend(course_quizzes)
                except Exception as e:
                    logger.warning(f"Error scraping quizzes for course {course.course_id}: {e}")
                    continue

            logger.info(f"Scraped {len(quizzes)} quizzes")
            return quizzes
        finally:
            await page.close()

    async def _scrape_course_quizzes(
        self, page: Page, course: CourseData
    ) -> List[QuizData]:
        """Scrape quizzes from a course page."""
        quizzes = []
        await page.goto(
            f"{BASE_URL}/course/view.php?id={course.course_id}",
            wait_until="domcontentloaded",
            timeout=20_000,
        )
        await page.wait_for_timeout(500)

        quiz_links = await page.query_selector_all('a[href*="/mod/quiz/view.php"]')
        for link in quiz_links:
            try:
                title = (await link.inner_text()).strip()
                href = await link.get_attribute("href") or ""
                quiz_url = href if href.startswith("http") else f"{BASE_URL}{href}"

                detail = await self._scrape_quiz_detail(page, quiz_url, course, title)
                if detail:
                    quizzes.append(detail)
            except Exception as e:
                logger.debug(f"Error extracting quiz link: {e}")
                continue

        return quizzes

    async def _scrape_quiz_detail(
        self, page: Page, url: str, course: CourseData, title: str
    ) -> Optional[QuizData]:
        """Scrape individual quiz page for details."""
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(500)

            opens_at = closes_at = None
            time_limit = attempts_allowed = None
            attempt_status = "not_attempted"
            best_grade = None

            rows = await page.query_selector_all("table.generaltable tr")
            for row in rows:
                cells = await row.query_selector_all("td, th")
                if len(cells) < 2:
                    continue
                label = (await cells[0].inner_text()).strip().lower()
                value = (await cells[1].inner_text()).strip()

                if "open" in label and "quiz" in label:
                    opens_at = parse_moodle_date(value)
                elif "close" in label and "quiz" in label:
                    closes_at = parse_moodle_date(value)
                elif "time limit" in label:
                    m = re.search(r"(\d+)", value)
                    if m:
                        time_limit = int(m.group(1))
                elif "attempt" in label and "allow" in label:
                    m = re.search(r"(\d+)", value)
                    if m:
                        attempts_allowed = int(m.group(1))
                elif "your best" in label or "grade" in label:
                    m = re.search(r"([\d.]+)", value)
                    if m:
                        best_grade = float(m.group(1))
                        attempt_status = "attempted"

            return QuizData(
                course_id=course.course_id,
                course_name=course.course_name,
                quiz_name=title,
                opens_at=opens_at,
                closes_at=closes_at,
                time_limit=time_limit,
                attempts_allowed=attempts_allowed,
                attempt_status=attempt_status,
                best_grade=best_grade,
                url=url,
            )
        except Exception as e:
            logger.debug(f"Error scraping quiz detail {url}: {e}")
            return None
