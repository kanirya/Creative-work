using EduPilot.Application.Common;
using EduPilot.Application.DTOs;

namespace EduPilot.Application.Features.Students.Queries.ExportStudentData;

public class ExportStudentDataQuery : BaseQuery<Result<StudentDataExportDto>>
{
    public Guid StudentId { get; set; }
}
