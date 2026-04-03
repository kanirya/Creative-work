using EduPilot.Domain.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System.Net.Http.Json;
using System.Text.Json;

namespace EduPilot.Infrastructure.Services;

public class QueryProcessorHttpClient : IQueryProcessor
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<QueryProcessorHttpClient> _logger;
    private readonly string _agentServiceUrl;

    public QueryProcessorHttpClient(
        HttpClient httpClient,
        IConfiguration configuration,
        ILogger<QueryProcessorHttpClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
        _agentServiceUrl = configuration["ServiceUrls:AIAgentService"] ?? "http://localhost:8001";
        _httpClient.BaseAddress = new Uri(_agentServiceUrl);
        _httpClient.Timeout = TimeSpan.FromSeconds(30);
    }

    public async Task<QueryResponse> ProcessQueryAsync(QueryRequest request, CancellationToken cancellationToken = default)
    {
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
            _logger.LogError(ex, "Error calling AI Agent Service");
            return new QueryResponse
            {
                Success = false,
                ErrorMessage = "Failed to process query"
            };
        }
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
