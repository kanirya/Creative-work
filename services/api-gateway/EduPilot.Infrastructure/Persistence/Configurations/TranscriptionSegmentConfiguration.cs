using EduPilot.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace EduPilot.Infrastructure.Persistence.Configurations;

public class TranscriptionSegmentConfiguration : IEntityTypeConfiguration<TranscriptionSegment>
{
    public void Configure(EntityTypeBuilder<TranscriptionSegment> builder)
    {
        builder.ToTable("transcription_segments");

        builder.HasKey(s => s.Id);

        builder.Property(s => s.Id)
            .HasColumnName("id")
            .ValueGeneratedNever();

        builder.Property(s => s.TranscriptionId)
            .HasColumnName("transcription_id")
            .IsRequired();

        builder.Property(s => s.StartTime)
            .HasColumnName("start_time_seconds")
            .HasConversion(
                time => (decimal)time.TotalSeconds,
                seconds => TimeSpan.FromSeconds((double)seconds))
            .IsRequired();

        builder.Property(s => s.EndTime)
            .HasColumnName("end_time_seconds")
            .HasConversion(
                time => (decimal)time.TotalSeconds,
                seconds => TimeSpan.FromSeconds((double)seconds))
            .IsRequired();

        builder.Property(s => s.Text)
            .HasColumnName("text")
            .HasColumnType("text")
            .IsRequired();

        // Indexes
        builder.HasIndex(s => s.TranscriptionId)
            .HasDatabaseName("idx_segments_transcription");

        builder.HasIndex(s => s.StartTime)
            .HasDatabaseName("idx_segments_start_time");

        // Ignore computed properties
        builder.Ignore(s => s.Duration);
    }
}
