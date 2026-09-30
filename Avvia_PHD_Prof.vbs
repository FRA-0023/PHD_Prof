' Avvia_PHD_Prof.vbs
' Launcher silenzioso senza finestra terminale CMD per PHD Prof Web Cockpit.
' Avvia il backend locale in background e apre il browser predefinito a zero attrito.
' Quando l'utente chiude la finestra del browser, il watchdog automatico termina il processo in background.

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

' WindowStyle: 0 = Finestra nascosta (zero flash o blocco CMD)
' bWaitOnReturn: False = Esecuzione asincrona immediata
wshShell.Run command, 0, False
