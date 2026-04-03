using EduPilot.Domain.Common;

namespace EduPilot.Domain.Entities;

/// <summary>
/// Represents a permission in the role-based access control system
/// </summary>
public class Permission : BaseEntity
{
    public Guid Id { get; private set; }
    public string Name { get; private set; }
    public string Resource { get; private set; }
    public string Action { get; private set; }
    public string Description { get; private set; }
    public DateTime CreatedAt { get; private set; }

    private readonly List<Role> _roles = new();
    public IReadOnlyCollection<Role> Roles => _roles.AsReadOnly();

    private Permission() { } // EF Core

    private Permission(string name, string resource, string action, string description)
    {
        Id = Guid.NewGuid();
        Name = name;
        Resource = resource;
        Action = action;
        Description = description;
        CreatedAt = DateTime.UtcNow;
    }

    public static Permission Create(string name, string resource, string action, string description)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Permission name cannot be empty", nameof(name));

        if (string.IsNullOrWhiteSpace(resource))
            throw new ArgumentException("Resource cannot be empty", nameof(resource));

        if (string.IsNullOrWhiteSpace(action))
            throw new ArgumentException("Action cannot be empty", nameof(action));

        return new Permission(name, resource, action, description);
    }

    public bool Matches(string resource, string action)
    {
        return Resource.Equals(resource, StringComparison.OrdinalIgnoreCase) &&
               (Action.Equals(action, StringComparison.OrdinalIgnoreCase) || Action == "*");
    }
}
