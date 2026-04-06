using EduPilot.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace EduPilot.Infrastructure.Services;

/// <summary>
/// Enforces FERPA data retention policies.
/// FERPA requires institutions to retain education records for a defined period.
/// </summary>
public class DataRetentionService
{
    // FERPA retention periods
    public static class RetentionPolicies
    {
        /// <summary>Data access audit logs retained for 5 years (FERPA requirement)</summary>
        public static readonly TimeSpan DataAccessLogs = TimeSpan.FromDays(5 * 365);

        /// <summary>Security events retained for 1 year</summary>
        public static readonly TimeSpan SecurityEvents = TimeSpan.FromDays(365);

        /// <summary>Transcription segments retained for 3 years</summary>
        public static readonly TimeSpan TranscriptionSegments = TimeSpan.FromDays(3 * 365);
    }

    private readonly ApplicationDbContext _dbContext;
    private readonly ILogger<DataRetentionService> _logger;

    public DataRetentionService(ApplicationDbContext dbContext, ILogger<DataRetentionService> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    /// <summary>
    /// Purge records that have exceeded their retention period.
    /// Should be called by the scheduler service on a daily basis.
    /// </summary>
    public async Task ApplyRetentionPoliciesAsync(CancellationToken cancellationToken = default)
    {
        await PurgeDataAccessLogsAsync(cancellationToken);
        await PurgeSecurityEventsAsync(cancellationToken);
    }

    private async Task PurgeDataAccessLogsAsync(CancellationToken cancellationToken)
    {
        var cutoff = DateTime.UtcNow - RetentionPolicies.DataAccessLogs;
        var deleted = await _dbContext.DataAccessLogs
            .Where(l => l.AccessedAt < cutoff)
            .ExecuteDeleteAsync(cancellationToken);

        if (deleted > 0)
            _logger.LogInformation("FERPA retention: purged {Count} data access log entries older than {Cutoff:yyyy-MM-dd}", deleted, cutoff);
    }

    private async Task PurgeSecurityEventsAsync(CancellationToken cancellationToken)
    {
        var cutoff = DateTime.UtcNow - RetentionPolicies.SecurityEvents;
        var deleted = await _dbContext.SecurityEvents
            .Where(e => e.OccurredAt < cutoff)
            .ExecuteDeleteAsync(cancellationToken);

        if (deleted > 0)
            _logger.LogInformation("Retention: purged {Count} security events older than {Cutoff:yyyy-MM-dd}", deleted, cutoff);
    }
}
