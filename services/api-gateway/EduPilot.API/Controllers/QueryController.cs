using EduPilot.Application.Features.Query.Commands.ProcessQuery;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;

namespace EduPilot.API.Controllers;

/// <summary>
/// AI-powered query processing endpoints
/// </summary>
[Authorize]
public class QueryController : BaseApiController
{
    /// <summary>
    /// Process a natural language query (text or voice)
    /// </summary>
    /// <param name="command">Query request with text or audio data</param>
    /// <returns>AI-generated response with source citations</returns>
    [HttpPost]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> ProcessQuery([FromBody] ProcessQueryCommand command)
    {
        var studentId = GetStudentId();
        command.StudentId = studentId;
        
        var result = await Mediator.Send(command);
        return HandleResult(result);
    }

    /// <summary>
    /// Process a voice query with audio file upload
    /// </summary>
    /// <param name="audioFile">Audio file (WAV, MP3, M4A)</param>
    /// <returns>AI-generated response with source citations</returns>
    [HttpPost("voice")]
    [Consumes("multipart/form-data")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> ProcessVoiceQuery(IFormFile audioFile)
    {
        if (audioFile == null || audioFile.Length == 0)
        {
            return BadRequest(new ApiResponse
            {
                Success = false,
                ErrorMessage = "Audio file is required"
            });
        }

        var studentId = GetStudentId();
        
        using var memoryStream = new MemoryStream();
        await audioFile.CopyToAsync(memoryStream);
        var audioData = memoryStream.ToArray();

        var command = new ProcessQueryCommand
        {
            StudentId = studentId,
            Type = "voice",
            AudioData = audioData,
            Query = string.Empty // Will be transcribed by AI service
        };

        var result = await Mediator.Send(command);
        return HandleResult(result);
    }

    private Guid GetStudentId()
    {
        var studentIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        return Guid.Parse(studentIdClaim ?? throw new UnauthorizedAccessException("Student ID not found in token"));
    }
}
