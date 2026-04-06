using EduPilot.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace EduPilot.Infrastructure.Persistence.Configurations;

public class RoleConfiguration : IEntityTypeConfiguration<Role>
{
    public void Configure(EntityTypeBuilder<Role> builder)
    {
        builder.ToTable("roles");

        builder.HasKey(r => r.Id);

        builder.Property(r => r.Id)
            .HasColumnName("id")
            .ValueGeneratedNever();

        builder.Property(r => r.Name)
            .HasColumnName("name")
            .HasMaxLength(50)
            .IsRequired();

        builder.Property(r => r.Description)
            .HasColumnName("description")
            .HasMaxLength(255);

        builder.Property(r => r.CreatedAt)
            .HasColumnName("created_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        builder.Property(r => r.UpdatedAt)
            .HasColumnName("updated_at")
            .HasDefaultValueSql("CURRENT_TIMESTAMP");

        builder.HasIndex(r => r.Name)
            .IsUnique()
            .HasDatabaseName("idx_roles_name");

        // Many-to-many: Role <-> Permission
        builder.HasMany(r => r.Permissions)
            .WithMany(p => p.Roles)
            .UsingEntity<Dictionary<string, object>>(
                "role_permissions",
                j => j.HasOne<Permission>().WithMany().HasForeignKey("permission_id"),
                j => j.HasOne<Role>().WithMany().HasForeignKey("role_id"));

        // Many-to-many: Student <-> Role (configured from Student side too, but define join table here)
        builder.HasMany(r => r.Students)
            .WithMany(s => s.Roles)
            .UsingEntity<Dictionary<string, object>>(
                "student_roles",
                j => j.HasOne<Student>().WithMany().HasForeignKey("student_id"),
                j => j.HasOne<Role>().WithMany().HasForeignKey("role_id"));
    }
}
