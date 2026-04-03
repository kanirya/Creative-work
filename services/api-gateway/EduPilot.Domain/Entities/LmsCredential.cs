using EduPilot.Domain.Common;

namespace EduPilot.Domain.Entities;

/// <summary>
/// Stores encrypted LMS credentials for students
/// Sensitive data is encrypted at rest using AES-256
/// </summary>
public class LmsCredential : BaseEntity
{
    public Guid StudentId { get; private set; }
    public Student Student { get; private set; } = null!;
    
    /// <summary>
    /// Encrypted LMS username/email
    /// </summary>
    public string EncryptedUsername { get; private set; }
    
    /// <summary>
    /// Encrypted LMS password
    /// </summary>
    public string EncryptedPassword { get; private set; }
    
    /// <summary>
    /// LMS platform identifier (e.g., "IqraUniversity", "Moodle")
    /// </summary>
    public string Platform { get; private set; }
    
    public DateTime LastUsedAt { get; private set; }
    public bool IsActive { get; private set; }

    private LmsCredential() { } // For EF Core

    private LmsCredential(
        Guid studentId,
        string encryptedUsername,
        string encryptedPassword,
        string platform)
    {
        StudentId = studentId;
        EncryptedUsername = encryptedUsername ?? throw new ArgumentNullException(nameof(encryptedUsername));
        EncryptedPassword = encryptedPassword ?? throw new ArgumentNullException(nameof(encryptedPassword));
        Platform = platform ?? throw new ArgumentNullException(nameof(platform));
        LastUsedAt = DateTime.UtcNow;
        IsActive = true;
    }

    public static LmsCredential Create(
        Guid studentId,
        string encryptedUsername,
        string encryptedPassword,
        string platform)
    {
        if (studentId == Guid.Empty)
            throw new ArgumentException("Student ID cannot be empty", nameof(studentId));

        if (string.IsNullOrWhiteSpace(encryptedUsername))
            throw new ArgumentException("Encrypted username cannot be empty", nameof(encryptedUsername));

        if (string.IsNullOrWhiteSpace(encryptedPassword))
            throw new ArgumentException("Encrypted password cannot be empty", nameof(encryptedPassword));

        if (string.IsNullOrWhiteSpace(platform))
            throw new ArgumentException("Platform cannot be empty", nameof(platform));

        return new LmsCredential(studentId, encryptedUsername, encryptedPassword, platform);
    }

    public void UpdateCredentials(string encryptedUsername, string encryptedPassword)
    {
        if (string.IsNullOrWhiteSpace(encryptedUsername))
            throw new ArgumentException("Encrypted username cannot be empty", nameof(encryptedUsername));

        if (string.IsNullOrWhiteSpace(encryptedPassword))
            throw new ArgumentException("Encrypted password cannot be empty", nameof(encryptedPassword));

        EncryptedUsername = encryptedUsername;
        EncryptedPassword = encryptedPassword;
        UpdateTimestamp();
    }

    public void MarkAsUsed()
    {
        LastUsedAt = DateTime.UtcNow;
        UpdateTimestamp();
    }

    public void Deactivate()
    {
        IsActive = false;
        UpdateTimestamp();
    }

    public void Activate()
    {
        IsActive = true;
        UpdateTimestamp();
    }
}
