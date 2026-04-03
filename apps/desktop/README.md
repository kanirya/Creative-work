# EduPilot Desktop Application

Windows desktop application built with Electron and Next.js.

## Prerequisites

- Node.js 20+
- pnpm
- Backend services running (docker-compose up)

## Development

Run the desktop app in development mode:

```powershell
# From the root directory
cd apps/desktop
pnpm dev
```

This will:
1. Start the Next.js development server
2. Launch the Electron window

## Building

### Build for Windows
```powershell
pnpm build:win
```

Output: `dist/EduPilot Setup.exe`

### Build for macOS
```powershell
pnpm build:mac
```

### Build for Linux
```powershell
pnpm build:linux
```

## Configuration

The app connects to the backend API at:
- Default: `http://localhost:5000`
- Configure in: Environment variables or Electron store

## Features

- Offline support with local data caching
- Auto-updates via electron-updater
- Native desktop notifications
- System tray integration
- Secure credential storage

## Project Structure

```
apps/desktop/
├── main/           # Electron main process
│   ├── index.js    # Main entry point
│   └── preload.js  # Preload script
├── src/            # Next.js app (renderer process)
│   ├── app/        # App routes
│   ├── components/ # React components
│   └── lib/        # Utilities
└── package.json    # Dependencies and build config
```

## Testing

```powershell
pnpm test
```

## Troubleshooting

### App won't start
- Ensure backend services are running: `docker-compose ps`
- Check API Gateway is accessible: `http://localhost:5000`

### Build fails
- Clear cache: `rm -rf .next node_modules dist`
- Reinstall: `pnpm install`
- Rebuild: `pnpm build:win`

## Notes

- The desktop app is NOT containerized (runs natively on Windows)
- It connects to the same backend services as the web app
- Offline functionality uses local SQLite database
