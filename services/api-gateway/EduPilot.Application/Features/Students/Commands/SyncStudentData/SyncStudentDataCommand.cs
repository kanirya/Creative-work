using EduPilot.Application.Common;

namespace EduPilot.Application.Features.Students.Commands.SyncStudentData;

public class SyncStudentDataCommand : BaseCommand<Result<SyncResult>>
{
    public Guid StudentId { get; set; }
}

public class SyncResult
{
    public bool Success { get; set; }
    public int CoursesUpdated { get; set; }
    public int AssignmentsUpdated { get; set; }
    public int AnnouncementsUpdated { get; set; }
    public DateTime SyncedAt { get; set; }
    public string? ErrorMessage { get; set; }
}
