using EduPilot.Domain.Entities;
using EduPilot.Domain.ValueObjects;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace EduPilot.Infrastructure.Persistence.Configurations;

public class CourseConfiguration : IEntityTypeConfiguration<Course>
{
    public void Configure(EntityTypeBuilder<Course> builder)
    {
        builder.ToTable("courses");

        builder.HasKey(c => c.Id);

        builder.Property(c => c.Id)
            .HasColumnName("id")
            .ValueGeneratedNever();

        builder.Property(c => c.Name)
            .HasColumnName("name")
            .HasMaxLength(255)
            .IsRequired();

        builder.Property(c => c.Instructor)
            .HasColumnName("instructor")
            .HasMaxLength(255);

        builder.Property(c => c.Semester)
            .HasColumnName("semester")
            .HasMaxLength(50)
            .IsRequired();

        builder.Property(c => c.CreditHours)
            .HasColumnName("credit_hours")
            .IsRequired();

        builder.Property(c => c.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        builder.Property(c => c.UpdatedAt)
            .HasColumnName("updated_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        // Value object conversion
        builder.Property(c => c.Code)
            .HasColumnName("code")
            .HasMaxLength(20)
            .IsRequired()
            .HasConversion(
                code => code.Value,
                value => CourseCode.Create(value));

        // Indexes
        builder.HasIndex(c => c.Code)
            .HasDatabaseName("idx_courses_code");

        builder.HasIndex(c => c.Semester)
            .HasDatabaseName("idx_courses_semester");

        // Relationships
        builder.HasMany(c => c.Assignments)
            .WithOne()
            .HasForeignKey(a => a.CourseId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasMany(c => c.Announcements)
            .WithOne()
            .HasForeignKey(a => a.CourseId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasMany(c => c.Recordings)
            .WithOne()
            .HasForeignKey(r => r.CourseId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
