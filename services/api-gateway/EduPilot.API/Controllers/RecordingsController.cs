using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using EduPilot.Domain.Interfaces;

namespace EduPilot.API.Controllers;

/// <summary>
/// Handles lecture recording webhooks from Zoom and Google Meet.
/// </summary>
[ApiController]
[Route("api/v1/recordings")]
[Produces("application/json")]
public class RecordingsController : ControllerBase
{
    private readonly ILogger<RecordingsController> _logger;
    private readonly ISchedulerService _schedulerService;

    public RecordingsController(
        ILogger<RecordingsController> logger,
        ISchedulerService schedulerService)
    {
        _logger = logger;
        _schedulerService = schedulerService;
    }

    /// <summary>
    /// Receive Zoom recording webhook, store metadata, and trigger transcription.
    /// </summary>
    [HttpPost("webhook/zoom")]
    [AllowAnonymous]
    public async Task<IActionResult> ZoomWebhook([FromBody] ZoomWebhookPayload payload)
    {
        if (payload?.Event == null)
            return BadRequest(new { success = false, message = "Invalid webhook payload" });

        _logger.LogInformation("Received Zoom webhook event: {Event}", payload.Event);

        if (payload.Event == "recording.completed" && payload.Payload?.Object != null)
        {
            var recording = payload.Payload.Object;
            _logger.LogInformation("Zoom recording completed: {Topic} (Meeting {MeetingId})",
                recording.Topic, recording.Id);

            // Trigger transcription job via scheduler
            try
            {
                await _schedulerService.TriggerTranscriptionAsync(new TranscriptionJobRequest
                {
                    RecordingId = Guid.NewGuid(),
                    AudioFileUrl = recording.RecordingFiles?.FirstOrDefault()?.DownloadUrl ?? string.Empty,
                    Source = "zoom",
                    Title = recording.Topic,
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to trigger transcription for Zoom recording {MeetingId}", recording.Id);
            }
        }

        return Ok(new { success = true });
    }

    /// <summary>
    /// Receive Google Meet recording webhook, store metadata, and trigger transcription.
    /// </summary>
    [HttpPost("webhook/meet")]
    [AllowAnonymous]
    public async Task<IActionResult> GoogleMeetWebhook([FromBody] GoogleMeetWebhookPayload payload)
    {
        if (payload == null)
            return BadRequest(new { success = false, message = "Invalid webhook payload" });

        _logger.LogInformation("Received Google Meet webhook for recording: {RecordingId}", payload.RecordingId);

        try
        {
            await _schedulerService.TriggerTranscriptionAsync(new TranscriptionJobRequest
            {
                RecordingId = Guid.TryParse(payload.RecordingId, out var id) ? id : Guid.NewGuid(),
                AudioFileUrl = payload.AudioUrl ?? string.Empty,
                Source = "meet",
                Title = payload.Title ?? "Google Meet Recording",
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to trigger transcription for Meet recording {RecordingId}", payload.RecordingId);
        }

        return Ok(new { success = true });
    }
}

// ── Webhook payload models ────────────────────────────────────────────────────

public class ZoomWebhookPayload
{
    public string? Event { get; set; }
    public ZoomWebhookObject? Payload { get; set; }
}

public class ZoomWebhookObject
{
    public ZoomRecordingObject? Object { get; set; }
}

public class ZoomRecordingObject
{
    public string? Id { get; set; }
    public string? Topic { get; set; }
    public List<ZoomRecordingFile>? RecordingFiles { get; set; }
}

public class ZoomRecordingFile
{
    public string? DownloadUrl { get; set; }
    public string? FileType { get; set; }
}

public class GoogleMeetWebhookPayload
{
    public string? RecordingId { get; set; }
    public string? Title { get; set; }
    public string? AudioUrl { get; set; }
    public string? MeetingId { get; set; }
}

public class TranscriptionJobRequest
{
    public Guid RecordingId { get; set; }
    public string AudioFileUrl { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
}
