using System.Collections.Concurrent;
using System.Net;

namespace EduPilot.API.Middleware;

public class RateLimitingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RateLimitingMiddleware> _logger;
    private static readonly ConcurrentDictionary<string, (DateTime WindowStart, int RequestCount)> _requestCounts = new();
    private const int MaxRequestsPerMinute = 100;
    private static readonly TimeSpan WindowDuration = TimeSpan.FromMinutes(1);

    public RateLimitingMiddleware(RequestDelegate next, ILogger<RateLimitingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var studentId = context.User?.FindFirst("student_id")?.Value;
        
        if (string.IsNullOrEmpty(studentId))
        {
            await _next(context);
            return;
        }

        var now = DateTime.UtcNow;
        var key = $"rate_limit:{studentId}";

        var (windowStart, requestCount) = _requestCounts.GetOrAdd(key, _ => (now, 0));

        if (now - windowStart > WindowDuration)
        {
            _requestCounts[key] = (now, 1);
            await _next(context);
            return;
        }

        if (requestCount >= MaxRequestsPerMinute)
        {
            _logger.LogWarning("Rate limit exceeded for student {StudentId}", studentId);
            context.Response.StatusCode = (int)HttpStatusCode.TooManyRequests;
            context.Response.ContentType = "application/json";
            
            var response = new
            {
                success = false,
                message = "Rate limit exceeded. Maximum 100 requests per minute allowed.",
                retryAfter = (int)(WindowDuration - (now - windowStart)).TotalSeconds
            };

            await context.Response.WriteAsJsonAsync(response);
            return;
        }

        _requestCounts[key] = (windowStart, requestCount + 1);
        await _next(context);
    }
}
