using EduPilot.Domain.Entities;
using EduPilot.Domain.Interfaces;
using EduPilot.Domain.ValueObjects;
using EduPilot.Infrastructure.Persistence;
using EduPilot.Infrastructure.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace EduPilot.Tests.Infrastructure.Persistence;

public class LmsCredentialIntegrationTests : IDisposable
{
    private readonly ApplicationDbContext _context;
    private readonly IEncryptionService _encryptionService;
    private readonly Guid _testStudentId;

    public LmsCredentialIntegrationTests()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        _context = new ApplicationDbContext(options);

        var configuration = new ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string>
            {
                ["AES_ENCRYPTION_KEY"] = "test_encryption_key_32_bytes_long",
                ["AES_ENCRYPTION_IV"] = "test_iv_16_bytes"
            }!)
            .Build();

        _encryptionService = new EncryptionService(configuration);

        // Create a test student
        var student = Student.Create(
            Email.Create("test@iqra.edu.pk"),
            "hashed_password",
            "Test",
            "Student",
            StudentId.Create("IU2024001")
        );
        _context.Students.Add(student);
        _context.SaveChanges();
        _testStudentId = student.Id;
    }

    [Fact]
    public async Task LmsCredential_Create_ShouldStoreEncryptedCredentials()
    {
        // Arrange
        var plainUsername = "student@lms.iqra.edu.pk";
        var plainPassword = "SecurePassword123!";
        var encryptedUsername = _encryptionService.Encrypt(plainUsername);
        var encryptedPassword = _encryptionService.Encrypt(plainPassword);

        var credential = LmsCredential.Create(
            _testStudentId,
            encryptedUsername,
            encryptedPassword,
            "IqraUniversity"
        );

        // Act
        _context.LmsCredentials.Add(credential);
        await _context.SaveChangesAsync();

        // Assert
        var stored = await _context.LmsCredentials
            .FirstOrDefaultAsync(c => c.StudentId == _testStudentId);

        Assert.NotNull(stored);
        Assert.Equal(encryptedUsername, stored.EncryptedUsername);
        Assert.Equal(encryptedPassword, stored.EncryptedPassword);
        Assert.NotEqual(plainUsername, stored.EncryptedUsername);
        Assert.NotEqual(plainPassword, stored.EncryptedPassword);
    }

    [Fact]
    public async Task LmsCredential_Retrieve_ShouldDecryptCorrectly()
    {
        // Arrange
        var plainUsername = "student@lms.iqra.edu.pk";
        var plainPassword = "SecurePassword123!";
        var encryptedUsername = _encryptionService.Encrypt(plainUsername);
        var encryptedPassword = _encryptionService.Encrypt(plainPassword);

        var credential = LmsCredential.Create(
            _testStudentId,
            encryptedUsername,
            encryptedPassword,
            "IqraUniversity"
        );

        _context.LmsCredentials.Add(credential);
        await _context.SaveChangesAsync();

        // Act
        var retrieved = await _context.LmsCredentials
            .FirstOrDefaultAsync(c => c.StudentId == _testStudentId);

        var decryptedUsername = _encryptionService.Decrypt(retrieved!.EncryptedUsername);
        var decryptedPassword = _encryptionService.Decrypt(retrieved.EncryptedPassword);

        // Assert
        Assert.Equal(plainUsername, decryptedUsername);
        Assert.Equal(plainPassword, decryptedPassword);
    }

    [Fact]
    public async Task LmsCredential_Update_ShouldUpdateEncryptedCredentials()
    {
        // Arrange
        var originalUsername = "old@lms.iqra.edu.pk";
        var originalPassword = "OldPassword123!";
        var credential = LmsCredential.Create(
            _testStudentId,
            _encryptionService.Encrypt(originalUsername),
            _encryptionService.Encrypt(originalPassword),
            "IqraUniversity"
        );

        _context.LmsCredentials.Add(credential);
        await _context.SaveChangesAsync();

        var newUsername = "new@lms.iqra.edu.pk";
        var newPassword = "NewPassword456!";

        // Act
        credential.UpdateCredentials(
            _encryptionService.Encrypt(newUsername),
            _encryptionService.Encrypt(newPassword)
        );
        await _context.SaveChangesAsync();

        // Assert
        var updated = await _context.LmsCredentials
            .FirstOrDefaultAsync(c => c.StudentId == _testStudentId);

        var decryptedUsername = _encryptionService.Decrypt(updated!.EncryptedUsername);
        var decryptedPassword = _encryptionService.Decrypt(updated.EncryptedPassword);

        Assert.Equal(newUsername, decryptedUsername);
        Assert.Equal(newPassword, decryptedPassword);
    }

    [Fact]
    public async Task LmsCredential_MarkAsUsed_ShouldUpdateLastUsedAt()
    {
        // Arrange
        var credential = LmsCredential.Create(
            _testStudentId,
            _encryptionService.Encrypt("user@lms.iqra.edu.pk"),
            _encryptionService.Encrypt("password"),
            "IqraUniversity"
        );

        _context.LmsCredentials.Add(credential);
        await _context.SaveChangesAsync();

        var originalLastUsedAt = credential.LastUsedAt;
        await Task.Delay(100); // Ensure time difference

        // Act
        credential.MarkAsUsed();
        await _context.SaveChangesAsync();

        // Assert
        var updated = await _context.LmsCredentials
            .FirstOrDefaultAsync(c => c.StudentId == _testStudentId);

        Assert.True(updated!.LastUsedAt > originalLastUsedAt);
    }

    [Fact]
    public async Task LmsCredential_Deactivate_ShouldSetIsActiveFalse()
    {
        // Arrange
        var credential = LmsCredential.Create(
            _testStudentId,
            _encryptionService.Encrypt("user@lms.iqra.edu.pk"),
            _encryptionService.Encrypt("password"),
            "IqraUniversity"
        );

        _context.LmsCredentials.Add(credential);
        await _context.SaveChangesAsync();

        // Act
        credential.Deactivate();
        await _context.SaveChangesAsync();

        // Assert
        var updated = await _context.LmsCredentials
            .FirstOrDefaultAsync(c => c.StudentId == _testStudentId);

        Assert.False(updated!.IsActive);
    }

    [Fact]
    public async Task LmsCredential_Activate_ShouldSetIsActiveTrue()
    {
        // Arrange
        var credential = LmsCredential.Create(
            _testStudentId,
            _encryptionService.Encrypt("user@lms.iqra.edu.pk"),
            _encryptionService.Encrypt("password"),
            "IqraUniversity"
        );

        credential.Deactivate();
        _context.LmsCredentials.Add(credential);
        await _context.SaveChangesAsync();

        // Act
        credential.Activate();
        await _context.SaveChangesAsync();

        // Assert
        var updated = await _context.LmsCredentials
            .FirstOrDefaultAsync(c => c.StudentId == _testStudentId);

        Assert.True(updated!.IsActive);
    }

    [Fact]
    public void LmsCredential_Create_WithEmptyStudentId_ShouldThrowException()
    {
        // Arrange
        var emptyStudentId = Guid.Empty;

        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
            LmsCredential.Create(
                emptyStudentId,
                _encryptionService.Encrypt("username"),
                _encryptionService.Encrypt("password"),
                "IqraUniversity"
            )
        );
    }

    [Fact]
    public void LmsCredential_Create_WithEmptyUsername_ShouldThrowException()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
            LmsCredential.Create(
                _testStudentId,
                string.Empty,
                _encryptionService.Encrypt("password"),
                "IqraUniversity"
            )
        );
    }

    [Fact]
    public void LmsCredential_Create_WithEmptyPassword_ShouldThrowException()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
            LmsCredential.Create(
                _testStudentId,
                _encryptionService.Encrypt("username"),
                string.Empty,
                "IqraUniversity"
            )
        );
    }

    [Fact]
    public void LmsCredential_Create_WithEmptyPlatform_ShouldThrowException()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
            LmsCredential.Create(
                _testStudentId,
                _encryptionService.Encrypt("username"),
                _encryptionService.Encrypt("password"),
                string.Empty
            )
        );
    }

    public void Dispose()
    {
        _context.Database.EnsureDeleted();
        _context.Dispose();
    }
}
