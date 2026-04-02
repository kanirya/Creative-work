using EduPilot.Domain.Common;
using EduPilot.Domain.Enums;
using EduPilot.Domain.ValueObjects;

namespace EduPilot.Domain.Entities;

public class Assignment : BaseEntity
{
    public Guid CourseId { get; private set; }
    public string Title { get; private set; }
    public string? Description { get; private set; }
    public DateTime DueDate { get; private set; }
    public int MaxPoints { get; private set; }
    public Grade? Grade { get; private set; }
    public AssignmentStatus Status { get; private set; }

    private Assignment() { } // For EF Core

    private Assignment(
        Guid courseId,
        string title,
        string? description,
        DateTime dueDate,
        int maxPoints)
    {
        CourseId = courseId;
        Title = title ?? throw new ArgumentNullException(nameof(title));
        Description = description;
        DueDate = dueDate;
        MaxPoints = maxPoints;
        Status = AssignmentStatus.Pending;
    }

    public static Assignment Create(
        Guid courseId,
        string title,
        string? description,
        DateTime dueDate,
        int maxPoints)
    {
        if (courseId == Guid.Empty)
            throw new ArgumentException("Course ID cannot be empty", nameof(courseId));

        if (string.IsNullOrWhiteSpace(title))
            throw new ArgumentException("Title cannot be empty", nameof(title));

        if (maxPoints <= 0)
            throw new ArgumentException("Max points must be greater than zero", nameof(maxPoints));

        return new Assignment(courseId, title, description, dueDate, maxPoints);
    }

    public void Submit()
    {
        if (Status == AssignmentStatus.Graded)
            throw new InvalidOperationException("Cannot submit a graded assignment");

        Status = DateTime.UtcNow > DueDate ? AssignmentStatus.Late : AssignmentStatus.Submitted;
        UpdateTimestamp();
    }

    public void SetGrade(decimal points)
    {
        Grade = ValueObjects.Grade.Create(points, MaxPoints);
        Status = AssignmentStatus.Graded;
        UpdateTimestamp();
    }

    public bool IsOverdue => DateTime.UtcNow > DueDate && Status == AssignmentStatus.Pending;

    public TimeSpan TimeUntilDue => DueDate - DateTime.UtcNow;
}
