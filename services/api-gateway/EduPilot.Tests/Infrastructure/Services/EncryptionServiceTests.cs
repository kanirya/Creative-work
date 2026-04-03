using EduPilot.Infrastructure.Services;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace EduPilot.Tests.Infrastructure.Services;

public class EncryptionServiceTests
{
    private readonly EncryptionService _encryptionService;

    public EncryptionServiceTests()
    {
        var configuration = new ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string>
            {
                ["AES_ENCRYPTION_KEY"] = "test_encryption_key_32_bytes_long",
                ["AES_ENCRYPTION_IV"] = "test_iv_16_bytes"
            }!)
            .Build();

        _encryptionService = new EncryptionService(configuration);
    }

    [Fact]
    public void Encrypt_WithValidPlainText_ShouldReturnEncryptedString()
    {
        // Arrange
        var plainText = "sensitive data";

        // Act
        var encrypted = _encryptionService.Encrypt(plainText);

        // Assert
        Assert.NotNull(encrypted);
        Assert.NotEqual(plainText, encrypted);
        Assert.True(encrypted.Length > 0);
    }

    [Fact]
    public void Decrypt_WithValidCipherText_ShouldReturnOriginalPlainText()
    {
        // Arrange
        var plainText = "sensitive data";
        var encrypted = _encryptionService.Encrypt(plainText);

        // Act
        var decrypted = _encryptionService.Decrypt(encrypted);

        // Assert
        Assert.Equal(plainText, decrypted);
    }

    [Fact]
    public void Encrypt_Decrypt_RoundTrip_ShouldReturnOriginalText()
    {
        // Arrange
        var plainText = "This is a test message with special characters: !@#$%^&*()";

        // Act
        var encrypted = _encryptionService.Encrypt(plainText);
        var decrypted = _encryptionService.Decrypt(encrypted);

        // Assert
        Assert.Equal(plainText, decrypted);
    }

    [Fact]
    public void Encrypt_WithEmptyString_ShouldReturnEmptyString()
    {
        // Arrange
        var plainText = string.Empty;

        // Act
        var encrypted = _encryptionService.Encrypt(plainText);

        // Assert
        Assert.Equal(string.Empty, encrypted);
    }

    [Fact]
    public void Encrypt_WithNull_ShouldReturnNull()
    {
        // Arrange
        string? plainText = null;

        // Act
        var encrypted = _encryptionService.Encrypt(plainText!);

        // Assert
        Assert.Null(encrypted);
    }

    [Fact]
    public void Decrypt_WithEmptyString_ShouldReturnEmptyString()
    {
        // Arrange
        var cipherText = string.Empty;

        // Act
        var decrypted = _encryptionService.Decrypt(cipherText);

        // Assert
        Assert.Equal(string.Empty, decrypted);
    }

    [Fact]
    public void Decrypt_WithNull_ShouldReturnNull()
    {
        // Arrange
        string? cipherText = null;

        // Act
        var decrypted = _encryptionService.Decrypt(cipherText!);

        // Assert
        Assert.Null(decrypted);
    }

    [Fact]
    public void Encrypt_SameTextTwice_ShouldProduceSameResult()
    {
        // Arrange
        var plainText = "consistent encryption test";

        // Act
        var encrypted1 = _encryptionService.Encrypt(plainText);
        var encrypted2 = _encryptionService.Encrypt(plainText);

        // Assert
        Assert.Equal(encrypted1, encrypted2);
    }

    [Fact]
    public void Decrypt_WithInvalidCipherText_ShouldThrowException()
    {
        // Arrange
        var invalidCipherText = "this is not valid base64 encrypted data!@#$";

        // Act & Assert
        Assert.Throws<FormatException>(() => _encryptionService.Decrypt(invalidCipherText));
    }

    [Fact]
    public void EncryptBytes_WithValidData_ShouldReturnEncryptedBytes()
    {
        // Arrange
        var plainBytes = System.Text.Encoding.UTF8.GetBytes("binary data");

        // Act
        var encryptedBytes = _encryptionService.EncryptBytes(plainBytes);

        // Assert
        Assert.NotNull(encryptedBytes);
        Assert.NotEqual(plainBytes, encryptedBytes);
        Assert.True(encryptedBytes.Length > 0);
    }

    [Fact]
    public void DecryptBytes_WithValidCipherBytes_ShouldReturnOriginalBytes()
    {
        // Arrange
        var plainBytes = System.Text.Encoding.UTF8.GetBytes("binary data");
        var encryptedBytes = _encryptionService.EncryptBytes(plainBytes);

        // Act
        var decryptedBytes = _encryptionService.DecryptBytes(encryptedBytes);

        // Assert
        Assert.Equal(plainBytes, decryptedBytes);
    }

    [Fact]
    public void EncryptBytes_Decrypt_RoundTrip_ShouldReturnOriginalBytes()
    {
        // Arrange
        var plainBytes = System.Text.Encoding.UTF8.GetBytes("Round trip test for bytes");

        // Act
        var encryptedBytes = _encryptionService.EncryptBytes(plainBytes);
        var decryptedBytes = _encryptionService.DecryptBytes(encryptedBytes);

        // Assert
        Assert.Equal(plainBytes, decryptedBytes);
    }

    [Fact]
    public void EncryptBytes_WithEmptyArray_ShouldReturnEmptyArray()
    {
        // Arrange
        var plainBytes = Array.Empty<byte>();

        // Act
        var encryptedBytes = _encryptionService.EncryptBytes(plainBytes);

        // Assert
        Assert.Empty(encryptedBytes);
    }

    [Fact]
    public void EncryptBytes_WithNull_ShouldReturnNull()
    {
        // Arrange
        byte[]? plainBytes = null;

        // Act
        var encryptedBytes = _encryptionService.EncryptBytes(plainBytes!);

        // Assert
        Assert.Null(encryptedBytes);
    }

    [Fact]
    public void Encrypt_LongText_ShouldHandleCorrectly()
    {
        // Arrange
        var longText = new string('A', 10000); // 10KB of text

        // Act
        var encrypted = _encryptionService.Encrypt(longText);
        var decrypted = _encryptionService.Decrypt(encrypted);

        // Assert
        Assert.Equal(longText, decrypted);
    }

    [Fact]
    public void Encrypt_UnicodeText_ShouldHandleCorrectly()
    {
        // Arrange
        var unicodeText = "Hello 世界 مرحبا мир 🌍";

        // Act
        var encrypted = _encryptionService.Encrypt(unicodeText);
        var decrypted = _encryptionService.Decrypt(encrypted);

        // Assert
        Assert.Equal(unicodeText, decrypted);
    }

    [Theory]
    [InlineData("password123")]
    [InlineData("user@example.com")]
    [InlineData("API_KEY_12345")]
    [InlineData("refresh_token_xyz")]
    public void Encrypt_Decrypt_VariousInputs_ShouldWorkCorrectly(string input)
    {
        // Act
        var encrypted = _encryptionService.Encrypt(input);
        var decrypted = _encryptionService.Decrypt(encrypted);

        // Assert
        Assert.Equal(input, decrypted);
        Assert.NotEqual(input, encrypted);
    }
}
