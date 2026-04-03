using System.Security.Cryptography;
using System.Text;
using EduPilot.Domain.Interfaces;
using Microsoft.Extensions.Configuration;

namespace EduPilot.Infrastructure.Services;

/// <summary>
/// Provides AES-256 encryption and decryption for sensitive data at rest
/// Implements Requirements 16.2 and 12.6 for data encryption
/// </summary>
public class EncryptionService : IEncryptionService
{
    private readonly byte[] _key;
    private readonly byte[] _iv;

    public EncryptionService(IConfiguration configuration)
    {
        var keyString = configuration["AES_ENCRYPTION_KEY"] 
            ?? throw new InvalidOperationException("AES_ENCRYPTION_KEY not configured");
        var ivString = configuration["AES_ENCRYPTION_IV"] 
            ?? throw new InvalidOperationException("AES_ENCRYPTION_IV not configured");

        // Ensure key is 32 bytes (256 bits) for AES-256
        _key = DeriveKey(keyString, 32);
        // Ensure IV is 16 bytes (128 bits)
        _iv = DeriveKey(ivString, 16);
    }

    public string Encrypt(string plainText)
    {
        if (string.IsNullOrEmpty(plainText))
            return plainText;

        using var aes = Aes.Create();
        aes.Key = _key;
        aes.IV = _iv;
        aes.Mode = CipherMode.CBC;
        aes.Padding = PaddingMode.PKCS7;

        using var encryptor = aes.CreateEncryptor();
        var plainBytes = Encoding.UTF8.GetBytes(plainText);
        var encryptedBytes = encryptor.TransformFinalBlock(plainBytes, 0, plainBytes.Length);

        return Convert.ToBase64String(encryptedBytes);
    }

    public string Decrypt(string cipherText)
    {
        if (string.IsNullOrEmpty(cipherText))
            return cipherText;

        try
        {
            using var aes = Aes.Create();
            aes.Key = _key;
            aes.IV = _iv;
            aes.Mode = CipherMode.CBC;
            aes.Padding = PaddingMode.PKCS7;

            using var decryptor = aes.CreateDecryptor();
            var cipherBytes = Convert.FromBase64String(cipherText);
            var decryptedBytes = decryptor.TransformFinalBlock(cipherBytes, 0, cipherBytes.Length);

            return Encoding.UTF8.GetString(decryptedBytes);
        }
        catch (CryptographicException)
        {
            // If decryption fails, the data might not be encrypted or key is wrong
            throw new InvalidOperationException("Failed to decrypt data. Invalid encryption key or corrupted data.");
        }
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

        try
        {
            using var aes = Aes.Create();
            aes.Key = _key;
            aes.IV = _iv;
            aes.Mode = CipherMode.CBC;
            aes.Padding = PaddingMode.PKCS7;

            using var decryptor = aes.CreateDecryptor();
            return decryptor.TransformFinalBlock(cipherBytes, 0, cipherBytes.Length);
        }
        catch (CryptographicException)
        {
            throw new InvalidOperationException("Failed to decrypt data. Invalid encryption key or corrupted data.");
        }
    }

    /// <summary>
    /// Derives a key of specified length from a string using SHA-256
    /// </summary>
    private static byte[] DeriveKey(string input, int length)
    {
        using var sha256 = SHA256.Create();
        var hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(input));
        
        if (hash.Length >= length)
        {
            var key = new byte[length];
            Array.Copy(hash, key, length);
            return key;
        }
        
        // If hash is shorter than needed, repeat it
        var result = new byte[length];
        for (int i = 0; i < length; i++)
        {
            result[i] = hash[i % hash.Length];
        }
        return result;
    }
}
