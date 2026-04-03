using System.Security.Cryptography;
using System.Text;

namespace EduPilot.Infrastructure.Security;

/// <summary>
/// Service for encrypting and decrypting sensitive data at rest using AES-256
/// </summary>
public interface IEncryptionService
{
    string Encrypt(string plainText);
    string Decrypt(string cipherText);
    byte[] EncryptBytes(byte[] plainBytes);
    byte[] DecryptBytes(byte[] cipherBytes);
}

public class EncryptionService : IEncryptionService
{
    private readonly byte[] _key;
    private readonly byte[] _iv;

    public EncryptionService(string encryptionKey)
    {
        if (string.IsNullOrWhiteSpace(encryptionKey))
            throw new ArgumentException("Encryption key cannot be empty", nameof(encryptionKey));

        // Derive key and IV from the encryption key using PBKDF2
        using var deriveBytes = new Rfc2898DeriveBytes(
            encryptionKey,
            Encoding.UTF8.GetBytes("EduPilot-Salt-2024"), // Salt
            100000, // Iterations
            HashAlgorithmName.SHA256);

        _key = deriveBytes.GetBytes(32); // 256 bits for AES-256
        _iv = deriveBytes.GetBytes(16);  // 128 bits for IV
    }

    public string Encrypt(string plainText)
    {
        if (string.IsNullOrEmpty(plainText))
            return plainText;

        var plainBytes = Encoding.UTF8.GetBytes(plainText);
        var encryptedBytes = EncryptBytes(plainBytes);
        return Convert.ToBase64String(encryptedBytes);
    }

    public string Decrypt(string cipherText)
    {
        if (string.IsNullOrEmpty(cipherText))
            return cipherText;

        var cipherBytes = Convert.FromBase64String(cipherText);
        var decryptedBytes = DecryptBytes(cipherBytes);
        return Encoding.UTF8.GetString(decryptedBytes);
    }

    public byte[] EncryptBytes(byte[] plainBytes)
    {
        if (plainBytes == null || plainBytes.Length == 0)
            return plainBytes;

        using var aes = Aes.Create();
        aes.Key = _key;
        aes.IV = _iv;
        aes.Mode = CipherMode.CBC;
        aes.Padding = PaddingMode.PKCS7;

        using var encryptor = aes.CreateEncryptor();
        return encryptor.TransformFinalBlock(plainBytes, 0, plainBytes.Length);
    }

    public byte[] DecryptBytes(byte[] cipherBytes)
    {
        if (cipherBytes == null || cipherBytes.Length == 0)
            return cipherBytes;

        using var aes = Aes.Create();
        aes.Key = _key;
        aes.IV = _iv;
        aes.Mode = CipherMode.CBC;
        aes.Padding = PaddingMode.PKCS7;

        using var decryptor = aes.CreateDecryptor();
        return decryptor.TransformFinalBlock(cipherBytes, 0, cipherBytes.Length);
    }
}
