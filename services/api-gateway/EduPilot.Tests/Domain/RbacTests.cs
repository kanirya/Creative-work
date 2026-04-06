using EduPilot.Domain.Entities;
using EduPilot.Domain.Enums;
using Xunit;

namespace EduPilot.Tests.Domain;

public class RbacTests
{
    [Fact]
    public void Role_Create_WithValidName_ShouldSucceed()
    {
        var role = Role.Create(UserRoles.Admin, "Administrator role");

        Assert.Equal(UserRoles.Admin, role.Name);
        Assert.Equal("Administrator role", role.Description);
        Assert.NotEqual(Guid.Empty, role.Id);
    }

    [Fact]
    public void Role_Create_WithEmptyName_ShouldThrow()
    {
        Assert.Throws<ArgumentException>(() => Role.Create("", "desc"));
    }

    [Fact]
    public void Role_Create_WithNameExceeding50Chars_ShouldThrow()
    {
        var longName = new string('A', 51);
        Assert.Throws<ArgumentException>(() => Role.Create(longName, "desc"));
    }

    [Fact]
    public void Permission_Create_WithValidData_ShouldSucceed()
    {
        var permission = Permission.Create("admin.students.manage", "students", "manage", "Manage students");

        Assert.Equal("admin.students.manage", permission.Name);
        Assert.Equal("students", permission.Resource);
        Assert.Equal("manage", permission.Action);
    }

    [Fact]
    public void Permission_Matches_ShouldReturnTrue_WhenResourceAndActionMatch()
    {
        var permission = Permission.Create("admin.students.manage", "students", "manage", "desc");

        Assert.True(permission.Matches("students", "manage"));
        Assert.True(permission.Matches("STUDENTS", "MANAGE")); // case-insensitive
    }

    [Fact]
    public void Permission_Matches_WithWildcardAction_ShouldMatchAnyAction()
    {
        var permission = Permission.Create("admin.students.all", "students", "*", "desc");

        Assert.True(permission.Matches("students", "read"));
        Assert.True(permission.Matches("students", "write"));
        Assert.True(permission.Matches("students", "delete"));
    }

    [Fact]
    public void Role_AddPermission_ShouldGrantPermission()
    {
        var role = Role.Create(UserRoles.Admin, "Admin");
        var permission = Permission.Create("admin.students.manage", "students", "manage", "desc");

        role.AddPermission(permission);

        Assert.True(role.HasPermission("admin.students.manage"));
    }

    [Fact]
    public void Role_AddPermission_Duplicate_ShouldNotAddTwice()
    {
        var role = Role.Create(UserRoles.Admin, "Admin");
        var permission = Permission.Create("admin.students.manage", "students", "manage", "desc");

        role.AddPermission(permission);
        role.AddPermission(permission); // duplicate

        Assert.Single(role.Permissions);
    }

    [Fact]
    public void Role_RemovePermission_ShouldRevokePermission()
    {
        var role = Role.Create(UserRoles.Admin, "Admin");
        var permission = Permission.Create("admin.students.manage", "students", "manage", "desc");
        role.AddPermission(permission);

        role.RemovePermission(permission);

        Assert.False(role.HasPermission("admin.students.manage"));
    }

    [Fact]
    public void Student_AssignRole_ShouldGrantRole()
    {
        var student = CreateTestStudent();
        var role = Role.Create(UserRoles.Admin, "Admin");

        student.AssignRole(role);

        Assert.True(student.HasRole(UserRoles.Admin));
    }

    [Fact]
    public void Student_AssignRole_Duplicate_ShouldNotAddTwice()
    {
        var student = CreateTestStudent();
        var role = Role.Create(UserRoles.Admin, "Admin");

        student.AssignRole(role);
        student.AssignRole(role); // duplicate

        Assert.Single(student.Roles);
    }

    [Fact]
    public void Student_RemoveRole_ShouldRevokeRole()
    {
        var student = CreateTestStudent();
        var role = Role.Create(UserRoles.Admin, "Admin");
        student.AssignRole(role);

        student.RemoveRole(role);

        Assert.False(student.HasRole(UserRoles.Admin));
    }

    [Fact]
    public void Student_HasPermission_ShouldReturnTrue_WhenRoleHasPermission()
    {
        var student = CreateTestStudent();
        var role = Role.Create(UserRoles.Admin, "Admin");
        var permission = Permission.Create("admin.students.manage", "students", "manage", "desc");
        role.AddPermission(permission);
        student.AssignRole(role);

        Assert.True(student.HasPermission("admin.students.manage"));
    }

    [Fact]
    public void Student_HasPermission_ShouldReturnFalse_WhenNoRoleHasPermission()
    {
        var student = CreateTestStudent();
        var role = Role.Create(UserRoles.Student, "Student");
        student.AssignRole(role);

        Assert.False(student.HasPermission("admin.students.manage"));
    }

    [Fact]
    public void Student_HasRole_IsCaseInsensitive()
    {
        var student = CreateTestStudent();
        var role = Role.Create("Admin", "Admin");
        student.AssignRole(role);

        Assert.True(student.HasRole("admin"));
        Assert.True(student.HasRole("ADMIN"));
    }

    private static Student CreateTestStudent()
    {
        var email = EduPilot.Domain.ValueObjects.Email.Create("test@example.com");
        var universityId = EduPilot.Domain.ValueObjects.StudentId.Create("STU001");
        return Student.Create(email, "hashedpassword", "Test", "User", universityId);
    }
}
