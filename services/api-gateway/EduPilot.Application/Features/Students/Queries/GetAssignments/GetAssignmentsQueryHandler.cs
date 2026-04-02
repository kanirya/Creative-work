using AutoMapper;
using EduPilot.Application.Common;
using EduPilot.Application.DTOs;
using EduPilot.Domain.Interfaces;
using MediatR;
using Microsoft.Extensions.Logging;

namespace EduPilot.Application.Features.Students.Queries.GetAssignments;

public class GetAssignmentsQueryHandler : IRequestHandler<GetAssignmentsQuery, Result<List<AssignmentDto>>>
{
    private readonly IStudentRepository _studentRepository;
    private readonly IMapper _mapper;
    private readonly ILogger<GetAssignmentsQueryHandler> _logger;

    public GetAssignmentsQueryHandler(
        IStudentRepository studentRepository,
        IMapper mapper,
        ILogger<GetAssignmentsQueryHandler> logger)
    {
        _studentRepository = studentRepository;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<Result<List<AssignmentDto>>> Handle(GetAssignmentsQuery request, CancellationToken cancellationToken)
    {
        try
        {
            var assignments = request.UpcomingOnly == true
                ? await _studentRepository.GetUpcomingAssignmentsAsync(request.StudentId, request.DaysAhead ?? 7, cancellationToken)
                : await _studentRepository.GetAssignmentsAsync(request.StudentId, cancellationToken);

            var assignmentDtos = _mapper.Map<List<AssignmentDto>>(assignments);

            // Filter by status if provided
            if (!string.IsNullOrWhiteSpace(request.Status))
            {
                assignmentDtos = assignmentDtos
                    .Where(a => a.Status.Equals(request.Status, StringComparison.OrdinalIgnoreCase))
                    .ToList();
            }

            _logger.LogInformation("Retrieved {Count} assignments for student {StudentId}", assignmentDtos.Count, request.StudentId);
            return Result<List<AssignmentDto>>.Success(assignmentDtos);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving assignments for student {StudentId}", request.StudentId);
            return Result<List<AssignmentDto>>.Failure("An error occurred while retrieving assignments");
        }
    }
}
