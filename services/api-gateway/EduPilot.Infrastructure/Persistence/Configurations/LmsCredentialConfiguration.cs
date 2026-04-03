using EduPilot.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace EduPilot.Infrastructure.Persistence.Configurations;

public class LmsCredentialConfiguration : IEntityTypeConfiguration<LmsCredential>
{
    public void Configure(EntityTypeBuilder<LmsCredential> builder)
    {
        builder.ToTable("lms_credentials");

        builder.HasKey(l => l.Id);

        builder.Property(l => l.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(l => l.StudentId)
            .HasColumnName("student_id")
            .IsRequired();

        builder.Property(l => l.EncryptedUsername)
            .HasColumnName("encrypted_username")
            .HasMaxLength(500)
            .IsRequired();

        builder.Property(l => l.EncryptedPassword)
            .HasColumnName("encrypted_password")
            .HasMaxLength(500)
            .IsRequired();

        builder.Property(l => l.Platform)
            .HasColumnName("platform")
            .HasMaxLength(50)
            .IsRequired();

        builder.Property(l => l.LastUsedAt)
            .HasColumnName("last_used_at")
            .IsRequired();

        builder.Property(l => l.IsActive)
            .HasColumnName("is_active")
            .IsRequired()
            .HasDefaultValue(true);

        builder.Property(l => l.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(l => l.UpdatedAt)
            .HasColumnName("updated_at")
            .IsRequired();

        // Relationships
        builder.HasOne(l => l.Student)
            .WithMany()
            .HasForeignKey(l => l.StudentId)
            .OnDelete(DeleteBehavior.Cascade);

        // Indexes
        builder.HasIndex(l => l.StudentId)
            .HasDatabaseName("idx_lms_credentials_student");

        builder.HasIndex(l => l.Platform)
            .HasDatabaseName("idx_lms_credentials_platform");

        builder.HasIndex(l => l.IsActive)
            .HasDatabaseName("idx_lms_credentials_is_active");
    }
}
