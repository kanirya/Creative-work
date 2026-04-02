using FluentValidation;

namespace EduPilot.Application.Features.Students.Queries.GetStudentCourses;

public class GetStudentCoursesQueryValidator : AbstractValidator<GetStudentCoursesQuery>
{
    public GetStudentCoursesQueryValidator()
    {
        RuleFor(x => x.StudentId)
            .NotEmpty().WithMessage("Student ID is required");
    }
}
