# How to Fix Windows Permission Problem for Desktop App

## The Problem
You're seeing this error when trying to install or build the desktop app:
```
ERROR: Cannot create symbolic link : A required privilege is not held by the client.
```

This happens because Windows requires special permissions to create symbolic links, which electron-builder needs during installation.

## Quick Fix (Recommended) - Enable Developer Mode

This is the **easiest and best solution** for development:

### Step-by-Step Instructions:

1. **Open Windows Settings**
   - Press `Win + I` on your keyboard
   - Or click Start → Settings

2. **Navigate to Developer Settings**
   - Click on **"Privacy & Security"** (left sidebar)
   - Click on **"For developers"** (in the main panel)

3. **Enable Developer Mode**
   - Find the **"Developer Mode"** toggle
   - Switch it to **ON**
   - Windows will show a warning - click **"Yes"** to confirm
   - Windows may download and install additional components (takes 1-2 minutes)

4. **Restart Your Terminal**
   - Close your current PowerShell window completely
   - Open a new PowerShell window

5. **Clean and Reinstall**
   ```powershell
   cd "C:\Creative work\apps\desktop"
   Remove-Item -Recurse -Force node_modules
   pnpm install
   ```

6. **Run the App**
   ```powershell
   pnpm dev
   ```

### Why This Works
Developer Mode grants your user account permission to create symbolic links without needing administrator privileges every time. This is safe for development machines and is the recommended approach by Microsoft for developers.

---

## Alternative Solution - Run as Administrator

If you can't enable Developer Mode (e.g., company policy), use this method:

### Step-by-Step Instructions:

1. **Close Your Current PowerShell**
   - Close any open PowerShell or terminal windows

2. **Open PowerShell as Administrator**
   - Click the Start button
   - Type "PowerShell"
   - Right-click on "Windows PowerShell"
   - Select **"Run as administrator"**
   - Click **"Yes"** on the User Account Control prompt

3. **Navigate to the Project**
   ```powershell
   cd "C:\Creative work\apps\desktop"
   ```

4. **Clean and Reinstall**
   ```powershell
   Remove-Item -Recurse -Force node_modules
   pnpm install
   ```

5. **Run the App**
   ```powershell
   pnpm dev
   ```

### Downside
You'll need to run PowerShell as administrator every time you want to install packages or build the app.

---

## Just Want to Run the App? (Skip Building)

If you just want to use the desktop app without building an installer:

```powershell
cd "C:\Creative work\apps\desktop"
pnpm dev
```

This runs the app in development mode without needing to build an installer, so it doesn't require special permissions.

---

## Verification

After applying either solution, you should see:

```
✓ Ready in 2.5s
○ Local:    http://localhost:3004
✓ Electron window opened successfully
```

And an Electron window should open with the EduPilot app.

---

## Troubleshooting

### "Developer Mode" option is grayed out
- Make sure you're logged in as an administrator
- Check if your organization has disabled Developer Mode via Group Policy
- Use the "Run as Administrator" solution instead

### Still getting permission errors after enabling Developer Mode
1. Make sure you restarted your terminal after enabling Developer Mode
2. Try restarting your computer
3. Clear the electron-builder cache:
   ```powershell
   Remove-Item -Recurse -Force "$env:LOCALAPPDATA\electron-builder\Cache"
   ```

### Electron window doesn't open
1. Check if the Electron binary was installed:
   ```powershell
   Test-Path "node_modules\electron\dist\electron.exe"
   ```
2. If it returns `False`, the installation failed - try the "Run as Administrator" solution

### Port 3004 is already in use
Another process is using port 3004. Kill it or change the port:
```powershell
# Find what's using the port
netstat -ano | findstr :3004

# Kill the process (replace PID with the number from above)
taskkill /PID <PID> /F
```

---

## What I Recommend

**For your situation, enable Developer Mode (first solution).** It's:
- ✅ One-time setup
- ✅ No need to run as admin every time  
- ✅ Works for all development tools
- ✅ The standard approach for Windows developers
- ✅ Easiest to maintain long-term

After enabling Developer Mode, you'll be able to install and run the desktop app without any permission issues.
