using MediatR;
using Microsoft.AspNetCore.Mvc;

namespace EduPilot.API.Controllers;

[ApiController]
[Route("api/v1/[controller]")]
[Produces("application/json")]
public abstract class BaseApiController : ControllerBase
{
    private ISender? _mediator;
    protected ISender Mediator => _mediator ??= HttpContext.RequestServices.GetRequiredService<ISender>();

    protected IActionResult HandleResult<T>(EduPilot.Application.Common.Result<T> result)
    {
        if (result.IsSuccess)
        {
            return Ok(new ApiResponse<T>
            {
                Success = true,
                Data = result.Data
            });
        }

        return BadRequest(new ApiResponse<T>
        {
            Success = false,
            ErrorMessage = result.ErrorMessage,
            Errors = result.Errors
        });
    }

    protected IActionResult HandleResult(EduPilot.Application.Common.Result result)
    {
        if (result.IsSuccess)
        {
            return Ok(new ApiResponse
            {
                Success = true
            });
        }

        return BadRequest(new ApiResponse
        {
            Success = false,
            ErrorMessage = result.ErrorMessage,
            Errors = result.Errors
        });
    }
}

public class ApiResponse<T>
{
    public bool Success { get; set; }
    public T? Data { get; set; }
    public string? ErrorMessage { get; set; }
    public List<string> Errors { get; set; } = new();
}

public class ApiResponse
{
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
    public List<string> Errors { get; set; } = new();
}
