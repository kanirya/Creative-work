using EduPilot.Application.Features.Authentication.Commands.AuthenticateStudent;
using EduPilot.Application.Features.Authentication.Commands.RefreshToken;
using EduPilot.Application.Features.Authentication.Queries.ValidateToken;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace EduPilot.API.Controllers;

/// <summary>
/// Authentication endpoints for student login and token management
/// </summary>
public class AuthController : BaseApiController
{
    /// <summary>
    /// Authenticate a student with email and password
    /// </summary>
    /// <param name="command">Login credentials</param>
    /// <returns>JWT tokens and student information</returns>
    [HttpPost("login")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Login([FromBody] AuthenticateStudentCommand command)
    {
        var result = await Mediator.Send(command);
        return HandleResult(result);
    }

    /// <summary>
    /// Refresh an expired access token using a refresh token
    /// </summary>
    /// <param name="command">Refresh token</param>
    /// <returns>New JWT tokens</returns>
    [HttpPost("refresh")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> RefreshToken([FromBody] RefreshTokenCommand command)
    {
        var result = await Mediator.Send(command);
        return HandleResult(result);
    }

    /// <summary>
    /// Validate a JWT access token
    /// </summary>
    /// <param name="token">JWT token to validate</param>
    /// <returns>Validation result</returns>
    [HttpGet("validate")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status200OK)]
    public async Task<IActionResult> ValidateToken([FromQuery] string token)
    {
        var result = await Mediator.Send(new ValidateTokenQuery { Token = token });
        return HandleResult(result);
    }
}
