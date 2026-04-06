using System.Text.RegularExpressions;
using EduPilot.Domain.Entities;
using EduPilot.Infrastructure.Persistence;
using Microsoft.Extensions.Logging;

namespace EduPilot.API.Middleware;

/// <summary>
/// Middleware for detecting and blocking security threats (SQL injection, XSS, etc.)
/// </summary>
public class SecurityMonitoringMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<SecurityMonitoringMiddleware> _logger;

    // SQL Injection patterns
    private static readonly Regex[] SqlInjectionPatterns = new[]
    {
        new Regex(@"(\bUNION\b.*\bSELECT\b)", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"(\bSELECT\b.*\bFROM\b.*\bWHERE\b)", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"(\bINSERT\b.*\bINTO\b.*\bVALUES\b)", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"(\bDELETE\b.*\bFROM\b)", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"(\bDROP\b.*\bTABLE\b)", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"(\bEXEC\b|\bEXECUTE\b)", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"(--|;|\/\*|\*\/)", RegexOptions.Compiled),
        new Regex(@"('.*OR.*'.*=.*')", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"(1=1|1\s*=\s*1)", RegexOptions.IgnoreCase | RegexOptions.Compiled)
    };

    // XSS patterns
    private static readonly Regex[] XssPatterns = new[]
    {
        new Regex(@"<script[^>]*>.*?</script>", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"javascript:", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"on\w+\s*=", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"<iframe[^>]*>", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"<object[^>]*>", RegexOptions.IgnoreCase | RegexOptions.Compiled),
        new Regex(@"<embed[^>]*>", RegexOptions.IgnoreCase | RegexOptions.Compiled)
    };

    public SecurityMonitoringMiddleware(
        RequestDelegate next,
        ILogger<SecurityMonitoringMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context, ApplicationDbContext dbContext)
    {
        // Read request body
        context.Request.EnableBuffering();
        var requestBody = await ReadRequestBodyAsync(context.Request);

        // Check query string
        var queryString = context.Request.QueryString.ToString();

        // Detect SQL injection
        if (DetectSqlInjection(queryString) || DetectSqlInjection(requestBody))
        {
            await LogAndBlockRequest(
                context,
                dbContext,
                SecurityEvent.EventTypes.SqlInjection,
                SecurityEvent.Severities.High,
                "SQL injection pattern detected",
                $"Query: {queryString}, Body: {TruncateString(requestBody, 500)}");
            return;
        }

        // Detect XSS
        if (DetectXss(queryString) || DetectXss(requestBody))
        {
            await LogAndBlockRequest(
                context,
                dbContext,
                SecurityEvent.EventTypes.XssAttempt,
                SecurityEvent.Severities.High,
                "XSS pattern detected",
                $"Query: {queryString}, Body: {TruncateString(requestBody, 500)}");
            return;
        }

        // Reset request body position for next middleware
        context.Request.Body.Position = 0;

        await _next(context);
    }

    private async Task<string> ReadRequestBodyAsync(HttpRequest request)
    {
        try
        {
            using var reader = new StreamReader(
                request.Body,
                encoding: System.Text.Encoding.UTF8,
                detectEncodingFromByteOrderMarks: false,
                bufferSize: 1024,
                leaveOpen: true);

            var body = await reader.ReadToEndAsync();
            request.Body.Position = 0;
            return body;
        }
        catch
        {
            return string.Empty;
        }
    }

    private bool DetectSqlInjection(string input)
    {
        if (string.IsNullOrEmpty(input))
            return false;

        return SqlInjectionPatterns.Any(pattern => pattern.IsMatch(input));
    }

    private bool DetectXss(string input)
    {
        if (string.IsNullOrEmpty(input))
            return false;

        return XssPatterns.Any(pattern => pattern.IsMatch(input));
    }

    private async Task LogAndBlockRequest(
        HttpContext context,
        ApplicationDbContext dbContext,
        string eventType,
        string severity,
        string detectionRule,
        string details)
    {
        var ipAddress = context.Connection.RemoteIpAddress?.ToString() ?? "Unknown";
        var userAgent = context.Request.Headers["User-Agent"].ToString();
        var requestPath = context.Request.Path.ToString();
        var requestMethod = context.Request.Method;
        var correlationId = context.Request.Headers["X-Correlation-ID"].FirstOrDefault()
            ?? context.TraceIdentifier;

        // Create security event
        var securityEvent = SecurityEvent.Create(
            eventType,
            severity,
            ipAddress,
            userAgent,
            requestPath,
            requestMethod,
            details,
            detectionRule,
            blocked: true,
            details);

        // Log to database
        try
        {
            dbContext.SecurityEvents.Add(securityEvent);
            await dbContext.SaveChangesAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to log security event to database");
        }

        // Log to application logs with correlation ID, IP, path, and matched pattern
        _logger.LogWarning(
            "Security threat detected and blocked: {EventType} | CorrelationId: {CorrelationId} | IP: {IpAddress} | Path: {RequestPath} | Pattern: {DetectionRule}",
            eventType,
            correlationId,
            ipAddress,
            requestPath,
            detectionRule);

        // Return 400 Bad Request
        context.Response.StatusCode = StatusCodes.Status400BadRequest;
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsJsonAsync(new
        {
            error = "Bad Request",
            message = "Request blocked due to security policy violation",
            correlationId
        });
    }

    private string TruncateString(string input, int maxLength)
    {
        if (string.IsNullOrEmpty(input) || input.Length <= maxLength)
            return input;

        return input.Substring(0, maxLength) + "...";
    }
}

public static class SecurityMonitoringMiddlewareExtensions
{
    public static IApplicationBuilder UseSecurityMonitoring(this IApplicationBuilder builder)
    {
        return builder.UseMiddleware<SecurityMonitoringMiddleware>();
    }
}
