using EduPilot.Domain.Common;
using EduPilot.Domain.ValueObjects;

namespace EduPilot.Domain.Entities;

public class Course : BaseEntity
{
    public CourseCode Code { get; private set; }
    public string Name { get; private set; }
    public string? Instructor { get; private set; }
    public string Semester { get; private set; }
    public int CreditHours { get; private set; }

    private readonly List<Assignment> _assignments = new();
    public IReadOnlyCollection<Assignment> Assignments => _assignments.AsReadOnly();

    private readonly List<Announcement> _announcements = new();
    public IReadOnlyCollection<Announcement> Announcements => _announcements.AsReadOnly();

    private readonly List<LectureRecording> _recordings = new();
    public IReadOnlyCollection<LectureRecording> Recordings => _recordings.AsReadOnly();

    private Course() { } // For EF Core

    private Course(
        CourseCode code,
        string name,
        string? instructor,
        string semester,
        int creditHours)
    {
        Code = code ?? throw new ArgumentNullException(nameof(code));
        Name = name ?? throw new ArgumentNullException(nameof(name));
        Instructor = instructor;
        Semester = semester ?? throw new ArgumentNullException(nameof(semester));
        CreditHours = creditHours;
    }

    public static Course Create(
        CourseCode code,
        string name,
        string? instructor,
        string semester,
        int creditHours)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Course name cannot be empty", nameof(name));

        if (string.IsNullOrWhiteSpace(semester))
            throw new ArgumentException("Semester cannot be empty", nameof(semester));

        if (creditHours <= 0 || creditHours > 10)
            throw new ArgumentException("Credit hours must be between 1 and 10", nameof(creditHours));

        return new Course(code, name, instructor, semester, creditHours);
    }

    public void UpdateDetails(string name, string? instructor, int creditHours)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Course name cannot be empty", nameof(name));

        if (creditHours <= 0 || creditHours > 10)
            throw new ArgumentException("Credit hours must be between 1 and 10", nameof(creditHours));

        Name = name;
        Instructor = instructor;
        CreditHours = creditHours;
        UpdateTimestamp();
    }

    public void AddAssignment(Assignment assignment)
    {
        if (assignment == null)
            throw new ArgumentNullException(nameof(assignment));

        _assignments.Add(assignment);
        UpdateTimestamp();
    }

    public void AddAnnouncement(Announcement announcement)
    {
        if (announcement == null)
            throw new ArgumentNullException(nameof(announcement));

        _announcements.Add(announcement);
        UpdateTimestamp();
    }

    public void AddRecording(LectureRecording recording)
    {
        if (recording == null)
            throw new ArgumentNullException(nameof(recording));

        _recordings.Add(recording);
        UpdateTimestamp();
    }
}
