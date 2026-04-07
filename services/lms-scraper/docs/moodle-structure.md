# Iqra University LMS — Moodle Page Structure

## Platform
- **LMS**: Moodle (theme: Academi)
- **Base URL**: `https://lms.iqra.edu.pk`

## Key URLs

| Page | URL Pattern |
|---|---|
| Dashboard | `/my/` |
| My Courses | `/my/courses.php` (dedicated courses page — use this, not `/my/`) |
| Course Page | `/course/view.php?id=<courseid>` |
| Assignments | `/mod/assign/view.php?id=<cmid>` |
| Assignment List | `/mod/assign/index.php?id=<courseid>` |
| Grades Overview | `/grade/report/overview/index.php` |
| Course Grades | `/grade/report/user/index.php?id=<courseid>` |
| Forum/Announcements | `/mod/forum/view.php?id=<cmid>` |
| Calendar | `/calendar/view.php?view=month` |
| Quiz | `/mod/quiz/view.php?id=<cmid>` |
| Profile | `/user/profile.php` |

## Dashboard Structure

```html
<!-- My Courses block -->
<div data-region="myoverview">
  <div data-region="courses-view">
    <div data-region="course-content">
      <!-- Course cards -->
      <div data-region="course-item" data-course-id="123">
        <div class="coursename">
          <a href="/course/view.php?id=123">Course Full Name</a>
        </div>
        <div class="coursecat">Category Name</div>
      </div>
    </div>
  </div>
</div>

<!-- Alternative: course list view -->
<div class="course-info-container">
  <h3 class="coursename">
    <a href="/course/view.php?id=123">Course Name</a>
  </h3>
</div>
```

## Course Page Structure

```html
<!-- Course header -->
<div id="page-header">
  <h1 class="h2">Course Full Name</h1>
</div>

<!-- Course sections with activities -->
<ul class="section img-text">
  <li class="activity assign modtype_assign">
    <div class="activityinstance">
      <a href="/mod/assign/view.php?id=456">
        <span class="instancename">Assignment Title</span>
      </a>
    </div>
  </li>
  <li class="activity forum modtype_forum">
    <div class="activityinstance">
      <a href="/mod/forum/view.php?id=789">
        <span class="instancename">Announcements</span>
      </a>
    </div>
  </li>
  <li class="activity quiz modtype_quiz">
    <div class="activityinstance">
      <a href="/mod/quiz/view.php?id=101">
        <span class="instancename">Quiz Title</span>
      </a>
    </div>
  </li>
</ul>
```

## Assignment Page Structure

```html
<!-- Assignment details -->
<div class="box generalbox">
  <div class="no-overflow">
    <!-- Assignment description HTML -->
  </div>
</div>

<!-- Submission status table -->
<table class="generaltable">
  <tr>
    <td>Due date</td>
    <td>Sunday, 15 December 2024, 11:59 PM</td>
  </tr>
  <tr>
    <td>Submission status</td>
    <td>No attempt</td>  <!-- or "Submitted for grading" -->
  </tr>
  <tr>
    <td>Grading status</td>
    <td>Not graded</td>  <!-- or "Graded" -->
  </tr>
  <tr>
    <td>Grade</td>
    <td>85.00 / 100.00</td>
  </tr>
</table>
```

## Grades Page Structure

```html
<!-- Grade overview table -->
<table class="generaltable">
  <thead>
    <tr>
      <th>Course name</th>
      <th>Grade</th>
      <th>Percentage</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><a href="/course/view.php?id=123">Course Name</a></td>
      <td>85.50</td>
      <td>85.50 %</td>
    </tr>
  </tbody>
</table>

<!-- Detailed grade report (per course) -->
<table class="user-grade">
  <tr class="leveleven">
    <th scope="row">Assignment 1</th>
    <td>85.00</td>
    <td>100.00</td>
    <td>85.00 %</td>
    <td>-</td>  <!-- feedback -->
  </tr>
</table>
```

## Forum/Announcements Structure

```html
<!-- Forum discussion list -->
<table class="forumheaderlist">
  <tbody>
    <tr class="discussion">
      <td class="topic starter">
        <a href="/mod/forum/discuss.php?d=123">Announcement Title</a>
      </td>
      <td class="author">
        <a href="/user/view.php?id=456">Instructor Name</a>
      </td>
      <td class="lastpost">
        <a href="...">
          <time datetime="2024-12-01T10:00:00+05:00">1 December 2024</time>
        </a>
      </td>
    </tr>
  </tbody>
</table>
```

## Calendar Structure

```html
<!-- Calendar events -->
<div class="eventlist">
  <div class="event">
    <div class="referer">
      <a href="/mod/assign/view.php?id=456">Assignment Due: Assignment Title</a>
    </div>
    <div class="date">
      <a href="...">Sunday, 15 December 2024</a>
    </div>
    <div class="course">
      <a href="/course/view.php?id=123">Course Name</a>
    </div>
  </div>
</div>
```

## Moodle Date Format

Moodle uses this date format throughout:
- Full: `"Sunday, 15 December 2024, 11:59 PM"`
- Short: `"15 December 2024"`
- ISO (in `datetime` attributes): `"2024-12-15T23:59:00+05:00"`

Python parsing:
```python
from datetime import datetime

# Full format
datetime.strptime("Sunday, 15 December 2024, 11:59 PM", "%A, %d %B %Y, %I:%M %p")

# Short format  
datetime.strptime("15 December 2024", "%d %B %Y")
```

## Moodle Session

After login, all requests must include:
- Cookie: `MoodleSession=<token>`
- This is automatically handled by Playwright's browser context
