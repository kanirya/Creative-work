namespace EduPilot.Domain.Interfaces;

public interface INotificationService
{
    Task SendEmailAsync(string to, string subject, string body, CancellationToken cancellationToken = default);
    Task SendWhatsAppAsync(string phoneNumber, string message, CancellationToken cancellationToken = default);
    Task SendTelegramAsync(long chatId, string message, CancellationToken cancellationToken = default);
    Task SendPushNotificationAsync(Guid studentId, string title, string message, CancellationToken cancellationToken = default);
}
