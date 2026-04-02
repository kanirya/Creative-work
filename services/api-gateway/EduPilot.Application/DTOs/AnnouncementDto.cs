namespace EduPilot.Application.DTOs;

public class AnnouncementDto
{
    public Guid Id { get; set; }
    public Guid CourseId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public DateTime PostedAt { get; set; }
    public string Priority { get; set; } = string.Empty;
    public bool IsUrgent { get; set; }
}
