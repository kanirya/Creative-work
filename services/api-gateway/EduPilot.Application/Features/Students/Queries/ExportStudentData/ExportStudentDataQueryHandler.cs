using AutoMapper;
using EduPilot.Application.Common;
using EduPilot.Application.DTOs;
using EduPilot.Domain.Interfaces;
using MediatR;
using Microsoft.Extensions.Logging;

namespace EduPilot.Application.Features.Students.Queries.ExportStudentData;

public class ExportStudentDataQueryHandler : IRequestHandler<ExportStudentDataQuery, Result<StudentDataExportDto>>
{
    private readonly IStudentRepository _studentRepository;
    private readonly IMapper _mapper;
    private readonly ILogger<ExportStudentDataQueryHandler> _logger;

    public ExportStudentDataQueryHandler(
        IStudentRepository studentRepository,
        IMapper mapper,
        ILogger<ExportStudentDataQueryHandler> logger)
    {
        _studentRepository = studentRepository;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<Result<StudentDataExportDto>> Handle(
        ExportStudentDataQuery request,
        CancellationToken cancellationToken)
    {
        try
        {
            var student = await _studentRepository.GetByIdAsync(request.StudentId, cancellationToken);
            if (student == null)
                return Result<StudentDataExportDto>.Failure("Student not found");

            var courses = await _studentRepository.GetCoursesAsync(request.StudentId, cancellationToken);
            var assignments = await _studentRepository.GetAssignmentsAsync(request.StudentId, cancellationToken);
            var announcements = await _studentRepository.GetAnnouncementsAsync(request.StudentId, cancellationToken);

            var export = new StudentDataExportDto
            {
                Profile = _mapper.Map<StudentDto>(student),
                Courses = _mapper.Map<List<CourseDto>>(courses),
                Assignments = _mapper.Map<List<AssignmentDto>>(assignments),
                Announcements = _mapper.Map<List<AnnouncementDto>>(announcements),
                ExportedAt = DateTime.UtcNow
            };

            _logger.LogInformation(
                "FERPA data export generated for student {StudentId}: {Courses} courses, {Assignments} assignments",
                request.StudentId, export.Courses.Count, export.Assignments.Count);

            return Result<StudentDataExportDto>.Success(export);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating data export for student {StudentId}", request.StudentId);
            return Result<StudentDataExportDto>.Failure("An error occurred while generating the data export");
        }
    }
}
