namespace EduPilot.Domain.Interfaces;

public interface ISchedulerService
{
    Task<bool> ScheduleScrapingJobAsync(Guid studentId, string cronExpression, CancellationToken cancellationToken = default);
    Task<bool> CancelJobAsync(Guid jobId, CancellationToken cancellationToken = default);
    Task<List<JobInfo>> GetJobsForStudentAsync(Guid studentId, CancellationToken cancellationToken = default);
}

public class JobInfo
{
    public Guid JobId { get; set; }
    public string JobType { get; set; } = string.Empty;
    public string CronExpression { get; set; } = string.Empty;
    public DateTime? NextRunTime { get; set; }
    public DateTime? LastRunTime { get; set; }
    public string Status { get; set; } = string.Empty;
}
