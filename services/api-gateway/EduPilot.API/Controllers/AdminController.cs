using EduPilot.Infrastructure.Persistence;
using EduPilot.Infrastructure.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace EduPilot.API.Controllers;

/// <summary>
/// Administrative endpoints protected by role-based access control.
/// Requires the "Admin" role.
/// </summary>
[Authorize(Policy = "AdminPolicy")]
[Route("api/admin")]
public class AdminController : BaseApiController
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ILogger<AdminController> _logger;
    private readonly DataRetentionService _retentionService;

    public AdminController(
        ApplicationDbContext dbContext,
        ILogger<AdminController> logger,
        DataRetentionService retentionService)
    {
        _dbContext = dbContext;
        _logger = logger;
        _retentionService = retentionService;
    }

    /// <summary>
    /// Get all students (admin only)
    /// </summary>
    [HttpGet("students")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    public async Task<IActionResult> GetAllStudents()
    {
        var students = await _dbContext.Students
            .Include(s => s.Roles)
            .Select(s => new
            {
                s.Id,
                Email = s.Email.Value,
                s.FirstName,
                s.LastName,
                UniversityId = s.UniversityId.Value,
                s.IsActive,
                s.EnrolledAt,
                Roles = s.Roles.Select(r => r.Name).ToList()
            })
            .ToListAsync();

        return Ok(new ApiResponse<object> { Success = true, Data = students });
    }

    /// <summary>
    /// Get all roles (admin only)
    /// </summary>
    [HttpGet("roles")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    public async Task<IActionResult> GetAllRoles()
    {
        var roles = await _dbContext.Roles
            .Include(r => r.Permissions)
            .Select(r => new
            {
                r.Id,
                r.Name,
                r.Description,
                r.CreatedAt,
                Permissions = r.Permissions.Select(p => new { p.Id, p.Name, p.Resource, p.Action }).ToList()
            })
            .ToListAsync();

        return Ok(new ApiResponse<object> { Success = true, Data = roles });
    }

    /// <summary>
    /// Get all permissions (admin only)
    /// </summary>
    [HttpGet("permissions")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    public async Task<IActionResult> GetAllPermissions()
    {
        var permissions = await _dbContext.Permissions
            .Select(p => new { p.Id, p.Name, p.Resource, p.Action, p.Description })
            .ToListAsync();

        return Ok(new ApiResponse<object> { Success = true, Data = permissions });
    }

    /// <summary>
    /// Assign a role to a student (admin only)
    /// </summary>
    [HttpPost("students/{studentId}/roles/{roleId}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    public async Task<IActionResult> AssignRole(Guid studentId, Guid roleId)
    {
        var student = await _dbContext.Students
            .Include(s => s.Roles)
            .FirstOrDefaultAsync(s => s.Id == studentId);

        if (student == null)
            return NotFound(new ApiResponse { Success = false, ErrorMessage = "Student not found" });

        var role = await _dbContext.Roles.FindAsync(roleId);
        if (role == null)
            return NotFound(new ApiResponse { Success = false, ErrorMessage = "Role not found" });

        student.AssignRole(role);
        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("Role {RoleName} assigned to student {StudentId}", role.Name, studentId);

        return Ok(new ApiResponse { Success = true });
    }

    /// <summary>
    /// Remove a role from a student (admin only)
    /// </summary>
    [HttpDelete("students/{studentId}/roles/{roleId}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    public async Task<IActionResult> RemoveRole(Guid studentId, Guid roleId)
    {
        var student = await _dbContext.Students
            .Include(s => s.Roles)
            .FirstOrDefaultAsync(s => s.Id == studentId);

        if (student == null)
            return NotFound(new ApiResponse { Success = false, ErrorMessage = "Student not found" });

        var role = student.Roles.FirstOrDefault(r => r.Id == roleId);
        if (role == null)
            return NotFound(new ApiResponse { Success = false, ErrorMessage = "Role not assigned to student" });

        student.RemoveRole(role);
        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("Role {RoleName} removed from student {StudentId}", role.Name, studentId);

        return Ok(new ApiResponse { Success = true });
    }

    /// <summary>
    /// Deactivate a student account (admin only)
    /// </summary>
    [HttpPost("students/{studentId}/deactivate")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    public async Task<IActionResult> DeactivateStudent(Guid studentId)
    {
        var student = await _dbContext.Students.FindAsync(studentId);
        if (student == null)
            return NotFound(new ApiResponse { Success = false, ErrorMessage = "Student not found" });

        student.Deactivate();
        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("Student {StudentId} deactivated by admin", studentId);

        return Ok(new ApiResponse { Success = true });
    }

    /// <summary>
    /// Get FERPA data access logs for a student (admin only)
    /// </summary>
    [HttpGet("ferpa/access-logs/{studentId}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    public async Task<IActionResult> GetDataAccessLogs(
        Guid studentId,
        [FromQuery] DateTime? from = null,
        [FromQuery] DateTime? to = null,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 50)
    {
        var query = _dbContext.DataAccessLogs
            .Where(l => l.StudentId == studentId);

        if (from.HasValue)
            query = query.Where(l => l.AccessedAt >= from.Value);
        if (to.HasValue)
            query = query.Where(l => l.AccessedAt <= to.Value);

        var total = await query.CountAsync();
        var logs = await query
            .OrderByDescending(l => l.AccessedAt)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(l => new
            {
                l.Id,
                l.StudentId,
                l.AccessedByUserId,
                l.AccessedByEmail,
                l.ResourceType,
                l.ResourceId,
                l.Action,
                l.IpAddress,
                l.AccessedAt,
                l.Purpose
            })
            .ToListAsync();

        return Ok(new ApiResponse<object>
        {
            Success = true,
            Data = new { total, page, pageSize, logs }
        });
    }

    /// <summary>
    /// Trigger FERPA data retention policy enforcement (admin only)
    /// </summary>
    [HttpPost("ferpa/apply-retention")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    public async Task<IActionResult> ApplyRetentionPolicies()
    {
        await _retentionService.ApplyRetentionPoliciesAsync();
        _logger.LogInformation("FERPA data retention policies applied by admin");
        return Ok(new ApiResponse { Success = true });
    }
}
