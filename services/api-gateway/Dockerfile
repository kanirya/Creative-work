# Multi-stage build for .NET 8 API Gateway
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy project files
COPY ["EduPilot.API/EduPilot.API.csproj", "EduPilot.API/"]
COPY ["EduPilot.Application/EduPilot.Application.csproj", "EduPilot.Application/"]
COPY ["EduPilot.Domain/EduPilot.Domain.csproj", "EduPilot.Domain/"]
COPY ["EduPilot.Infrastructure/EduPilot.Infrastructure.csproj", "EduPilot.Infrastructure/"]

# Restore dependencies
RUN dotnet restore "EduPilot.API/EduPilot.API.csproj"

# Copy all source code
COPY . .

# Build the application
WORKDIR "/src/EduPilot.API"
RUN dotnet build "EduPilot.API.csproj" -c Release -o /app/build

# Publish the application
FROM build AS publish
RUN dotnet publish "EduPilot.API.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Final stage - runtime image
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app

# Install curl for health checks
USER root
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Copy published application
COPY --from=publish /app/publish .

# Expose port
EXPOSE 8080

# Set environment variables
ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the application
ENTRYPOINT ["dotnet", "EduPilot.API.dll"]
