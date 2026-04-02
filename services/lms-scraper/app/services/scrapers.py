from playwright.async_api import BrowserContext, Page
from typing import List, Dict, Any
import logging
from datetime import datetime
from app.config import get_settings
from app.models import CourseData, AssignmentData, AnnouncementData

logger = logging.getLogger(__name__)
settings = get_settings()


class LMSScrapers:
    def __init__(self, context: BrowserContext):
        self.context = context
    
    async def scrape_courses(self) -> List[CourseData]:
        """
        Scrape student courses from LMS
        
        Returns:
            List of CourseData objects
        """
        logger.info("Starting courses scraping")
        courses = []
        
        try:
            page = await self.context.new_page()
            
            # Navigate to courses page
            courses_url = f"{settings.lms_base_url}/courses"
            await page.goto(courses_url, timeout=settings.lms_timeout)
            await page.wait_for_load_state('networkidle')
            
            # Wait for course list to load
            await page.wait_for_selector('.course-item, .course-card, [class*="course"]', timeout=10000)
            
            # Extract course elements
            course_elements = await page.query_selector_all('.course-item, .course-card, [class*="course"]')
            
            for element in course_elements:
                try:
                    # Extract course code
                    code_element = await element.query_selector('[class*="code"], .course-code')
                    course_code = await code_element.inner_text() if code_element else "UNKNOWN"
                    
                    # Extract course name
                    name_element = await element.query_selector('[class*="name"], .course-name, h3, h4')
                    course_name = await name_element.inner_text() if name_element else "Unknown Course"
                    
                    # Extract instructor
                    instructor_element = await element.query_selector('[class*="instructor"], .instructor-name')
                    instructor = await instructor_element.inner_text() if instructor_element else "Unknown"
                    
                    # Extract semester (default to current)
                    semester = "Fall 2024"  # TODO: Extract from LMS
                    
                    # Extract credits (default to 3)
                    credits = 3  # TODO: Extract from LMS
                    
                    courses.append(CourseData(
                        course_code=course_code.strip(),
                        course_name=course_name.strip(),
                        instructor=instructor.strip(),
                        semester=semester,
                        credits=credits
                    ))
                    
                    logger.info(f"Scraped course: {course_code} - {course_name}")
                
                except Exception as e:
                    logger.warning(f"Error extracting course data: {str(e)}")
                    continue
            
            await page.close()
            logger.info(f"Successfully scraped {len(courses)} courses")
            
        except Exception as e:
            logger.error(f"Error scraping courses: {str(e)}", exc_info=True)
        
        return courses
    
    async def scrape_assignments(self) -> List[AssignmentData]:
        """
        Scrape student assignments from LMS
        
        Returns:
            List of AssignmentData objects
        """
        logger.info("Starting assignments scraping")
        assignments = []
        
        try:
            page = await self.context.new_page()
            
            # Navigate to assignments page
            assignments_url = f"{settings.lms_base_url}/assignments"
            await page.goto(assignments_url, timeout=settings.lms_timeout)
            await page.wait_for_load_state('networkidle')
            
            # Wait for assignment list to load
            await page.wait_for_selector('.assignment-item, .assignment-card, [class*="assignment"]', timeout=10000)
            
            # Extract assignment elements
            assignment_elements = await page.query_selector_all('.assignment-item, .assignment-card, [class*="assignment"]')
            
            for element in assignment_elements:
                try:
                    # Extract title
                    title_element = await element.query_selector('[class*="title"], .assignment-title, h3, h4')
                    title = await title_element.inner_text() if title_element else "Unknown Assignment"
                    
                    # Extract description
                    desc_element = await element.query_selector('[class*="description"], .assignment-description, p')
                    description = await desc_element.inner_text() if desc_element else ""
                    
                    # Extract course code
                    course_element = await element.query_selector('[class*="course"], .course-code')
                    course_code = await course_element.inner_text() if course_element else "UNKNOWN"
                    
                    # Extract due date
                    due_date_element = await element.query_selector('[class*="due"], .due-date, [class*="deadline"]')
                    due_date_str = await due_date_element.inner_text() if due_date_element else None
                    
                    # Parse due date (simplified - needs proper parsing)
                    due_date = datetime.utcnow()  # TODO: Parse actual date
                    
                    # Extract max score
                    score_element = await element.query_selector('[class*="points"], .max-score')
                    max_score_str = await score_element.inner_text() if score_element else "100"
                    max_score = float(''.join(filter(str.isdigit, max_score_str)) or "100")
                    
                    # Extract status
                    status_element = await element.query_selector('[class*="status"], .assignment-status')
                    status = await status_element.inner_text() if status_element else "pending"
                    
                    assignments.append(AssignmentData(
                        title=title.strip(),
                        description=description.strip(),
                        course_code=course_code.strip(),
                        due_date=due_date,
                        max_score=max_score,
                        status=status.strip().lower()
                    ))
                    
                    logger.info(f"Scraped assignment: {title}")
                
                except Exception as e:
                    logger.warning(f"Error extracting assignment data: {str(e)}")
                    continue
            
            await page.close()
            logger.info(f"Successfully scraped {len(assignments)} assignments")
            
        except Exception as e:
            logger.error(f"Error scraping assignments: {str(e)}", exc_info=True)
        
        return assignments
    
    async def scrape_announcements(self) -> List[AnnouncementData]:
        """
        Scrape course announcements from LMS
        
        Returns:
            List of AnnouncementData objects
        """
        logger.info("Starting announcements scraping")
        announcements = []
        
        try:
            page = await self.context.new_page()
            
            # Navigate to announcements page
            announcements_url = f"{settings.lms_base_url}/announcements"
            await page.goto(announcements_url, timeout=settings.lms_timeout)
            await page.wait_for_load_state('networkidle')
            
            # Wait for announcement list to load
            await page.wait_for_selector('.announcement-item, .announcement-card, [class*="announcement"]', timeout=10000)
            
            # Extract announcement elements
            announcement_elements = await page.query_selector_all('.announcement-item, .announcement-card, [class*="announcement"]')
            
            for element in announcement_elements:
                try:
                    # Extract title
                    title_element = await element.query_selector('[class*="title"], .announcement-title, h3, h4')
                    title = await title_element.inner_text() if title_element else "Unknown Announcement"
                    
                    # Extract content
                    content_element = await element.query_selector('[class*="content"], .announcement-content, p')
                    content = await content_element.inner_text() if content_element else ""
                    
                    # Extract course code
                    course_element = await element.query_selector('[class*="course"], .course-code')
                    course_code = await course_element.inner_text() if course_element else "GENERAL"
                    
                    # Extract posted date
                    date_element = await element.query_selector('[class*="date"], .posted-date, time')
                    posted_date = datetime.utcnow()  # TODO: Parse actual date
                    
                    # Determine priority based on keywords
                    priority = "normal"
                    if any(keyword in title.lower() for keyword in ["urgent", "important", "critical"]):
                        priority = "high"
                    
                    announcements.append(AnnouncementData(
                        title=title.strip(),
                        content=content.strip(),
                        course_code=course_code.strip(),
                        posted_date=posted_date,
                        priority=priority
                    ))
                    
                    logger.info(f"Scraped announcement: {title}")
                
                except Exception as e:
                    logger.warning(f"Error extracting announcement data: {str(e)}")
                    continue
            
            await page.close()
            logger.info(f"Successfully scraped {len(announcements)} announcements")
            
        except Exception as e:
            logger.error(f"Error scraping announcements: {str(e)}", exc_info=True)
        
        return announcements
    
    async def scrape_grades(self) -> Dict[str, Any]:
        """
        Scrape student grades from LMS
        
        Returns:
            Dictionary with grades data
        """
        logger.info("Starting grades scraping")
        grades = {}
        
        try:
            page = await self.context.new_page()
            
            # Navigate to grades page
            grades_url = f"{settings.lms_base_url}/grades"
            await page.goto(grades_url, timeout=settings.lms_timeout)
            await page.wait_for_load_state('networkidle')
            
            # Wait for grades table to load
            await page.wait_for_selector('table, .grades-table, [class*="grade"]', timeout=10000)
            
            # Extract grades (simplified implementation)
            # TODO: Implement detailed grade extraction
            
            await page.close()
            logger.info("Successfully scraped grades")
            
        except Exception as e:
            logger.error(f"Error scraping grades: {str(e)}", exc_info=True)
        
        return grades
    
    async def scrape_schedule(self) -> Dict[str, Any]:
        """
        Scrape student schedule from LMS
        
        Returns:
            Dictionary with schedule data
        """
        logger.info("Starting schedule scraping")
        schedule = {}
        
        try:
            page = await self.context.new_page()
            
            # Navigate to schedule page
            schedule_url = f"{settings.lms_base_url}/schedule"
            await page.goto(schedule_url, timeout=settings.lms_timeout)
            await page.wait_for_load_state('networkidle')
            
            # Wait for schedule to load
            await page.wait_for_selector('.schedule, .timetable, [class*="schedule"]', timeout=10000)
            
            # Extract schedule (simplified implementation)
            # TODO: Implement detailed schedule extraction
            
            await page.close()
            logger.info("Successfully scraped schedule")
            
        except Exception as e:
            logger.error(f"Error scraping schedule: {str(e)}", exc_info=True)
        
        return schedule
