Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Run from the folder where this file lives
appDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = appDir

' Install / update dependencies silently (hidden window, wait until done)
shell.Run "cmd /c pip install -r requirements.txt --quiet", 0, True

' Launch the app with pythonw.exe — no console window
shell.Run "pythonw main.py", 0, False
