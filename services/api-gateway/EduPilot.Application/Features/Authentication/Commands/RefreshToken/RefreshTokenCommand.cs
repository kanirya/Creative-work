using EduPilot.Application.Common;
using EduPilot.Application.DTOs;

namespace EduPilot.Application.Features.Authentication.Commands.RefreshToken;

public class RefreshTokenCommand : BaseCommand<Result<LoginResponse>>
{
    public string RefreshToken { get; set; } = string.Empty;
}
