using EduPilot.Domain.Entities;
using EduPilot.Domain.ValueObjects;

namespace EduPilot.Domain.Interfaces;

public interface IStudentRepository : IRepository<Student>
{
    Task<Student?> GetByEmailAsync(Email email, CancellationToken cancellationToken = default);
    Task<Student?> GetByUniversityIdAsync(StudentId universityId, CancellationToken cancellationToken = default);
    Task<IEnumerable<Course>> GetCoursesAsync(Guid studentId, CancellationToken cancellationToken = default);
    Task<IEnumerable<Assignment>> GetAssignmentsAsync(Guid studentId, CancellationToken cancellationToken = default);
    Task<IEnumerable<Assignment>> GetUpcomingAssignmentsAsync(Guid studentId, int days = 7, CancellationToken cancellationToken = default);
    Task<IEnumerable<Announcement>> GetAnnouncementsAsync(Guid studentId, CancellationToken cancellationToken = default);
    Task<bool> EmailExistsAsync(Email email, CancellationToken cancellationToken = default);
}
