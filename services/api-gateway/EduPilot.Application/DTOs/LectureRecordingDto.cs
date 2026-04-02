namespace EduPilot.Application.DTOs;

public class LectureRecordingDto
{
    public Guid Id { get; set; }
    public Guid CourseId { get; set; }
    public string Title { get; set; } = string.Empty;
    public DateTime RecordedAt { get; set; }
    public TimeSpan Duration { get; set; }
    public string StorageUrl { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
    public bool HasTranscription { get; set; }
}
