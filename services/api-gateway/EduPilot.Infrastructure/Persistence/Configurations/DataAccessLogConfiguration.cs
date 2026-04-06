using EduPilot.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace EduPilot.Infrastructure.Persistence.Configurations;

public class DataAccessLogConfiguration : IEntityTypeConfiguration<DataAccessLog>
{
    public void Configure(EntityTypeBuilder<DataAccessLog> builder)
    {
        builder.ToTable("data_access_logs");

        builder.HasKey(d => d.Id);

        builder.Property(d => d.Id)
            .HasColumnName("id")
            .ValueGeneratedNever();

        builder.Property(d => d.StudentId)
            .HasColumnName("student_id")
            .IsRequired();

        builder.Property(d => d.AccessedByUserId)
            .HasColumnName("accessed_by_user_id");

        builder.Property(d => d.AccessedByEmail)
            .HasColumnName("accessed_by_email")
            .HasMaxLength(255)
            .IsRequired();

        builder.Property(d => d.ResourceType)
            .HasColumnName("resource_type")
            .HasMaxLength(100)
            .IsRequired();

        builder.Property(d => d.ResourceId)
            .HasColumnName("resource_id")
            .IsRequired();

        builder.Property(d => d.Action)
            .HasColumnName("action")
            .HasMaxLength(50)
            .IsRequired();

        builder.Property(d => d.IpAddress)
            .HasColumnName("ip_address")
            .HasMaxLength(45);

        builder.Property(d => d.UserAgent)
            .HasColumnName("user_agent")
            .HasMaxLength(500);

        builder.Property(d => d.AccessedAt)
            .HasColumnName("accessed_at")
            .IsRequired();

        builder.Property(d => d.Purpose)
            .HasColumnName("purpose")
            .HasMaxLength(255);

        builder.Property(d => d.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        builder.Property(d => d.UpdatedAt)
            .HasColumnName("updated_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        // Indexes for FERPA audit queries
        builder.HasIndex(d => d.StudentId)
            .HasDatabaseName("idx_data_access_logs_student_id");

        builder.HasIndex(d => d.AccessedAt)
            .HasDatabaseName("idx_data_access_logs_accessed_at");

        builder.HasIndex(d => d.AccessedByUserId)
            .HasDatabaseName("idx_data_access_logs_accessed_by");

        // Foreign key to students
        builder.HasOne<Student>()
            .WithMany()
            .HasForeignKey(d => d.StudentId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
