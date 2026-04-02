using EduPilot.Domain.Common;

namespace EduPilot.Domain.ValueObjects;

public class CourseCode : ValueObject
{
    public string Value { get; private set; }

    private CourseCode(string value)
    {
        Value = value;
    }

    public static CourseCode Create(string code)
    {
        if (string.IsNullOrWhiteSpace(code))
            throw new ArgumentException("Course code cannot be empty", nameof(code));

        code = code.Trim().ToUpperInvariant();

        if (code.Length < 2 || code.Length > 20)
            throw new ArgumentException("Course code must be between 2 and 20 characters", nameof(code));

        return new CourseCode(code);
    }

    protected override IEnumerable<object> GetEqualityComponents()
    {
        yield return Value;
    }

    public override string ToString() => Value;
}
