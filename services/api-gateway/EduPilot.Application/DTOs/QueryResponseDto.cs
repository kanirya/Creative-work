namespace EduPilot.Application.DTOs;

public class QueryResponseDto
{
    public string Answer { get; set; } = string.Empty;
    public List<SourceCitationDto> Sources { get; set; } = new();
    public float ConfidenceScore { get; set; }
}

public class SourceCitationDto
{
    public string DocumentType { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Excerpt { get; set; } = string.Empty;
    public string? Url { get; set; }
}
