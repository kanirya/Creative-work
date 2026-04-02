namespace EduPilot.Domain.Interfaces;

public interface ITranscriptionService
{
    Task<bool> QueueTranscriptionAsync(Guid recordingId, string audioFileUrl, CancellationToken cancellationToken = default);
    Task<TranscriptionStatus> GetTranscriptionStatusAsync(Guid recordingId, CancellationToken cancellationToken = default);
    Task<string?> GetTranscriptionTextAsync(Guid recordingId, CancellationToken cancellationToken = default);
}

public enum TranscriptionStatus
{
    Unknown,
    Queued,
    Processing,
    Completed,
    Failed
}
