namespace EduPilot.Application.DTOs;

public class QueryRequestDto
{
    public string Query { get; set; } = string.Empty;
    public string Type { get; set; } = "text"; // "text" or "voice"
    public byte[]? AudioData { get; set; }
}
