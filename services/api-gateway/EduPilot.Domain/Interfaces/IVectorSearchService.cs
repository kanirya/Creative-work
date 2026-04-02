namespace EduPilot.Domain.Interfaces;

public interface IVectorSearchService
{
    Task<IEnumerable<SearchResult>> SearchAsync(
        Guid studentId,
        string query,
        int topK = 5,
        CancellationToken cancellationToken = default);

    Task<IEnumerable<SearchResult>> SearchByTypeAsync(
        Guid studentId,
        string query,
        string documentType,
        int topK = 5,
        CancellationToken cancellationToken = default);

    Task StoreEmbeddingAsync(
        Guid studentId,
        string documentType,
        Guid documentId,
        string content,
        Dictionary<string, object>? metadata = null,
        CancellationToken cancellationToken = default);
}

public class SearchResult
{
    public Guid DocumentId { get; set; }
    public string DocumentType { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public float SimilarityScore { get; set; }
    public Dictionary<string, object>? Metadata { get; set; }
}
