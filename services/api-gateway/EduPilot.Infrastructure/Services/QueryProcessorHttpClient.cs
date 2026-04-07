using EduPilot.Domain.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace EduPilot.Infrastructure.Services;

public class QueryProcessorHttpClient : IQueryProcessor
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<QueryProcessorHttpClient> _logger;
    private readonly ICacheService _cacheService;
    private readonly string _agentServiceUrl;

    public QueryProcessorHttpClient(
        HttpClient httpClient,
        IConfiguration configuration,
        ILogger<QueryProcessorHttpClient> logger,
        ICacheService cacheService)
    {
        _httpClient = httpClient;
        _logger = logger;
        _cacheService = cacheService;
        _agentServiceUrl = configuration["ServiceUrls:AIAgentService"] ?? "http://localhost:8001";
        _httpClient.BaseAddress = new Uri(_agentServiceUrl);
        _httpClient.Timeout = TimeSpan.FromSeconds(30);
    }

    private static string ComputeQueryHash(string query)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(query.ToLowerInvariant().Trim()));
        return Convert.ToHexString(bytes)[..16];
    }

    public async Task<QueryResponse> ProcessQueryAsync(QueryRequest request, CancellationToken cancellationToken = default)
    {
        var cacheKey = $"query_cache:{request.StudentId}:{ComputeQueryHash(request.Query)}";

        try
        {
            _logger.LogInformation("Sending query to AI Agent Service for student {StudentId}", request.StudentId);

            var response = await _httpClient.PostAsJsonAsync("/query", new
            {
                student_id = request.StudentId.ToString(),
                query = request.Query,
                query_type = request.Type.ToString().ToLower()
            }, cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogError("AI Agent Service returned error: {StatusCode}", response.StatusCode);
                return await GetCachedFallbackAsync(cacheKey, $"AI Agent Service returned error: {response.StatusCode}");
            }

            var result = await response.Content.ReadFromJsonAsync<AgentServiceResponse>(cancellationToken);

            if (result == null)
            {
                return await GetCachedFallbackAsync(cacheKey, "Failed to parse AI Agent Service response");
            }

            var queryResponse = new QueryResponse
            {
                Success = true,
                Answer = result.Answer,
                ConfidenceScore = result.ConfidenceScore,
                Sources = result.Sources.Select(s => new SourceCitation
                {
                    DocumentType = s.DocumentType,
                    Title = s.Title,
                    Excerpt = s.Excerpt,
                    Url = s.Url
                }).ToList()
            };

            // Cache successful response for fallback
            await _cacheService.SetAsync(cacheKey, JsonSerializer.Serialize(queryResponse), TimeSpan.FromHours(1));

            return queryResponse;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling AI Agent Service");
            return await GetCachedFallbackAsync(cacheKey, "Failed to process query");
        }
    }

    private async Task<QueryResponse> GetCachedFallbackAsync(string cacheKey, string errorMessage)
    {
        var cached = await _cacheService.GetAsync<string>(cacheKey);
        if (cached != null)
        {
            _logger.LogWarning("AI Agent unavailable — returning cached response for key {CacheKey}", cacheKey);
            var cachedResponse = JsonSerializer.Deserialize<QueryResponse>(cached);
            if (cachedResponse != null)
            {
                cachedResponse.Answer = $"[Cached response] {cachedResponse.Answer}";
                return cachedResponse;
            }
        }

        return new QueryResponse { Success = false, ErrorMessage = errorMessage };
    }

    public async Task<QueryResponse> ProcessVoiceQueryAsync(VoiceQueryRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation("Sending voice query to AI Agent Service for student {StudentId}", request.StudentId);

            using var content = new MultipartFormDataContent();
            content.Add(new StringContent(request.StudentId.ToString()), "student_id");
            content.Add(new ByteArrayContent(request.AudioData), "audio", "audio.wav");

            var response = await _httpClient.PostAsync("/query/voice", content, cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogError("AI Agent Service returned error: {StatusCode}", response.StatusCode);
                return new QueryResponse
                {
                    Success = false,
                    ErrorMessage = $"AI Agent Service returned error: {response.StatusCode}"
                };
            }

            var result = await response.Content.ReadFromJsonAsync<AgentServiceResponse>(cancellationToken);

            if (result == null)
            {
                return new QueryResponse
                {
                    Success = false,
                    ErrorMessage = "Failed to parse AI Agent Service response"
                };
            }

            return new QueryResponse
            {
                Success = true,
                Answer = result.Answer,
                ConfidenceScore = result.ConfidenceScore,
                Sources = result.Sources.Select(s => new SourceCitation
                {
                    DocumentType = s.DocumentType,
                    Title = s.Title,
                    Excerpt = s.Excerpt,
                    Url = s.Url
                }).ToList()
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling AI Agent Service for voice query");
            return new QueryResponse
            {
                Success = false,
                ErrorMessage = "Failed to process voice query"
            };
        }
    }

    private class AgentServiceResponse
    {
        public string Answer { get; set; } = string.Empty;
        public float ConfidenceScore { get; set; }
        public List<AgentSourceCitation> Sources { get; set; } = new();
    }

    private class AgentSourceCitation
    {
        public string DocumentType { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public string Excerpt { get; set; } = string.Empty;
        public string? Url { get; set; }
    }
}
