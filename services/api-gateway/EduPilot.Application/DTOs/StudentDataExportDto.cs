namespace EduPilot.Application.DTOs;

/// <summary>
/// Complete export of a student's educational records (FERPA data portability)
/// </summary>
public class StudentDataExportDto
{
    public StudentDto Profile { get; set; } = new();
    public List<CourseDto> Courses { get; set; } = new();
    public List<AssignmentDto> Assignments { get; set; } = new();
    public List<AnnouncementDto> Announcements { get; set; } = new();
    public DateTime ExportedAt { get; set; } = DateTime.UtcNow;
    public string ExportVersion { get; set; } = "1.0";
}
