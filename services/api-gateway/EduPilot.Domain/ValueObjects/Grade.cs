using EduPilot.Domain.Common;

namespace EduPilot.Domain.ValueObjects;

public class Grade : ValueObject
{
    public decimal Points { get; private set; }
    public decimal MaxPoints { get; private set; }
    public decimal Percentage => MaxPoints > 0 ? (Points / MaxPoints) * 100 : 0;
    public string LetterGrade => CalculateLetterGrade();

    private Grade(decimal points, decimal maxPoints)
    {
        Points = points;
        MaxPoints = maxPoints;
    }

    public static Grade Create(decimal points, decimal maxPoints)
    {
        if (points < 0)
            throw new ArgumentException("Points cannot be negative", nameof(points));

        if (maxPoints <= 0)
            throw new ArgumentException("Max points must be greater than zero", nameof(maxPoints));

        if (points > maxPoints)
            throw new ArgumentException("Points cannot exceed max points", nameof(points));

        return new Grade(points, maxPoints);
    }

    private string CalculateLetterGrade()
    {
        var percentage = Percentage;

        return percentage switch
        {
            >= 90 => "A",
            >= 80 => "B",
            >= 70 => "C",
            >= 60 => "D",
            _ => "F"
        };
    }

    protected override IEnumerable<object> GetEqualityComponents()
    {
        yield return Points;
        yield return MaxPoints;
    }

    public override string ToString() => $"{Points}/{MaxPoints} ({LetterGrade})";
}
