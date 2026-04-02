using EduPilot.Application.Common;

namespace EduPilot.Application.Features.Authentication.Queries.ValidateToken;

public class ValidateTokenQuery : BaseQuery<Result<bool>>
{
    public string Token { get; set; } = string.Empty;
}
