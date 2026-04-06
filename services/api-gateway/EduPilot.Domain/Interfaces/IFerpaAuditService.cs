namespace EduPilot.Domain.Interfaces;

/// <summary>
/// Service for FERPA-compliant data access logging
/// </summary>
public interface IFerpaAuditService
{
    /// <summary>
    /// Log access to a student's educational record
    /// </summary>
    Task LogAccessAsync(
        Guid studentId,
        Guid? accessedByUserId,
        string accessedByEmail,
        string resourceType,
        Guid resourceId,
        string action,
        string ipAddress,
        string userAgent,
        string purpose = "Student access",
        CancellationToken cancellationToken = default);
}
