using EduPilot.Application.Common;
using EduPilot.Application.DTOs;

namespace EduPilot.Application.Features.Students.Queries.GetAssignments;

public class GetAssignmentsQuery : BaseQuery<Result<List<AssignmentDto>>>
{
    public Guid StudentId { get; set; }
    public string? Status { get; set; }
    public bool? UpcomingOnly { get; set; }
    public int? DaysAhead { get; set; }
}
