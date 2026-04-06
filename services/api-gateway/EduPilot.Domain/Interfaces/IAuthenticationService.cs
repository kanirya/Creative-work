using EduPilot.Domain.ValueObjects;

namespace EduPilot.Domain.Interfaces;

public interface IAuthenticationService
{
    Task<AuthenticationResult> AuthenticateAsync(Email email, string password, CancellationToken cancellationToken = default);
    Task<AuthenticationResult> AuthenticateAsync(Email email, string password, Guid studentId, IEnumerable<string> roles, CancellationToken cancellationToken = default);
    Task<bool> ValidateTokenAsync(string token, CancellationToken cancellationToken = default);
    Task<RefreshTokenResult> RefreshTokenAsync(string refreshToken, CancellationToken cancellationToken = default);
    Task RevokeTokenAsync(string refreshToken, CancellationToken cancellationToken = default);
    string HashPassword(string password);
    bool VerifyPassword(string password, string passwordHash);
}

public class AuthenticationResult
{
    public string AccessToken { get; set; } = string.Empty;
    public string RefreshToken { get; set; } = string.Empty;
    public DateTime ExpiresAt { get; set; }
    public Guid StudentId { get; set; }
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
}

public class RefreshTokenResult
{
    public string AccessToken { get; set; } = string.Empty;
    public string RefreshToken { get; set; } = string.Empty;
    public DateTime ExpiresAt { get; set; }
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
}
