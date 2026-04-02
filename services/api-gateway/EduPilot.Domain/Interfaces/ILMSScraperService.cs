namespace EduPilot.Domain.Interfaces;

public interface ILMSScraperService
{
    Task<bool> TriggerScrapingAsync(Guid studentId, string lmsUsername, string lmsPassword, CancellationToken cancellationToken = default);
    Task<ScrapingStatus> GetScrapingStatusAsync(Guid studentId, CancellationToken cancellationToken = default);
}

public enum ScrapingStatus
{
    Unknown,
    Pending,
    InProgress,
    Completed,
    Failed
}
