using EduPilot.Application.Features.Students.Commands.SyncStudentData;
using EduPilot.Application.Features.Students.Queries.ExportStudentData;
using EduPilot.Application.Features.Students.Queries.GetAssignments;
using EduPilot.Application.Features.Students.Queries.GetStudentCourses;
using EduPilot.Domain.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;

namespace EduPilot.API.Controllers;

/// <summary>
/// Student data endpoints for courses, assignments, and synchronization
/// </summary>
[Authorize]
public class StudentsController : BaseApiController
{
    private readonly IFerpaAuditService _ferpaAudit;

    public StudentsController(IFerpaAuditService ferpaAudit)
    {
        _ferpaAudit = ferpaAudit;
    }

    /// <summary>
    /// Get all courses for the authenticated student
    /// </summary>
    /// <returns>List of courses</returns>
    [HttpGet("courses")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> GetCourses()
    {
        var studentId = GetStudentId();
        var result = await Mediator.Send(new GetStudentCoursesQuery { StudentId = studentId });

        await _ferpaAudit.LogAccessAsync(
            studentId, studentId, GetUserEmail(),
            "Courses", studentId, "READ",
            GetIpAddress(), GetUserAgent());

        return HandleResult(result);
    }

    /// <summary>
    /// Get assignments for the authenticated student
    /// </summary>
    /// <param name="status">Filter by status (optional)</param>
    /// <param name="upcomingOnly">Show only upcoming assignments</param>
    /// <param name="daysAhead">Number of days ahead for upcoming filter</param>
    /// <returns>List of assignments</returns>
    [HttpGet("assignments")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> GetAssignments(
        [FromQuery] string? status = null,
        [FromQuery] bool? upcomingOnly = null,
        [FromQuery] int? daysAhead = null)
    {
        var studentId = GetStudentId();
        var result = await Mediator.Send(new GetAssignmentsQuery
        {
            StudentId = studentId,
            Status = status,
            UpcomingOnly = upcomingOnly,
            DaysAhead = daysAhead
        });

        await _ferpaAudit.LogAccessAsync(
            studentId, studentId, GetUserEmail(),
            "Assignments", studentId, "READ",
            GetIpAddress(), GetUserAgent());

        return HandleResult(result);
    }

    /// <summary>
    /// Trigger LMS data synchronization for the authenticated student
    /// </summary>
    /// <returns>Sync result with updated counts</returns>
    [HttpPost("sync")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> SyncData()
    {
        var studentId = GetStudentId();
        var result = await Mediator.Send(new SyncStudentDataCommand { StudentId = studentId });
        return HandleResult(result);
    }

    /// <summary>
    /// Export all educational records for the authenticated student (FERPA data portability)
    /// </summary>
    /// <returns>Complete student data export in JSON format</returns>
    [HttpGet("export")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> ExportData()
    {
        var studentId = GetStudentId();
        var result = await Mediator.Send(new ExportStudentDataQuery { StudentId = studentId });

        if (result.IsSuccess)
        {
            await _ferpaAudit.LogAccessAsync(
                studentId, studentId, GetUserEmail(),
                "StudentDataExport", studentId, "EXPORT",
                GetIpAddress(), GetUserAgent(),
                purpose: "FERPA data export request by student");
        }

        return HandleResult(result);
    }

    private Guid GetStudentId()
    {
        var studentIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        return Guid.Parse(studentIdClaim ?? throw new UnauthorizedAccessException("Student ID not found in token"));
    }

    private string GetUserEmail()
    {
        return User.FindFirst(ClaimTypes.Email)?.Value ?? "unknown";
    }

    private string GetIpAddress()
    {
        return HttpContext.Connection.RemoteIpAddress?.ToString() ?? "Unknown";
    }

    private string GetUserAgent()
    {
        return HttpContext.Request.Headers["User-Agent"].ToString();
    }
}
