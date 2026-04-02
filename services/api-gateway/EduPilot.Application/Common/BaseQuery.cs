using MediatR;

namespace EduPilot.Application.Common;

public abstract class BaseQuery<TResponse> : IRequest<TResponse>
{
}
