using EduPilot.Domain.Interfaces;
using EduPilot.Domain.ValueObjects;
using Microsoft.Extensions.Configuration;
using Microsoft.IdentityModel.Tokens;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;

namespace EduPilot.Infrastructure.Services;

public class AuthenticationService : IAuthenticationService
{
    private readonly IConfiguration _configuration;
    private readonly ICacheService _cacheService;

    public AuthenticationService(IConfiguration configuration, ICacheService cacheService)
    {
        _configuration = configuration;
        _cacheService = cacheService;
    }

    public async Task<AuthenticationResult> AuthenticateAsync(Email email, string password, CancellationToken cancellationToken = default)
    {
        // This method assumes password verification has already been done
        // Generate JWT tokens
        var accessToken = GenerateAccessToken(email.Value, Guid.NewGuid());
        var refreshToken = GenerateRefreshToken();
        var expiresAt = DateTime.UtcNow.AddMinutes(GetAccessTokenExpiryMinutes());

        // Store refresh token in cache
        await _cacheService.SetAsync(
            $"refresh_token:{refreshToken}",
            new { Email = email.Value, CreatedAt = DateTime.UtcNow },
            TimeSpan.FromDays(GetRefreshTokenExpiryDays()),
            cancellationToken);

        return new AuthenticationResult
        {
            Success = true,
            AccessToken = accessToken,
            RefreshToken = refreshToken,
            ExpiresAt = expiresAt
        };
    }

    public async Task<bool> ValidateTokenAsync(string token, CancellationToken cancellationToken = default)
    {
        try
        {
            var tokenHandler = new JwtSecurityTokenHandler();
            var key = Encoding.UTF8.GetBytes(GetSecretKey());

            tokenHandler.ValidateToken(token, new TokenValidationParameters
            {
                ValidateIssuerSigningKey = true,
                IssuerSigningKey = new SymmetricSecurityKey(key),
                ValidateIssuer = true,
                ValidIssuer = GetIssuer(),
                ValidateAudience = true,
                ValidAudience = GetAudience(),
                ValidateLifetime = true,
                ClockSkew = TimeSpan.Zero
            }, out _);

            return true;
        }
        catch
        {
            return false;
        }
    }

    public async Task<RefreshTokenResult> RefreshTokenAsync(string refreshToken, CancellationToken cancellationToken = default)
    {
        var tokenData = await _cacheService.GetAsync<dynamic>($"refresh_token:{refreshToken}", cancellationToken);

        if (tokenData == null)
        {
            return new RefreshTokenResult
            {
                Success = false,
                ErrorMessage = "Invalid refresh token"
            };
        }

        // Generate new tokens
        var email = tokenData.Email.ToString();
        var accessToken = GenerateAccessToken(email, Guid.NewGuid());
        var newRefreshToken = GenerateRefreshToken();
        var expiresAt = DateTime.UtcNow.AddMinutes(GetAccessTokenExpiryMinutes());

        // Remove old refresh token and store new one
        await _cacheService.RemoveAsync($"refresh_token:{refreshToken}", cancellationToken);
        await _cacheService.SetAsync(
            $"refresh_token:{newRefreshToken}",
            new { Email = email, CreatedAt = DateTime.UtcNow },
            TimeSpan.FromDays(GetRefreshTokenExpiryDays()),
            cancellationToken);

        return new RefreshTokenResult
        {
            Success = true,
            AccessToken = accessToken,
            RefreshToken = newRefreshToken,
            ExpiresAt = expiresAt
        };
    }

    public async Task RevokeTokenAsync(string refreshToken, CancellationToken cancellationToken = default)
    {
        await _cacheService.RemoveAsync($"refresh_token:{refreshToken}", cancellationToken);
    }

    public string HashPassword(string password)
    {
        return BCrypt.Net.BCrypt.HashPassword(password, workFactor: 12);
    }

    public bool VerifyPassword(string password, string passwordHash)
    {
        try
        {
            // Log for debugging
            Console.WriteLine($"Verifying password. Hash starts with: {passwordHash.Substring(0, Math.Min(10, passwordHash.Length))}");
            var result = BCrypt.Net.BCrypt.Verify(password, passwordHash);
            Console.WriteLine($"Verification result: {result}");
            return result;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"BCrypt verification error: {ex.Message}");
            // Try with enhanced entropy for older hash formats
            try
            {
                return BCrypt.Net.BCrypt.Verify(password, passwordHash, enhancedEntropy: true);
            }
            catch
            {
                return false;
            }
        }
    }

    private string GenerateAccessToken(string email, Guid studentId)
    {
        var tokenHandler = new JwtSecurityTokenHandler();
        var key = Encoding.UTF8.GetBytes(GetSecretKey());

        var tokenDescriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity(new[]
            {
                new Claim(ClaimTypes.Email, email),
                new Claim(ClaimTypes.NameIdentifier, studentId.ToString()),
                new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString())
            }),
            Expires = DateTime.UtcNow.AddMinutes(GetAccessTokenExpiryMinutes()),
            Issuer = GetIssuer(),
            Audience = GetAudience(),
            SigningCredentials = new SigningCredentials(
                new SymmetricSecurityKey(key),
                SecurityAlgorithms.HmacSha256Signature)
        };

        var token = tokenHandler.CreateToken(tokenDescriptor);
        return tokenHandler.WriteToken(token);
    }

    private string GenerateRefreshToken()
    {
        return Guid.NewGuid().ToString("N") + Guid.NewGuid().ToString("N");
    }

    private string GetSecretKey() => _configuration["JwtSettings:SecretKey"] ?? throw new InvalidOperationException("JWT secret key not configured");
    private string GetIssuer() => _configuration["JwtSettings:Issuer"] ?? "EduPilot";
    private string GetAudience() => _configuration["JwtSettings:Audience"] ?? "EduPilot";
    private int GetAccessTokenExpiryMinutes() => int.Parse(_configuration["JwtSettings:AccessTokenExpiryMinutes"] ?? "15");
    private int GetRefreshTokenExpiryDays() => int.Parse(_configuration["JwtSettings:RefreshTokenExpiryDays"] ?? "7");
}
