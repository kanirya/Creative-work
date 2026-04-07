using System.Collections.Concurrent;

namespace EduPilot.Infrastructure.Services;

public enum CircuitState { Closed, Open, HalfOpen }

public record CircuitBreakerStatus(
    string ServiceName,
    CircuitState State,
    int FailureCount,
    DateTime? LastFailureAt,
    DateTime? OpenedAt
);

/// <summary>
/// Tracks circuit breaker state per downstream service.
/// Exposed via health endpoint for observability.
/// </summary>
public class CircuitBreakerStateService
{
    private readonly ConcurrentDictionary<string, CircuitBreakerStatus> _states = new();

    public void RecordFailure(string serviceName)
    {
        _states.AddOrUpdate(
            serviceName,
            _ => new CircuitBreakerStatus(serviceName, CircuitState.Closed, 1, DateTime.UtcNow, null),
            (_, existing) =>
            {
                var newCount = existing.FailureCount + 1;
                var state = newCount >= 5 ? CircuitState.Open : existing.State;
                var openedAt = state == CircuitState.Open && existing.State != CircuitState.Open
                    ? DateTime.UtcNow
                    : existing.OpenedAt;
                return existing with { FailureCount = newCount, LastFailureAt = DateTime.UtcNow, State = state, OpenedAt = openedAt };
            });
    }

    public void RecordSuccess(string serviceName)
    {
        _states.AddOrUpdate(
            serviceName,
            _ => new CircuitBreakerStatus(serviceName, CircuitState.Closed, 0, null, null),
            (_, existing) => existing with { State = CircuitState.Closed, FailureCount = 0, OpenedAt = null });
    }

    public void SetHalfOpen(string serviceName)
    {
        if (_states.TryGetValue(serviceName, out var existing))
        {
            _states[serviceName] = existing with { State = CircuitState.HalfOpen };
        }
    }

    public CircuitBreakerStatus? GetStatus(string serviceName)
        => _states.TryGetValue(serviceName, out var status) ? status : null;

    public IReadOnlyDictionary<string, CircuitBreakerStatus> GetAllStatuses()
        => _states;
}
