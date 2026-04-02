using EduPilot.Domain.Common;
using EduPilot.Domain.ValueObjects;

namespace EduPilot.Domain.Entities;

public class Student : BaseEntity
{
    public Email Email { get; private set; }
    public string PasswordHash { get; private set; }
    public string FirstName { get; private set; }
    public string LastName { get; private set; }
    public StudentId UniversityId { get; private set; }
    public DateTime EnrolledAt { get; private set; }
    public bool IsActive { get; private set; }

    private readonly List<Course> _courses = new();
    public IReadOnlyCollection<Course> Courses => _courses.AsReadOnly();

    private readonly List<LectureRecording> _recordings = new();
    public IReadOnlyCollection<LectureRecording> Recordings => _recordings.AsReadOnly();

    private Student() { } // For EF Core

    private Student(
        Email email,
        string passwordHash,
        string firstName,
        string lastName,
        StudentId universityId,
        DateTime enrolledAt)
    {
        Email = email ?? throw new ArgumentNullException(nameof(email));
        PasswordHash = passwordHash ?? throw new ArgumentNullException(nameof(passwordHash));
        FirstName = firstName ?? throw new ArgumentNullException(nameof(firstName));
        LastName = lastName ?? throw new ArgumentNullException(nameof(lastName));
        UniversityId = universityId ?? throw new ArgumentNullException(nameof(universityId));
        EnrolledAt = enrolledAt;
        IsActive = true;
    }

    public static Student Create(
        Email email,
        string passwordHash,
        string firstName,
        string lastName,
        StudentId universityId)
    {
        if (string.IsNullOrWhiteSpace(firstName))
            throw new ArgumentException("First name cannot be empty", nameof(firstName));

        if (string.IsNullOrWhiteSpace(lastName))
            throw new ArgumentException("Last name cannot be empty", nameof(lastName));

        return new Student(email, passwordHash, firstName, lastName, universityId, DateTime.UtcNow);
    }

    public void UpdatePassword(string newPasswordHash)
    {
        if (string.IsNullOrWhiteSpace(newPasswordHash))
            throw new ArgumentException("Password hash cannot be empty", nameof(newPasswordHash));

        PasswordHash = newPasswordHash;
        UpdateTimestamp();
    }

    public void UpdateProfile(string firstName, string lastName)
    {
        if (string.IsNullOrWhiteSpace(firstName))
            throw new ArgumentException("First name cannot be empty", nameof(firstName));

        if (string.IsNullOrWhiteSpace(lastName))
            throw new ArgumentException("Last name cannot be empty", nameof(lastName));

        FirstName = firstName;
        LastName = lastName;
        UpdateTimestamp();
    }

    public void Deactivate()
    {
        IsActive = false;
        UpdateTimestamp();
    }

    public void Activate()
    {
        IsActive = true;
        UpdateTimestamp();
    }

    public void EnrollInCourse(Course course)
    {
        if (course == null)
            throw new ArgumentNullException(nameof(course));

        if (_courses.Any(c => c.Id == course.Id))
            return; // Already enrolled

        _courses.Add(course);
        UpdateTimestamp();
    }

    public string FullName => $"{FirstName} {LastName}";
}
