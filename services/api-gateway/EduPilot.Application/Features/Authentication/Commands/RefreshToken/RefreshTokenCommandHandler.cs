using AutoMapper;
using EduPilot.Application.Common;
using EduPilot.Application.DTOs;
using EduPilot.Domain.Interfaces;
using MediatR;
using Microsoft.Extensions.Logging;

namespace EduPilot.Application.Features.Authentication.Commands.RefreshToken;

public class RefreshTokenCommandHandler : IRequestHandler<RefreshTokenCommand, Result<LoginResponse>>
{
    private readonly IStudentRepository _studentRepository;
    private readonly IAuthenticationService _authenticationService;
    private readonly IMapper _mapper;
    private readonly ILogger<RefreshTokenCommandHandler> _logger;

    public RefreshTokenCommandHandler(
        IStudentRepository studentRepository,
        IAuthenticationService authenticationService,
        IMapper mapper,
        ILogger<RefreshTokenCommandHandler> logger)
    {
        _studentRepository = studentRepository;
        _authenticationService = authenticationService;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<Result<LoginResponse>> Handle(RefreshTokenCommand request, CancellationToken cancellationToken)
    {
        try
        {
            var refreshResult = await _authenticationService.RefreshTokenAsync(request.RefreshToken, cancellationToken);

            if (!refreshResult.Success)
            {
                _logger.LogWarning("Token refresh failed");
                return Result<LoginResponse>.Failure(refreshResult.ErrorMessage ?? "Token refresh failed");
            }

            // Get student by ID from the refresh result (assuming the service returns student ID)
            // For now, we'll return a simplified response
            var response = new LoginResponse
            {
                AccessToken = refreshResult.AccessToken,
                RefreshToken = refreshResult.RefreshToken,
                ExpiresAt = refreshResult.ExpiresAt,
                Student = new StudentDto() // Will be populated from token claims
            };

            _logger.LogInformation("Token refreshed successfully");
            return Result<LoginResponse>.Success(response);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error refreshing token");
            return Result<LoginResponse>.Failure("An error occurred while refreshing token");
        }
    }
}
