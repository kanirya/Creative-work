namespace EduPilot.Application.DTOs;

public class StudentDto
{
    public Guid Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public string FirstName { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public string UniversityId { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
    public DateTime EnrolledAt { get; set; }
    public bool IsActive { get; set; }
}
