using FluentValidation;

namespace EduPilot.Application.Features.Authentication.Commands.AuthenticateStudent;

public class AuthenticateStudentCommandValidator : AbstractValidator<AuthenticateStudentCommand>
{
    public AuthenticateStudentCommandValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty().WithMessage("Email is required")
            .EmailAddress().WithMessage("Invalid email format");

        RuleFor(x => x.Password)
            .NotEmpty().WithMessage("Password is required")
            .MinimumLength(6).WithMessage("Password must be at least 6 characters");
    }
}
