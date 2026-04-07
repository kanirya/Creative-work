using System.Collections.Concurrent;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace EduPilot.Infrastructure.Services;

public record SyncOperation(Guid StudentId, string DataType, int RetryCount, DateTime NextRetryAt);

/// <summary>
/// In-memory queue for failed sync operations with exponential backoff retry.
/// </summary>
public class SyncRetryQueue : BackgroundService
{
    private readonly ConcurrentQueue<SyncOperation> _queue = new();
    private readonly ILogger<SyncRetryQueue> _logger;
    private const int MaxRetries = 5;

    public SyncRetryQueue(ILogger<SyncRetryQueue> logger)
    {
        _logger = logger;
    }

    public void Enqueue(Guid studentId, string dataType)
    {
        var op = new SyncOperation(studentId, dataType, 0, DateTime.UtcNow);
        _queue.Enqueue(op);
        _logger.LogInformation("Queued sync retry for student {StudentId}, type {DataType}", studentId, dataType);
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("SyncRetryQueue background service started");

        while (!stoppingToken.IsCancellationRequested)
        {
            await ProcessQueueAsync(stoppingToken);
            await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
        }
    }

    private async Task ProcessQueueAsync(CancellationToken cancellationToken)
    {
        var now = DateTime.UtcNow;
        var pending = new List<SyncOperation>();

        // Drain the queue
        while (_queue.TryDequeue(out var op))
        {
            pending.Add(op);
        }

        foreach (var op in pending)
        {
            if (op.NextRetryAt > now)
            {
                // Not ready yet — re-enqueue
                _queue.Enqueue(op);
                continue;
            }

            if (op.RetryCount >= MaxRetries)
            {
                _logger.LogError(
                    "Sync operation for student {StudentId} type {DataType} exceeded max retries ({Max}). Dropping.",
                    op.StudentId, op.DataType, MaxRetries);
                continue;
            }

            try
            {
                await RetrySyncAsync(op, cancellationToken);
                _logger.LogInformation(
                    "Sync retry succeeded for student {StudentId} type {DataType} (attempt {Attempt})",
                    op.StudentId, op.DataType, op.RetryCount + 1);
            }
            catch (Exception ex)
            {
                var nextRetry = op.RetryCount + 1;
                var backoff = TimeSpan.FromSeconds(Math.Pow(2, nextRetry)); // 2, 4, 8, 16, 32s
                var retried = op with { RetryCount = nextRetry, NextRetryAt = now + backoff };

                _logger.LogWarning(ex,
                    "Sync retry failed for student {StudentId} type {DataType} (attempt {Attempt}). Next retry in {Backoff}s",
                    op.StudentId, op.DataType, nextRetry, backoff.TotalSeconds);

                _queue.Enqueue(retried);
            }
        }
    }

    private Task RetrySyncAsync(SyncOperation op, CancellationToken cancellationToken)
    {
        // In a real implementation this would call the LMS scraper or data sync service.
        // For now, log and simulate success.
        _logger.LogInformation("Retrying sync for student {StudentId}, type {DataType}", op.StudentId, op.DataType);
        return Task.CompletedTask;
    }

    public int QueueLength => _queue.Count;
}
