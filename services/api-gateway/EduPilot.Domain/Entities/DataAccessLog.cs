using EduPilot.Domain.Common;

namespace EduPilot.Domain.Entities;

/// <summary>
/// Represents a log entry for data access (FERPA compliance)
/// </summary>
public class DataAccessLog : BaseEntity
{
    public Guid Id { get; private set; }
    public Guid StudentId { get; private set; }
    public Guid? AccessedByUserId { get; private set; }
    public string AccessedByEmail { get; private set; }
    public string ResourceType { get; private set; }
    public Guid ResourceId { get; private set; }
    public string Action { get; private set; }
    public string IpAddress { get; private set; }
    public string UserAgent { get; private set; }
    public DateTime AccessedAt { get; private set; }
    public string Purpose { get; private set; }

    private DataAccessLog() { } // EF Core

    private DataAccessLog(
        Guid studentId,
        Guid? accessedByUserId,
        string accessedByEmail,
        string resourceType,
        Guid resourceId,
        string action,
        string ipAddress,
        string userAgent,
        string purpose)
    {
        Id = Guid.NewGuid();
        StudentId = studentId;
        AccessedByUserId = accessedByUserId;
        AccessedByEmail = accessedByEmail;
        ResourceType = resourceType;
        ResourceId = resourceId;
        Action = action;
        IpAddress = ipAddress;
        UserAgent = userAgent;
        AccessedAt = DateTime.UtcNow;
        Purpose = purpose;
    }

    public static DataAccessLog Create(
        Guid studentId,
        Guid? accessedByUserId,
        string accessedByEmail,
        string resourceType,
        Guid resourceId,
        string action,
        string ipAddress,
        string userAgent,
        string purpose = "Student access")
    {
        if (studentId == Guid.Empty)
            throw new ArgumentException("Student ID cannot be empty", nameof(studentId));

        if (string.IsNullOrWhiteSpace(accessedByEmail))
            throw new ArgumentException("Accessed by email cannot be empty", nameof(accessedByEmail));

        if (string.IsNullOrWhiteSpace(resourceType))
            throw new ArgumentException("Resource type cannot be empty", nameof(resourceType));

        if (resourceId == Guid.Empty)
            throw new ArgumentException("Resource ID cannot be empty", nameof(resourceId));

        if (string.IsNullOrWhiteSpace(action))
            throw new ArgumentException("Action cannot be empty", nameof(action));

        return new DataAccessLog(
            studentId,
            accessedByUserId,
            accessedByEmail,
            resourceType,
            resourceId,
            action,
            ipAddress ?? "Unknown",
            userAgent ?? "Unknown",
            purpose);
    }
}
