using AutoMapper;
using EduPilot.Application.Common;
using EduPilot.Application.DTOs;
using EduPilot.Domain.Interfaces;
using MediatR;
using Microsoft.Extensions.Logging;

namespace EduPilot.Application.Features.Students.Queries.GetStudentCourses;

public class GetStudentCoursesQueryHandler : IRequestHandler<GetStudentCoursesQuery, Result<List<CourseDto>>>
{
    private readonly IStudentRepository _studentRepository;
    private readonly IMapper _mapper;
    private readonly ILogger<GetStudentCoursesQueryHandler> _logger;

    public GetStudentCoursesQueryHandler(
        IStudentRepository studentRepository,
        IMapper mapper,
        ILogger<GetStudentCoursesQueryHandler> logger)
    {
        _studentRepository = studentRepository;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<Result<List<CourseDto>>> Handle(GetStudentCoursesQuery request, CancellationToken cancellationToken)
    {
        try
        {
            var courses = await _studentRepository.GetCoursesAsync(request.StudentId, cancellationToken);
            var courseDtos = _mapper.Map<List<CourseDto>>(courses);

            _logger.LogInformation("Retrieved {Count} courses for student {StudentId}", courseDtos.Count, request.StudentId);
            return Result<List<CourseDto>>.Success(courseDtos);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving courses for student {StudentId}", request.StudentId);
            return Result<List<CourseDto>>.Failure("An error occurred while retrieving courses");
        }
    }
}
