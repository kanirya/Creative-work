namespace EduPilot.Application.DTOs;

public class CourseDto
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? Instructor { get; set; }
    public string Semester { get; set; } = string.Empty;
    public int CreditHours { get; set; }
    public DateTime CreatedAt { get; set; }
}
