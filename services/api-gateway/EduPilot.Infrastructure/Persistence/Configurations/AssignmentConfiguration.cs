using EduPilot.Domain.Entities;
using EduPilot.Domain.Enums;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace EduPilot.Infrastructure.Persistence.Configurations;

public class AssignmentConfiguration : IEntityTypeConfiguration<Assignment>
{
    public void Configure(EntityTypeBuilder<Assignment> builder)
    {
        builder.ToTable("assignments");

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

        builder.Property(a => a.Description)
            .HasColumnName("description")
            .HasColumnType("text");

        builder.Property(a => a.DueDate)
            .HasColumnName("due_date")
            .IsRequired();

        builder.Property(a => a.MaxPoints)
            .HasColumnName("max_points")
            .IsRequired();

        builder.Property(a => a.Status)
            .HasColumnName("status")
            .HasMaxLength(50)
            .IsRequired()
            .HasConversion<string>();

        builder.Property(a => a.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        builder.Property(a => a.UpdatedAt)
            .HasColumnName("updated_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        // Owned type for Grade
        builder.OwnsOne(a => a.Grade, grade =>
        {
            grade.Property(g => g.Points).HasColumnName("points_earned");
            grade.Property(g => g.MaxPoints).HasColumnName("max_points_grade");
            grade.Ignore(g => g.Percentage);
            grade.Ignore(g => g.LetterGrade);
        });

        // Indexes
        builder.HasIndex(a => a.CourseId)
            .HasDatabaseName("idx_assignments_course");

        builder.HasIndex(a => a.DueDate)
            .HasDatabaseName("idx_assignments_due_date");

        builder.HasIndex(a => a.Status)
            .HasDatabaseName("idx_assignments_status");

        // Ignore computed properties
        builder.Ignore(a => a.IsOverdue);
        builder.Ignore(a => a.TimeUntilDue);
    }
}
