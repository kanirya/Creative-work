using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.SignalR;

namespace EduPilot.API.Hubs;

/// <summary>
/// SignalR hub for real-time student data synchronization across devices.
/// </summary>
[Authorize]
public class StudentDataHub : Hub
{
    private readonly ILogger<StudentDataHub> _logger;

    public StudentDataHub(ILogger<StudentDataHub> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// Join a student-specific group so all devices for that student receive updates.
    /// </summary>
    public async Task JoinStudentGroup(string studentId)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, $"student-{studentId}");
        _logger.LogInformation("Connection {ConnectionId} joined group student-{StudentId}",
            Context.ConnectionId, studentId);
    }

    /// <summary>
    /// Leave a student group.
    /// </summary>
    public async Task LeaveStudentGroup(string studentId)
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"student-{studentId}");
        _logger.LogInformation("Connection {ConnectionId} left group student-{StudentId}",
            Context.ConnectionId, studentId);
    }

    /// <summary>
    /// Broadcast a data update to all connections in a student's group.
    /// </summary>
    public async Task SendDataUpdate(string studentId, string dataType)
    {
        _logger.LogInformation("Broadcasting {DataType} update for student {StudentId}", dataType, studentId);
        await Clients.Group($"student-{studentId}").SendAsync("DataUpdated", new
        {
            studentId,
            dataType,
            timestamp = DateTime.UtcNow
        });
    }

    public override async Task OnConnectedAsync()
    {
        _logger.LogDebug("Client connected: {ConnectionId}", Context.ConnectionId);
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        _logger.LogDebug("Client disconnected: {ConnectionId}", Context.ConnectionId);
        await base.OnDisconnectedAsync(exception);
    }
}
