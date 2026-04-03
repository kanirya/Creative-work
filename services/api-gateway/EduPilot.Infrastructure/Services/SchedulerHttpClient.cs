using System.Net.Http.Json;
using EduPilot.Domain.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace EduPilot.Infrastructure.Services;

public class SchedulerHttpClient : ISchedulerService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<SchedulerHttpClient> _logger;

    public SchedulerHttpClient(HttpClient httpClient, IConfiguration configuration, ILogger<SchedulerHttpClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
        _httpClient.BaseAddress = new Uri(configuration["ServiceUrls:SchedulerService"] ?? "http://localhost:8004");
        _httpClient.Timeout = TimeSpan.FromSeconds(10);
    }

    public async Task<bool> ScheduleScrapingJobAsync(Guid studentId, string cronExpression, CancellationToken cancellationToken = default)
    {
        try
        {
            var request = new
            {
                studentId,
                jobType = "scraping",
                cronExpression
            };

            var response = await _httpClient.PostAsJsonAsync("/api/jobs/schedule", request, cancellationToken);
            
            if (response.IsSuccessStatusCode)
            {
                _logger.LogInformation("Successfully scheduled scraping job for student {StudentId}", studentId);
                return true;
            }

            _logger.LogWarning("Failed to schedule scraping job for student {StudentId}. Status: {StatusCode}", 
                studentId, response.StatusCode);
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error scheduling scraping job for student {StudentId}", studentId);
            return false;
        }
    }

    public async Task<bool> CancelJobAsync(Guid jobId, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.DeleteAsync($"/api/jobs/{jobId}", cancellationToken);
            
            if (response.IsSuccessStatusCode)
            {
                _logger.LogInformation("Successfully cancelled job {JobId}", jobId);
                return true;
            }

            _logger.LogWarning("Failed to cancel job {JobId}. Status: {StatusCode}", 
                jobId, response.StatusCode);
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error cancelling job {JobId}", jobId);
            return false;
        }
    }

    public async Task<List<JobInfo>> GetJobsForStudentAsync(Guid studentId, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.GetFromJsonAsync<List<JobInfo>>(
                $"/api/jobs/student/{studentId}", cancellationToken);

            return response ?? new List<JobInfo>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting jobs for student {StudentId}", studentId);
            return new List<JobInfo>();
        }
    }
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
