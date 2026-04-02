using EduPilot.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace EduPilot.Infrastructure.Persistence.Configurations;

public class LectureRecordingConfiguration : IEntityTypeConfiguration<LectureRecording>
{
    public void Configure(EntityTypeBuilder<LectureRecording> builder)
    {
        builder.ToTable("lecture_recordings");

        builder.HasKey(r => r.Id);

        builder.Property(r => r.Id)
            .HasColumnName("id")
            .ValueGeneratedNever();

        builder.Property(r => r.CourseId)
            .HasColumnName("course_id")
            .IsRequired();

        builder.Property(r => r.Title)
            .HasColumnName("title")
            .HasMaxLength(255)
            .IsRequired();

        builder.Property(r => r.RecordedAt)
            .HasColumnName("recorded_at")
            .IsRequired();

        builder.Property(r => r.Duration)
            .HasColumnName("duration_seconds")
            .HasConversion(
                duration => (int)duration.TotalSeconds,
                seconds => TimeSpan.FromSeconds(seconds))
            .IsRequired();

        builder.Property(r => r.StorageUrl)
            .HasColumnName("storage_url")
            .HasColumnType("text")
            .IsRequired();

        builder.Property(r => r.Source)
            .HasColumnName("source")
            .HasMaxLength(50)
            .IsRequired()
            .HasConversion<string>();

        builder.Property(r => r.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        // Indexes
        builder.HasIndex(r => r.CourseId)
            .HasDatabaseName("idx_recordings_course");

        builder.HasIndex(r => r.RecordedAt)
            .HasDatabaseName("idx_recordings_date");

        builder.HasIndex(r => r.Source)
            .HasDatabaseName("idx_recordings_source");

        // Relationships
        builder.HasOne(r => r.Transcription)
            .WithOne()
            .HasForeignKey<Transcription>(t => t.RecordingId)
            .OnDelete(DeleteBehavior.Cascade);

        // Ignore computed properties
        builder.Ignore(r => r.HasTranscription);
    }
}
