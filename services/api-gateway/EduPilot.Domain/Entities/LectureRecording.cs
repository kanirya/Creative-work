using EduPilot.Domain.Common;
using EduPilot.Domain.Enums;

namespace EduPilot.Domain.Entities;

public class LectureRecording : BaseEntity
{
    public Guid CourseId { get; private set; }
    public string Title { get; private set; }
    public DateTime RecordedAt { get; private set; }
    public TimeSpan Duration { get; private set; }
    public string StorageUrl { get; private set; }
    public RecordingSource Source { get; private set; }
    public Transcription? Transcription { get; private set; }

    private LectureRecording() { } // For EF Core

    private LectureRecording(
        Guid courseId,
        string title,
        DateTime recordedAt,
        TimeSpan duration,
        string storageUrl,
        RecordingSource source)
    {
        CourseId = courseId;
        Title = title ?? throw new ArgumentNullException(nameof(title));
        RecordedAt = recordedAt;
        Duration = duration;
        StorageUrl = storageUrl ?? throw new ArgumentNullException(nameof(storageUrl));
        Source = source;
    }

    public static LectureRecording Create(
        Guid courseId,
        string title,
        DateTime recordedAt,
        TimeSpan duration,
        string storageUrl,
        RecordingSource source)
    {
        if (courseId == Guid.Empty)
            throw new ArgumentException("Course ID cannot be empty", nameof(courseId));

        if (string.IsNullOrWhiteSpace(title))
            throw new ArgumentException("Title cannot be empty", nameof(title));

        if (duration <= TimeSpan.Zero)
            throw new ArgumentException("Duration must be greater than zero", nameof(duration));

        if (string.IsNullOrWhiteSpace(storageUrl))
            throw new ArgumentException("Storage URL cannot be empty", nameof(storageUrl));

        return new LectureRecording(courseId, title, recordedAt, duration, storageUrl, source);
    }

    public void SetTranscription(Transcription transcription)
    {
        Transcription = transcription ?? throw new ArgumentNullException(nameof(transcription));
        UpdateTimestamp();
    }

    public bool HasTranscription => Transcription != null;
}
