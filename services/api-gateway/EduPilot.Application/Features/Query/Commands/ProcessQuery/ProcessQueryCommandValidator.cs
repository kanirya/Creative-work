using FluentValidation;

namespace EduPilot.Application.Features.Query.Commands.ProcessQuery;

public class ProcessQueryCommandValidator : AbstractValidator<ProcessQueryCommand>
{
    public ProcessQueryCommandValidator()
    {
        RuleFor(x => x.StudentId)
            .NotEmpty().WithMessage("Student ID is required");

        RuleFor(x => x.Query)
            .NotEmpty().WithMessage("Query is required")
            .MaximumLength(1000).WithMessage("Query must not exceed 1000 characters")
            .When(x => x.Type.Equals("text", StringComparison.OrdinalIgnoreCase));

        RuleFor(x => x.AudioData)
            .NotNull().WithMessage("Audio data is required for voice queries")
            .When(x => x.Type.Equals("voice", StringComparison.OrdinalIgnoreCase));

        RuleFor(x => x.Type)
            .Must(type => type.Equals("text", StringComparison.OrdinalIgnoreCase) || 
                         type.Equals("voice", StringComparison.OrdinalIgnoreCase))
            .WithMessage("Type must be either 'text' or 'voice'");
    }
}
