using AutoMapper;
using EduPilot.Application.Common;
using EduPilot.Application.DTOs;
using EduPilot.Domain.Interfaces;
using EduPilot.Domain.ValueObjects;
using MediatR;
using Microsoft.Extensions.Logging;

namespace EduPilot.Application.Features.Authentication.Commands.AuthenticateStudent;

public class AuthenticateStudentCommandHandler : IRequestHandler<AuthenticateStudentCommand, Result<LoginResponse>>
{
    private readonly IStudentRepository _studentRepository;
    private readonly IAuthenticationService _authenticationService;
    private readonly IMapper _mapper;
    private readonly ILogger<AuthenticateStudentCommandHandler> _logger;

    public AuthenticateStudentCommandHandler(
        IStudentRepository studentRepository,
        IAuthenticationService authenticationService,
        IMapper mapper,
        ILogger<AuthenticateStudentCommandHandler> logger)
    {
        _studentRepository = studentRepository;
        _authenticationService = authenticationService;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<Result<LoginResponse>> Handle(AuthenticateStudentCommand request, CancellationToken cancellationToken)
    {
        try
        {
            // Validate email format
            Email email;
            try
            {
                email = Email.Create(request.Email);
            }
            catch (ArgumentException ex)
            {
                _logger.LogWarning("Invalid email format: {Email}", request.Email);
                return Result<LoginResponse>.Failure("Invalid email format");
            }

            // Get student by email
            var student = await _studentRepository.GetByEmailAsync(email, cancellationToken);
            if (student == null)
            {
                _logger.LogWarning("Student not found: {Email}", request.Email);
                return Result<LoginResponse>.Failure("Invalid email or password");
            }

            // Check if student is active
            if (!student.IsActive)
            {
                _logger.LogWarning("Inactive student attempted login: {Email}", request.Email);
                return Result<LoginResponse>.Failure("Account is inactive");
            }

            // Verify password
            if (!_authenticationService.VerifyPassword(request.Password, student.PasswordHash))
            {
                _logger.LogWarning("Invalid password for student: {Email}", request.Email);
                return Result<LoginResponse>.Failure("Invalid email or password");
            }

            // Authenticate and generate tokens
            var authResult = await _authenticationService.AuthenticateAsync(email, request.Password, cancellationToken);
            
            if (!authResult.Success)
            {
                _logger.LogError("Authentication failed for student: {Email}", request.Email);
                return Result<LoginResponse>.Failure(authResult.ErrorMessage ?? "Authentication failed");
            }

            // Map student to DTO
            var studentDto = _mapper.Map<StudentDto>(student);

            var response = new LoginResponse
            {
                AccessToken = authResult.AccessToken,
                RefreshToken = authResult.RefreshToken,
                ExpiresAt = authResult.ExpiresAt,
                Student = studentDto
            };

            _logger.LogInformation("Student authenticated successfully: {Email}", request.Email);
            return Result<LoginResponse>.Success(response);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error authenticating student: {Email}", request.Email);
            return Result<LoginResponse>.Failure("An error occurred during authentication");
        }
    }
}
