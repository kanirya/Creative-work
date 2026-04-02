namespace EduPilot.Domain.Interfaces;

public interface IQueryProcessor
{
    Task<QueryResponse> ProcessQueryAsync(QueryRequest request, CancellationToken cancellationToken = default);
    Task<QueryResponse> ProcessVoiceQueryAsync(VoiceQueryRequest request, CancellationToken cancellationToken = default);
}

public class QueryRequest
{
    public Guid StudentId { get; set; }
    public string Query { get; set; } = string.Empty;
    public QueryType Type { get; set; }
}

public class VoiceQueryRequest
{
    public Guid StudentId { get; set; }
    public byte[] AudioData { get; set; } = Array.Empty<byte>();
}

public class QueryResponse
{
    public string Answer { get; set; } = string.Empty;
    public List<SourceCitation> Sources { get; set; } = new();
    public float ConfidenceScore { get; set; }
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
}

public class SourceCitation
{
    public string DocumentType { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Excerpt { get; set; } = string.Empty;
    public string? Url { get; set; }
}

public enum QueryType
{
    Text = 0,
    Voice = 1
}
