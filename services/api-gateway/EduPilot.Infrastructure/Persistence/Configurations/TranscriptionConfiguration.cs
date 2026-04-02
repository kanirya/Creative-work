using EduPilot.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace EduPilot.Infrastructure.Persistence.Configurations;

public class TranscriptionConfiguration : IEntityTypeConfiguration<Transcription>
{
    public void Configure(EntityTypeBuilder<Transcription> builder)
    {
        builder.ToTable("transcriptions");

        builder.HasKey(t => t.Id);

        builder.Property(t => t.Id)
            .HasColumnName("id")
            .ValueGeneratedNever();

        builder.Property(t => t.RecordingId)
            .HasColumnName("recording_id")
            .IsRequired();

        builder.Property(t => t.FullText)
            .HasColumnName("full_text")
            .HasColumnType("text")
            .IsRequired();

        builder.Property(t => t.Language)
            .HasColumnName("language")
            .HasMaxLength(10)
            .IsRequired()
            .HasDefaultValue("en");

        builder.Property(t => t.TranscribedAt)
            .HasColumnName("transcribed_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        // Indexes
        builder.HasIndex(t => t.RecordingId)
            .HasDatabaseName("idx_transcriptions_recording");

        builder.HasIndex(t => t.Language)
            .HasDatabaseName("idx_transcriptions_language");

        // Relationships
        builder.HasMany(t => t.Segments)
            .WithOne()
            .HasForeignKey(s => s.TranscriptionId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
