using EduPilot.Domain.Entities;
using EduPilot.Domain.Interfaces;
using EduPilot.Domain.ValueObjects;
using Microsoft.EntityFrameworkCore;

namespace EduPilot.Infrastructure.Persistence.Repositories;

public class StudentRepository : Repository<Student>, IStudentRepository
{
    public StudentRepository(ApplicationDbContext context) : base(context)
    {
    }

    public async Task<Student?> GetByEmailAsync(Email email, CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .FirstOrDefaultAsync(s => s.Email == email, cancellationToken);
    }

    public async Task<Student?> GetByUniversityIdAsync(StudentId universityId, CancellationToken cancellationToken = default)
    {
        return await _dbSet
            .FirstOrDefaultAsync(s => s.UniversityId == universityId, cancellationToken);
    }

    public async Task<IEnumerable<Course>> GetCoursesAsync(Guid studentId, CancellationToken cancellationToken = default)
    {
        var student = await _dbSet
            .Include(s => s.Courses)
            .FirstOrDefaultAsync(s => s.Id == studentId, cancellationToken);

        return student?.Courses ?? Enumerable.Empty<Course>();
    }

    public async Task<IEnumerable<Assignment>> GetAssignmentsAsync(Guid studentId, CancellationToken cancellationToken = default)
    {
        var student = await _dbSet
            .Include(s => s.Courses)
                .ThenInclude(c => c.Assignments)
            .FirstOrDefaultAsync(s => s.Id == studentId, cancellationToken);

        return student?.Courses
            .SelectMany(c => c.Assignments)
            .OrderBy(a => a.DueDate)
            ?? Enumerable.Empty<Assignment>();
    }

    public async Task<IEnumerable<Assignment>> GetUpcomingAssignmentsAsync(
        Guid studentId, 
        int days = 7, 
        CancellationToken cancellationToken = default)
    {
        var cutoffDate = DateTime.UtcNow.AddDays(days);
        
        var student = await _dbSet
            .Include(s => s.Courses)
                .ThenInclude(c => c.Assignments)
            .FirstOrDefaultAsync(s => s.Id == studentId, cancellationToken);

        return student?.Courses
            .SelectMany(c => c.Assignments)
            .Where(a => a.DueDate >= DateTime.UtcNow && a.DueDate <= cutoffDate)
            .OrderBy(a => a.DueDate)
            ?? Enumerable.Empty<Assignment>();
    }

    public async Task<IEnumerable<Announcement>> GetAnnouncementsAsync(Guid studentId, CancellationToken cancellationToken = default)
    {
        var student = await _dbSet
            .Include(s => s.Courses)
                .ThenInclude(c => c.Announcements)
            .FirstOrDefaultAsync(s => s.Id == studentId, cancellationToken);

        return student?.Courses
            .SelectMany(c => c.Announcements)
            .OrderByDescending(a => a.PostedAt)
            ?? Enumerable.Empty<Announcement>();
    }

    public async Task<bool> EmailExistsAsync(Email email, CancellationToken cancellationToken = default)
    {
        return await _dbSet.AnyAsync(s => s.Email == email, cancellationToken);
    }
}
