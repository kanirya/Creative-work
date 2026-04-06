using EduPilot.Domain.Entities;
using EduPilot.Domain.Interfaces;
using EduPilot.Infrastructure.Persistence;
using Microsoft.Extensions.Logging;

namespace EduPilot.Infrastructure.Services;

/// <summary>
/// FERPA-compliant data access logging service.
/// Logs who accessed which student records, when, and why.
/// </summary>
public class FerpaAuditService : IFerpaAuditService
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ILogger<FerpaAuditService> _logger;

    public FerpaAuditService(ApplicationDbContext dbContext, ILogger<FerpaAuditService> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task LogAccessAsync(
        Guid studentId,
        Guid? accessedByUserId,
        string accessedByEmail,
        string resourceType,
        Guid resourceId,
        string action,
        string ipAddress,
        string userAgent,
        string purpose = "Student access",
        CancellationToken cancellationToken = default)
    {
        try
        {
            var log = DataAccessLog.Create(
                studentId,
                accessedByUserId,
                accessedByEmail,
                resourceType,
                resourceId,
                action,
                ipAddress,
                userAgent,
                purpose);

            _dbContext.DataAccessLogs.Add(log);
            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation(
                "FERPA audit: {Action} on {ResourceType}/{ResourceId} for student {StudentId} by {AccessedByEmail}",
                action, resourceType, resourceId, studentId, accessedByEmail);
        }
        catch (Exception ex)
        {
            // Never let audit logging failures break the main request
            _logger.LogError(ex,
                "Failed to write FERPA audit log for student {StudentId}, resource {ResourceType}/{ResourceId}",
                studentId, resourceType, resourceId);
        }
    }
}
