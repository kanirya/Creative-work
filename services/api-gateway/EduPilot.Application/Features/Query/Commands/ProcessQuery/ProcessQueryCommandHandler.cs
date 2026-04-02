using EduPilot.Application.Common;
using EduPilot.Application.DTOs;
using EduPilot.Domain.Interfaces;
using MediatR;
using Microsoft.Extensions.Logging;

namespace EduPilot.Application.Features.Query.Commands.ProcessQuery;

public class ProcessQueryCommandHandler : IRequestHandler<ProcessQueryCommand, Result<QueryResponseDto>>
{
    private readonly IQueryProcessor _queryProcessor;
    private readonly ILogger<ProcessQueryCommandHandler> _logger;

    public ProcessQueryCommandHandler(
        IQueryProcessor queryProcessor,
        ILogger<ProcessQueryCommandHandler> logger)
    {
        _queryProcessor = queryProcessor;
        _logger = logger;
    }

    public async Task<Result<QueryResponseDto>> Handle(ProcessQueryCommand request, CancellationToken cancellationToken)
    {
        try
        {
            _logger.LogInformation("Processing query for student {StudentId}: {Query}", request.StudentId, request.Query);

            Domain.Interfaces.QueryResponse response;

            if (request.Type.Equals("voice", StringComparison.OrdinalIgnoreCase) && request.AudioData != null)
            {
                var voiceRequest = new VoiceQueryRequest
                {
                    StudentId = request.StudentId,
                    AudioData = request.AudioData
                };
                response = await _queryProcessor.ProcessVoiceQueryAsync(voiceRequest, cancellationToken);
            }
            else
            {
                var queryRequest = new Domain.Interfaces.QueryRequest
                {
                    StudentId = request.StudentId,
                    Query = request.Query,
                    Type = request.Type.Equals("voice", StringComparison.OrdinalIgnoreCase) 
                        ? Domain.Interfaces.QueryType.Voice 
                        : Domain.Interfaces.QueryType.Text
                };
                response = await _queryProcessor.ProcessQueryAsync(queryRequest, cancellationToken);
            }

            if (!response.Success)
            {
                _logger.LogWarning("Query processing failed for student {StudentId}: {Error}", 
                    request.StudentId, response.ErrorMessage);
                return Result<QueryResponseDto>.Failure(response.ErrorMessage ?? "Query processing failed");
            }

            var responseDto = new QueryResponseDto
            {
                Answer = response.Answer,
                ConfidenceScore = response.ConfidenceScore,
                Sources = response.Sources.Select(s => new SourceCitationDto
                {
                    DocumentType = s.DocumentType,
                    Title = s.Title,
                    Excerpt = s.Excerpt,
                    Url = s.Url
                }).ToList()
            };

            _logger.LogInformation("Query processed successfully for student {StudentId} with confidence {Confidence}", 
                request.StudentId, response.ConfidenceScore);

            return Result<QueryResponseDto>.Success(responseDto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing query for student {StudentId}", request.StudentId);
            return Result<QueryResponseDto>.Failure("An error occurred while processing your query");
        }
    }
}
