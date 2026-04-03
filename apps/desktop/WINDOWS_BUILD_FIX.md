# Windows Desktop App - Build Fix

## Issue
The build fails due to Windows requiring administrator privileges to create symbolic links for code signing tools.

## Solutions

### Option 1: Run in Development Mode (Recommended)
Instead of building an installer, run the app directly in development mode:

```powershell
# Stop the web Docker container to free port 3000
docker-compose stop web

# Run the desktop app
cd apps/desktop
pnpm dev
```

This will open the Electron window without needing to build an installer.

### Option 2: Build as Administrator
Run PowerShell as Administrator and then build:

1. Right-click PowerShell
2. Select "Run as Administrator"
3. Navigate to the project:
   ```powershell
   cd "C:\Creative work\apps\desktop"
   pnpm build:win
   ```

### Option 3: Enable Developer Mode (Windows 10/11)
Enable Developer Mode to allow symlink creation without admin rights:

1. Open Settings
2. Go to "Update & Security" → "For developers"
3. Turn on "Developer Mode"
4. Restart your computer
5. Try building again:
   ```powershell
   cd apps/desktop
   pnpm build:win
   ```

### Option 4: Build Portable Version (No Installer)
Build a portable version that doesn't require installation:

```powershell
cd apps/desktop
$env:CSC_IDENTITY_AUTO_DISCOVERY="false"
pnpm exec electron-builder --win portable --config.win.sign=null
```

### Option 5: Use the Unpacked Build
The build actually creates an unpacked version before failing. Check:

```
apps/desktop/dist/win-unpacked/EduPilot.exe
```

You can run this directly without needing the installer.

## Recommended Workflow

For development and testing:
1. Use `pnpm dev` to run the app
2. Test all features
3. Only build the installer when you need to distribute the app

For distribution:
1. Enable Developer Mode or run as Administrator
2. Build the installer: `pnpm build:win`
3. The installer will be in `apps/desktop/dist/`

## Current Status

The Next.js build completed successfully. The app is ready to run in development mode.
