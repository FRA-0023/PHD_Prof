' Avvia_PHD_Prof.vbs
' Silent windowless launcher for PHD Prof Web Cockpit on Windows.
' Launches the local FastAPI backend in the background and opens the default browser.
' When the browser tab is closed, the automatic heartbeat watchdog terminates the background process.

Option Explicit
Dim fso, scriptDir, wshShell, pythonExe, command

Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set wshShell = CreateObject("WScript.Shell")
wshShell.CurrentDirectory = scriptDir

Dim localApp
localApp = wshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
pythonExe = localApp & "\Programs\Python\Python311\python.exe"
If Not fso.FileExists(pythonExe) Then
    pythonExe = "python.exe"
End If

command = """" & pythonExe & """ pdf_to_notion.py --mode web"

' WindowStyle: 0 = Hidden window (zero CMD flashing or terminal blocking)
' bWaitOnReturn: False = Immediate asynchronous execution
wshShell.Run command, 0, False
