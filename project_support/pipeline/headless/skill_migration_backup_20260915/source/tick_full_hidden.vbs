' tick_full_hidden.vbs <project> - Hidden launcher for tick_full.bat
' Hides console windows (Task Scheduler interactive run would otherwise pop cmd windows)
' Runs the bat directly via WScript.Shell.Run (window style 0 = hidden).
' NOTE: do NOT wrap in "cmd /c ..." - cmd's leading-quote rule mangles the bat path.
' Usage: wscript.exe "D:\project\.claude\skills\songcl_research_pipeline\tick_full_hidden.vbs" cluster_project
Option Explicit
Dim ws, project, bat, q, cmd
If WScript.Arguments.Count = 0 Then
    WScript.Echo "Usage: tick_full_hidden.vbs <project>"
    WScript.Quit 1
End If
project = WScript.Arguments(0)
bat = "D:\project\.claude\skills\songcl_research_pipeline\tick_full.bat"
q = Chr(34) ' double-quote
Set ws = CreateObject("WScript.Shell")
cmd = q & bat & q & " " & q & project & q
ws.Run cmd, 0, False
WScript.Quit 0
