using FluentValidation;

namespace EduPilot.Application.Features.Students.Queries.GetAssignments;

public class GetAssignmentsQueryValidator : AbstractValidator<GetAssignmentsQuery>
{
    public GetAssignmentsQueryValidator()
    {
        RuleFor(x => x.StudentId)
            .NotEmpty().WithMessage("Student ID is required");

        RuleFor(x => x.DaysAhead)
            .GreaterThan(0).WithMessage("Days ahead must be greater than 0")
            .LessThanOrEqualTo(365).WithMessage("Days ahead must not exceed 365")
            .When(x => x.DaysAhead.HasValue);
    }
}
