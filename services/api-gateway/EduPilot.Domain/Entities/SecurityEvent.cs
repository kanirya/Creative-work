using EduPilot.Domain.Common;

namespace EduPilot.Domain.Entities;

/// <summary>
/// Represents a security event (attempted attacks, suspicious activity)
/// </summary>
public class SecurityEvent : BaseEntity
{
    public Guid Id { get; private set; }
    public string EventType { get; private set; }
    public string Severity { get; private set; }
    public string IpAddress { get; private set; }
    public string UserAgent { get; private set; }
    public string RequestPath { get; private set; }
    public string RequestMethod { get; private set; }
    public string Payload { get; private set; }
    public string DetectionRule { get; private set; }
    public bool Blocked { get; private set; }
    public DateTime OccurredAt { get; private set; }
    public string Details { get; private set; }

    private SecurityEvent() { } // EF Core

    private SecurityEvent(
        string eventType,
        string severity,
        string ipAddress,
        string userAgent,
        string requestPath,
        string requestMethod,
        string payload,
        string detectionRule,
        bool blocked,
        string details)
    {
        Id = Guid.NewGuid();
        EventType = eventType;
        Severity = severity;
        IpAddress = ipAddress;
        UserAgent = userAgent;
        RequestPath = requestPath;
        RequestMethod = requestMethod;
        Payload = payload;
        DetectionRule = detectionRule;
        Blocked = blocked;
        OccurredAt = DateTime.UtcNow;
        Details = details;
    }

    public static SecurityEvent Create(
        string eventType,
        string severity,
        string ipAddress,
        string userAgent,
        string requestPath,
        string requestMethod,
        string payload,
        string detectionRule,
        bool blocked,
        string details)
    {
        if (string.IsNullOrWhiteSpace(eventType))
            throw new ArgumentException("Event type cannot be empty", nameof(eventType));

        if (string.IsNullOrWhiteSpace(severity))
            throw new ArgumentException("Severity cannot be empty", nameof(severity));

        return new SecurityEvent(
            eventType,
            severity,
            ipAddress ?? "Unknown",
            userAgent ?? "Unknown",
            requestPath ?? "/",
            requestMethod ?? "UNKNOWN",
            payload,
            detectionRule,
            blocked,
            details);
    }

    public static class EventTypes
    {
        public const string SqlInjection = "SQL_INJECTION";
        public const string XssAttempt = "XSS_ATTEMPT";
        public const string UnauthorizedAccess = "UNAUTHORIZED_ACCESS";
        public const string BruteForce = "BRUTE_FORCE";
        public const string SuspiciousActivity = "SUSPICIOUS_ACTIVITY";
    }

    public static class Severities
    {
        public const string Low = "LOW";
        public const string Medium = "MEDIUM";
        public const string High = "HIGH";
        public const string Critical = "CRITICAL";
    }
}
