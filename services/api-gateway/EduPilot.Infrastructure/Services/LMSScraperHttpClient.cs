using System.Net.Http.Json;
using EduPilot.Domain.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace EduPilot.Infrastructure.Services;

public class LMSScraperHttpClient : ILMSScraperService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<LMSScraperHttpClient> _logger;

    public LMSScraperHttpClient(HttpClient httpClient, IConfiguration configuration, ILogger<LMSScraperHttpClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
        _httpClient.BaseAddress = new Uri(configuration["MicroserviceUrls:LMSScraper"] ?? "http://localhost:8002");
        _httpClient.Timeout = TimeSpan.FromSeconds(10);
    }

    public async Task<bool> TriggerScrapingAsync(Guid studentId, string lmsUsername, string lmsPassword, CancellationToken cancellationToken = default)
    {
        try
        {
            var request = new
            {
                studentId,
                lmsUsername,
                lmsPassword
            };

            var response = await _httpClient.PostAsJsonAsync("/api/scrape", request, cancellationToken);
            
            if (response.IsSuccessStatusCode)
            {
                _logger.LogInformation("Successfully triggered LMS scraping for student {StudentId}", studentId);
                return true;
            }

            _logger.LogWarning("Failed to trigger LMS scraping for student {StudentId}. Status: {StatusCode}", 
                studentId, response.StatusCode);
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error triggering LMS scraping for student {StudentId}", studentId);
            return false;
        }
    }

    public async Task<ScrapingStatus> GetScrapingStatusAsync(Guid studentId, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.GetFromJsonAsync<ScrapingStatusResponse>(
                $"/api/scrape/status/{studentId}", cancellationToken);

            return response?.Status ?? ScrapingStatus.Unknown;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting scraping status for student {StudentId}", studentId);
            return ScrapingStatus.Unknown;
        }
    }
}

public class ScrapingStatusResponse
{
    public ScrapingStatus Status { get; set; }
    public DateTime? LastScrapedAt { get; set; }
    public string? ErrorMessage { get; set; }
}

public enum ScrapingStatus
{
    Unknown,
    Pending,
    InProgress,
    Completed,
    Failed
}
