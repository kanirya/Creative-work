using EduPilot.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace EduPilot.Infrastructure.Persistence.Configurations;

public class AnnouncementConfiguration : IEntityTypeConfiguration<Announcement>
{
    public void Configure(EntityTypeBuilder<Announcement> builder)
    {
        builder.ToTable("announcements");

        builder.HasKey(a => a.Id);

        builder.Property(a => a.Id)
            .HasColumnName("id")
            .ValueGeneratedNever();

        builder.Property(a => a.CourseId)
            .HasColumnName("course_id")
            .IsRequired();

        builder.Property(a => a.Title)
            .HasColumnName("title")
            .HasMaxLength(255)
            .IsRequired();

        builder.Property(a => a.Content)
            .HasColumnName("content")
            .HasColumnType("text")
            .IsRequired();

        builder.Property(a => a.PostedAt)
            .HasColumnName("posted_at")
            .IsRequired();

        builder.Property(a => a.Priority)
            .HasColumnName("priority")
            .HasMaxLength(20)
            .IsRequired()
            .HasDefaultValue("normal")
            .HasConversion<string>();

        builder.Property(a => a.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        // Indexes
        builder.HasIndex(a => a.CourseId)
            .HasDatabaseName("idx_announcements_course");

        builder.HasIndex(a => a.PostedAt)
            .IsDescending()
            .HasDatabaseName("idx_announcements_posted");

        builder.HasIndex(a => a.Priority)
            .HasDatabaseName("idx_announcements_priority");

        // Ignore computed properties
        builder.Ignore(a => a.IsUrgent);
    }
}
