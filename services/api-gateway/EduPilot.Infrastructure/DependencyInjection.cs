using EduPilot.Domain.Interfaces;
using EduPilot.Infrastructure.Persistence;
using EduPilot.Infrastructure.Persistence.Repositories;
using EduPilot.Infrastructure.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Polly;
using Polly.Extensions.Http;
using StackExchange.Redis;

namespace EduPilot.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        // Database
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseNpgsql(
                configuration.GetConnectionString("DefaultConnection"),
                npgsqlOptions => npgsqlOptions.UseVector()));

        // Repositories
        services.AddScoped<IStudentRepository, StudentRepository>();
        services.AddScoped<IUnitOfWork, UnitOfWork>();

        // Redis
        var redisConnectionString = configuration.GetConnectionString("Redis") ?? "localhost:6379";
        // Remove redis:// prefix if present
        if (redisConnectionString.StartsWith("redis://"))
        {
            redisConnectionString = redisConnectionString.Substring("redis://".Length);
        }
        var redisConnection = ConnectionMultiplexer.Connect($"{redisConnectionString},abortConnect=false");
        services.AddSingleton<IConnectionMultiplexer>(redisConnection);
        services.AddSingleton<ICacheService, RedisCacheService>();

        // Services
        services.AddScoped<IAuthenticationService, AuthenticationService>();
        services.AddSingleton<IEncryptionService, EncryptionService>();
        services.AddScoped<IFerpaAuditService, FerpaAuditService>();
        services.AddScoped<DataRetentionService>();

        // HTTP Clients with Polly retry policies
        services.AddHttpClient<IQueryProcessor, QueryProcessorHttpClient>()
            .AddPolicyHandler(GetRetryPolicy())
            .AddPolicyHandler(GetCircuitBreakerPolicy());

        services.AddHttpClient<ILMSScraperService, LMSScraperHttpClient>()
            .AddPolicyHandler(GetRetryPolicy())
            .AddPolicyHandler(GetCircuitBreakerPolicy());

        services.AddHttpClient<ITranscriptionService, TranscriptionHttpClient>()
            .AddPolicyHandler(GetRetryPolicy())
            .AddPolicyHandler(GetCircuitBreakerPolicy());

        services.AddHttpClient<ISchedulerService, SchedulerHttpClient>()
            .AddPolicyHandler(GetRetryPolicy())
            .AddPolicyHandler(GetCircuitBreakerPolicy());

        // Sync retry queue background service
        services.AddSingleton<SyncRetryQueue>();
        services.AddHostedService(sp => sp.GetRequiredService<SyncRetryQueue>());

        return services;
    }

    private static IAsyncPolicy<HttpResponseMessage> GetRetryPolicy()
    {
        return HttpPolicyExtensions
            .HandleTransientHttpError()
            .WaitAndRetryAsync(
                retryCount: 3,
                sleepDurationProvider: retryAttempt => TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)),
                onRetry: (outcome, timespan, retryAttempt, context) =>
                {
                    // Log retry attempt
                });
    }

    private static IAsyncPolicy<HttpResponseMessage> GetCircuitBreakerPolicy()
    {
        return HttpPolicyExtensions
            .HandleTransientHttpError()
            .CircuitBreakerAsync(
                handledEventsAllowedBeforeBreaking: 5,
                durationOfBreak: TimeSpan.FromSeconds(60));
    }
}
