using EduPilot.Application.Common;
using EduPilot.Application.DTOs;

namespace EduPilot.Application.Features.Students.Queries.GetStudentCourses;

public class GetStudentCoursesQuery : BaseQuery<Result<List<CourseDto>>>
{
    public Guid StudentId { get; set; }
}
