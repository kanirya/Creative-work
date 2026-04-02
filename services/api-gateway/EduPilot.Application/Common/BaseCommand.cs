using MediatR;

namespace EduPilot.Application.Common;

public abstract class BaseCommand<TResponse> : IRequest<TResponse>
{
}

public abstract class BaseCommand : IRequest
{
}
