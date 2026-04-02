using EduPilot.Domain.Common;

namespace EduPilot.Domain.ValueObjects;

public class StudentId : ValueObject
{
    public string Value { get; private set; }

    private StudentId(string value)
    {
        Value = value;
    }

    public static StudentId Create(string studentId)
    {
        if (string.IsNullOrWhiteSpace(studentId))
            throw new ArgumentException("Student ID cannot be empty", nameof(studentId));

        studentId = studentId.Trim().ToUpperInvariant();

        if (studentId.Length < 5 || studentId.Length > 50)
            throw new ArgumentException("Student ID must be between 5 and 50 characters", nameof(studentId));

        return new StudentId(studentId);
    }

    protected override IEnumerable<object> GetEqualityComponents()
    {
        yield return Value;
    }

    public override string ToString() => Value;
}
