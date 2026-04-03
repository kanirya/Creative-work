'use client';

import { ProtectedRoute } from '@/components/ProtectedRoute';
import { DashboardLayout } from '@/components/DashboardLayout';
import { useStudentCourses, useStudentAssignments } from '@edupilot/api-client';
import { Card } from '@edupilot/ui';
import { formatDisplayDate, formatRelativeTime } from '@edupilot/utils';
import type { AssignmentDto, CourseDto } from '@edupilot/types';

export default function DashboardPage() {
  const { data: courses, isLoading: coursesLoading } = useStudentCourses();
  const { data: assignments, isLoading: assignmentsLoading } = useStudentAssignments();

  // Filter upcoming assignments (not submitted and not past due)
  const upcomingAssignments = assignments?.filter(
    (a: AssignmentDto) => a.status !== 'submitted' && new Date(a.dueDate) > new Date()
  ).sort((a: AssignmentDto, b: AssignmentDto) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime());

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-2">Welcome back to EduPilot</p>
          </div>

          {/* Courses Section */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">My Courses</h2>
            {coursesLoading ? (
              <div className="text-gray-600">Loading courses...</div>
            ) : courses && courses.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {courses.map((course: CourseDto) => (
                  <Card key={course.id} className="p-6 hover:shadow-lg transition-shadow">
                    <h3 className="text-lg font-semibold text-gray-900">{course.courseName}</h3>
                    <p className="text-sm text-gray-600 mt-1">{course.courseCode}</p>
                    {course.instructor && (
                      <p className="text-sm text-gray-500 mt-2">
                        Instructor: {course.instructor}
                      </p>
                    )}
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="p-6 text-center text-gray-600">
                No courses found. Data will sync from your LMS shortly.
              </Card>
            )}
          </section>

          {/* Upcoming Assignments Section */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Upcoming Assignments</h2>
            {assignmentsLoading ? (
              <div className="text-gray-600">Loading assignments...</div>
            ) : upcomingAssignments && upcomingAssignments.length > 0 ? (
              <div className="space-y-3">
                {upcomingAssignments.slice(0, 5).map((assignment: AssignmentDto) => (
                  <Card key={assignment.id} className="p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{assignment.title}</h3>
                        <p className="text-sm text-gray-600 mt-1">
                          {assignment.courseCode}
                        </p>
                      </div>
                      <div className="text-right ml-4">
                        <p className="text-sm font-medium text-gray-900">
                          {formatDisplayDate(assignment.dueDate)}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatRelativeTime(assignment.dueDate)}
                        </p>
                      </div>
                    </div>
                    {assignment.description && (
                      <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                        {assignment.description}
                      </p>
                    )}
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="p-6 text-center text-gray-600">
                No upcoming assignments
              </Card>
            )}
          </section>

          {/* Recent Announcements Section */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Recent Announcements</h2>
            <Card className="p-6 text-center text-gray-600">
              Announcements will appear here
            </Card>
          </section>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
