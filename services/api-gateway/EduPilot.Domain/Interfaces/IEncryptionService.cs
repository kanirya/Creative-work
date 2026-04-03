namespace EduPilot.Domain.Interfaces;

/// <summary>
/// Service for encrypting and decrypting sensitive data at rest
/// Implements AES-256 encryption for Requirements 16.2 and 12.6
/// </summary>
public interface IEncryptionService
{
    /// <summary>
    /// Encrypts a plain text string using AES-256
    /// </summary>
    /// <param name="plainText">The text to encrypt</param>
    /// <returns>Base64-encoded encrypted string</returns>
    string Encrypt(string plainText);

    /// <summary>
    /// Decrypts an encrypted string using AES-256
    /// </summary>
    /// <param name="cipherText">Base64-encoded encrypted string</param>
    /// <returns>Decrypted plain text</returns>
    string Decrypt(string cipherText);

    /// <summary>
    /// Encrypts a byte array using AES-256
    /// </summary>
    /// <param name="plainBytes">The bytes to encrypt</param>
    /// <returns>Encrypted bytes</returns>
    byte[] EncryptBytes(byte[] plainBytes);

    /// <summary>
    /// Decrypts an encrypted byte array using AES-256
    /// </summary>
    /// <param name="cipherBytes">The encrypted bytes</param>
    /// <returns>Decrypted bytes</returns>
    byte[] DecryptBytes(byte[] cipherBytes);
}
