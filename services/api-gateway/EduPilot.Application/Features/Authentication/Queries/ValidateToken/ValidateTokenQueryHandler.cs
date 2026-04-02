using EduPilot.Application.Common;
using EduPilot.Domain.Interfaces;
using MediatR;
using Microsoft.Extensions.Logging;

namespace EduPilot.Application.Features.Authentication.Queries.ValidateToken;

public class ValidateTokenQueryHandler : IRequestHandler<ValidateTokenQuery, Result<bool>>
{
    private readonly IAuthenticationService _authenticationService;
    private readonly ILogger<ValidateTokenQueryHandler> _logger;

    public ValidateTokenQueryHandler(
        IAuthenticationService authenticationService,
        ILogger<ValidateTokenQueryHandler> logger)
    {
        _authenticationService = authenticationService;
        _logger = logger;
    }

    public async Task<Result<bool>> Handle(ValidateTokenQuery request, CancellationToken cancellationToken)
    {
        try
        {
            var isValid = await _authenticationService.ValidateTokenAsync(request.Token, cancellationToken);
            return Result<bool>.Success(isValid);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error validating token");
            return Result<bool>.Failure("An error occurred while validating token");
        }
    }
}
