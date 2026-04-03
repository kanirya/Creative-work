using System.Net.Http.Json;
using EduPilot.Domain.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace EduPilot.Infrastructure.Services;

public class TranscriptionHttpClient : ITranscriptionService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<TranscriptionHttpClient> _logger;

    public TranscriptionHttpClient(HttpClient httpClient, IConfiguration configuration, ILogger<TranscriptionHttpClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
        _httpClient.BaseAddress = new Uri(configuration["ServiceUrls:TranscriptionService"] ?? "http://localhost:8003");
        _httpClient.Timeout = TimeSpan.FromSeconds(10);
    }

    public async Task<bool> QueueTranscriptionAsync(Guid recordingId, string audioFileUrl, CancellationToken cancellationToken = default)
    {
        try
        {
            var request = new
            {
                recordingId,
                audioFileUrl
            };

            var response = await _httpClient.PostAsJsonAsync("/api/transcribe/queue", request, cancellationToken);
            
            if (response.IsSuccessStatusCode)
            {
                _logger.LogInformation("Successfully queued transcription for recording {RecordingId}", recordingId);
                return true;
            }

            _logger.LogWarning("Failed to queue transcription for recording {RecordingId}. Status: {StatusCode}", 
                recordingId, response.StatusCode);
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error queuing transcription for recording {RecordingId}", recordingId);
            return false;
        }
    }

    public async Task<TranscriptionStatus> GetTranscriptionStatusAsync(Guid recordingId, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.GetFromJsonAsync<TranscriptionStatusResponse>(
                $"/api/transcribe/status/{recordingId}", cancellationToken);

            return response?.Status ?? TranscriptionStatus.Unknown;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting transcription status for recording {RecordingId}", recordingId);
            return TranscriptionStatus.Unknown;
        }
    }

    public async Task<string?> GetTranscriptionTextAsync(Guid recordingId, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.GetFromJsonAsync<TranscriptionTextResponse>(
                $"/api/transcribe/{recordingId}", cancellationToken);

            return response?.Text;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting transcription text for recording {RecordingId}", recordingId);
            return null;
        }
    }
}

public class TranscriptionStatusResponse
{
    public TranscriptionStatus Status { get; set; }
    public DateTime? CompletedAt { get; set; }
    public string? ErrorMessage { get; set; }
}

public class TranscriptionTextResponse
{
    public string Text { get; set; } = string.Empty;
    public List<TranscriptionSegment> Segments { get; set; } = new();
}

public class TranscriptionSegment
{
    public string Text { get; set; } = string.Empty;
    public double StartTime { get; set; }
    public double EndTime { get; set; }
}
