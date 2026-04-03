using System.Security.Claims;
using EduPilot.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;

namespace EduPilot.API.Middleware;

/// <summary>
/// Middleware for role-based access control (RBAC)
/// </summary>
public class AuthorizationMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<AuthorizationMiddleware> _logger;

    // Define protected endpoints and required permissions
    private static readonly Dictionary<string, string[]> ProtectedEndpoints = new()
    {
        // Admin endpoints
        { "/api/admin/students", new[] { "admin.students.manage" } },
        { "/api/admin/courses", new[] { "admin.courses.manage" } },
        { "/api/admin/users", new[] { "admin.users.manage" } },
        { "/api/admin/roles", new[] { "admin.roles.manage" } },
        { "/api/admin/permissions", new[] { "admin.permissions.manage" } },
        { "/api/admin/security", new[] { "admin.security.view" } },
        { "/api/admin/logs", new[] { "admin.logs.view" } },
        
        // Data export endpoints (FERPA)
        { "/api/students/{id}/export", new[] { "student.data.export" } },
        { "/api/students/{id}/access-logs", new[] { "student.data.view-logs" } }
    };

    public AuthorizationMiddleware(
        RequestDelegate next,
        ILogger<AuthorizationMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context, ApplicationDbContext dbContext)
    {
        var path = context.Request.Path.ToString().ToLowerInvariant();

        // Check if endpoint requires authorization
        var requiredPermissions = GetRequiredPermissions(path);
        if (requiredPermissions == null || requiredPermissions.Length == 0)
        {
            await _next(context);
            return;
        }

        // Check if user is authenticated
        if (!context.User.Identity?.IsAuthenticated ?? true)
        {
            context.Response.StatusCode = StatusCodes.Status401Unauthorized;
            await context.Response.WriteAsJsonAsync(new
            {
                error = "Unauthorized",
                message = "Authentication required"
            });
            return;
        }

        // Get user ID from claims
        var userIdClaim = context.User.FindFirst(ClaimTypes.NameIdentifier);
        if (userIdClaim == null || !Guid.TryParse(userIdClaim.Value, out var userId))
        {
            context.Response.StatusCode = StatusCodes.Status401Unauthorized;
            await context.Response.WriteAsJsonAsync(new
            {
                error = "Unauthorized",
                message = "Invalid user identity"
            });
            return;
        }

        // Load user with roles and permissions
        var student = await dbContext.Students
            .Include(s => s.Roles)
                .ThenInclude(r => r.Permissions)
            .FirstOrDefaultAsync(s => s.Id == userId);

        if (student == null)
        {
            context.Response.StatusCode = StatusCodes.Status401Unauthorized;
            await context.Response.WriteAsJsonAsync(new
            {
                error = "Unauthorized",
                message = "User not found"
            });
            return;
        }

        // Check if user has required permissions
        var hasPermission = requiredPermissions.Any(permission =>
            student.Roles.Any(role =>
                role.Permissions.Any(p => p.Name == permission)));

        if (!hasPermission)
        {
            _logger.LogWarning(
                "Authorization failed for user {UserId} on endpoint {Path}. Required permissions: {Permissions}",
                userId,
                path,
                string.Join(", ", requiredPermissions));

            context.Response.StatusCode = StatusCodes.Status403Forbidden;
            await context.Response.WriteAsJsonAsync(new
            {
                error = "Forbidden",
                message = "Insufficient permissions to access this resource"
            });
            return;
        }

        await _next(context);
    }

    private string[]? GetRequiredPermissions(string path)
    {
        // Exact match
        if (ProtectedEndpoints.TryGetValue(path, out var permissions))
            return permissions;

        // Pattern match (e.g., /api/students/{id}/export)
        foreach (var (pattern, perms) in ProtectedEndpoints)
        {
            if (MatchesPattern(path, pattern))
                return perms;
        }

        return null;
    }

    private bool MatchesPattern(string path, string pattern)
    {
        // Simple pattern matching for {id} placeholders
        var patternParts = pattern.Split('/');
        var pathParts = path.Split('/');

        if (patternParts.Length != pathParts.Length)
            return false;

        for (int i = 0; i < patternParts.Length; i++)
        {
            if (patternParts[i].StartsWith("{") && patternParts[i].EndsWith("}"))
                continue; // Wildcard match

            if (!patternParts[i].Equals(pathParts[i], StringComparison.OrdinalIgnoreCase))
                return false;
        }

        return true;
    }
}

public static class AuthorizationMiddlewareExtensions
{
    public static IApplicationBuilder UseRoleBasedAuthorization(this IApplicationBuilder builder)
    {
        return builder.UseMiddleware<AuthorizationMiddleware>();
    }
}
