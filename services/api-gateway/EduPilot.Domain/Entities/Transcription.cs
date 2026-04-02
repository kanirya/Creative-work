using EduPilot.Domain.Common;

namespace EduPilot.Domain.Entities;

public class Transcription : BaseEntity
{
    public Guid RecordingId { get; private set; }
    public string FullText { get; private set; }
    public string Language { get; private set; }
    public DateTime TranscribedAt { get; private set; }

    private readonly List<TranscriptionSegment> _segments = new();
    public IReadOnlyCollection<TranscriptionSegment> Segments => _segments.AsReadOnly();

    private Transcription() { } // For EF Core

    private Transcription(
        Guid recordingId,
        string fullText,
        string language)
    {
        RecordingId = recordingId;
        FullText = fullText ?? throw new ArgumentNullException(nameof(fullText));
        Language = language ?? throw new ArgumentNullException(nameof(language));
        TranscribedAt = DateTime.UtcNow;
    }

    public static Transcription Create(
        Guid recordingId,
        string fullText,
        string language)
    {
        if (recordingId == Guid.Empty)
            throw new ArgumentException("Recording ID cannot be empty", nameof(recordingId));

        if (string.IsNullOrWhiteSpace(fullText))
            throw new ArgumentException("Full text cannot be empty", nameof(fullText));

        if (string.IsNullOrWhiteSpace(language))
            throw new ArgumentException("Language cannot be empty", nameof(language));

        return new Transcription(recordingId, fullText, language);
    }

    public void AddSegment(TranscriptionSegment segment)
    {
        if (segment == null)
            throw new ArgumentNullException(nameof(segment));

        _segments.Add(segment);
        UpdateTimestamp();
    }

    public void AddSegments(IEnumerable<TranscriptionSegment> segments)
    {
        if (segments == null)
            throw new ArgumentNullException(nameof(segments));

        foreach (var segment in segments)
        {
            _segments.Add(segment);
        }

        UpdateTimestamp();
    }
}
