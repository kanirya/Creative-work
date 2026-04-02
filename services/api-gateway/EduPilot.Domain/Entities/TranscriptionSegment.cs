using EduPilot.Domain.Common;

namespace EduPilot.Domain.Entities;

public class TranscriptionSegment : BaseEntity
{
    public Guid TranscriptionId { get; private set; }
    public TimeSpan StartTime { get; private set; }
    public TimeSpan EndTime { get; private set; }
    public string Text { get; private set; }

    private TranscriptionSegment() { } // For EF Core

    private TranscriptionSegment(
        Guid transcriptionId,
        TimeSpan startTime,
        TimeSpan endTime,
        string text)
    {
        TranscriptionId = transcriptionId;
        StartTime = startTime;
        EndTime = endTime;
        Text = text ?? throw new ArgumentNullException(nameof(text));
    }

    public static TranscriptionSegment Create(
        Guid transcriptionId,
        TimeSpan startTime,
        TimeSpan endTime,
        string text)
    {
        if (transcriptionId == Guid.Empty)
            throw new ArgumentException("Transcription ID cannot be empty", nameof(transcriptionId));

        if (endTime <= startTime)
            throw new ArgumentException("End time must be after start time", nameof(endTime));

        if (string.IsNullOrWhiteSpace(text))
            throw new ArgumentException("Text cannot be empty", nameof(text));

        return new TranscriptionSegment(transcriptionId, startTime, endTime, text);
    }

    public TimeSpan Duration => EndTime - StartTime;
}
