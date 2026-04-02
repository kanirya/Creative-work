using EduPilot.Application.Common;
using EduPilot.Application.DTOs;

namespace EduPilot.Application.Features.Authentication.Commands.AuthenticateStudent;

public class AuthenticateStudentCommand : BaseCommand<Result<LoginResponse>>
{
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}
