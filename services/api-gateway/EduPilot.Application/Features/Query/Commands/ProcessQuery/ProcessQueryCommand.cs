using EduPilot.Application.Common;
using EduPilot.Application.DTOs;

namespace EduPilot.Application.Features.Query.Commands.ProcessQuery;

public class ProcessQueryCommand : BaseCommand<Result<QueryResponseDto>>
{
    public Guid StudentId { get; set; }
    public string Query { get; set; } = string.Empty;
    public string Type { get; set; } = "text";
    public byte[]? AudioData { get; set; }
}
