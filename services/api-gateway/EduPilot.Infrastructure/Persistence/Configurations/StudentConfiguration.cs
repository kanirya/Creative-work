using EduPilot.Domain.Entities;
using EduPilot.Domain.ValueObjects;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace EduPilot.Infrastructure.Persistence.Configurations;

public class StudentConfiguration : IEntityTypeConfiguration<Student>
{
    public void Configure(EntityTypeBuilder<Student> builder)
    {
        builder.ToTable("students");

        builder.HasKey(s => s.Id);

        builder.Property(s => s.Id)
            .HasColumnName("id")
            .ValueGeneratedNever();

        builder.Property(s => s.FirstName)
            .HasColumnName("first_name")
            .HasMaxLength(100)
            .IsRequired();

        builder.Property(s => s.LastName)
            .HasColumnName("last_name")
            .HasMaxLength(100)
            .IsRequired();

        builder.Property(s => s.PasswordHash)
            .HasColumnName("password_hash")
            .HasMaxLength(255)
            .IsRequired();

        builder.Property(s => s.EnrolledAt)
            .HasColumnName("enrolled_at")
            .IsRequired();

        builder.Property(s => s.IsActive)
            .HasColumnName("is_active")
            .HasDefaultValue(true);

        builder.Property(s => s.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        builder.Property(s => s.UpdatedAt)
            .HasColumnName("updated_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        // Value object conversions
        builder.Property(s => s.Email)
            .HasColumnName("email")
            .HasMaxLength(255)
            .IsRequired()
            .HasConversion(
                email => email.Value,
                value => Email.Create(value));

        builder.Property(s => s.UniversityId)
            .HasColumnName("university_id")
            .HasMaxLength(50)
            .IsRequired()
            .HasConversion(
                id => id.Value,
                value => StudentId.Create(value));

        // Indexes
        builder.HasIndex(s => s.Email)
            .IsUnique()
            .HasDatabaseName("idx_students_email");

        builder.HasIndex(s => s.UniversityId)
            .IsUnique()
            .HasDatabaseName("idx_students_university_id");

        builder.HasIndex(s => s.IsActive)
            .HasDatabaseName("idx_students_is_active");

        // Relationships
        builder.HasMany(s => s.Courses)
            .WithMany()
            .UsingEntity<Dictionary<string, object>>(
                "student_courses",
                j => j.HasOne<Course>().WithMany().HasForeignKey("course_id"),
                j => j.HasOne<Student>().WithMany().HasForeignKey("student_id"));

        builder.Ignore(s => s.FullName);
    }
}
