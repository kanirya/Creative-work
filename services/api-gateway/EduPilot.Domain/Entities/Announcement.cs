using EduPilot.Domain.Common;
using EduPilot.Domain.Enums;

namespace EduPilot.Domain.Entities;

public class Announcement : BaseEntity
{
    public Guid CourseId { get; private set; }
    public string Title { get; private set; }
    public string Content { get; private set; }
    public DateTime PostedAt { get; private set; }
    public AnnouncementPriority Priority { get; private set; }

    private Announcement() { } // For EF Core

    private Announcement(
        Guid courseId,
        string title,
        string content,
        DateTime postedAt,
        AnnouncementPriority priority)
    {
        CourseId = courseId;
        Title = title ?? throw new ArgumentNullException(nameof(title));
        Content = content ?? throw new ArgumentNullException(nameof(content));
        PostedAt = postedAt;
        Priority = priority;
    }

    public static Announcement Create(
        Guid courseId,
        string title,
        string content,
        DateTime postedAt,
        AnnouncementPriority priority = AnnouncementPriority.Normal)
    {
        if (courseId == Guid.Empty)
            throw new ArgumentException("Course ID cannot be empty", nameof(courseId));

        if (string.IsNullOrWhiteSpace(title))
            throw new ArgumentException("Title cannot be empty", nameof(title));

        if (string.IsNullOrWhiteSpace(content))
            throw new ArgumentException("Content cannot be empty", nameof(content));

        return new Announcement(courseId, title, content, postedAt, priority);
    }

    public void UpdatePriority(AnnouncementPriority priority)
    {
        Priority = priority;
        UpdateTimestamp();
    }

    public bool IsUrgent => Priority == AnnouncementPriority.Urgent;
}
