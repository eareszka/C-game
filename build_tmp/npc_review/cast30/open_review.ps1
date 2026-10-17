$ErrorActionPreference='Stop'
$npcCorrectedWindow=Get-Process -Name Aseprite | Where-Object { $_.MainWindowTitle -like '*cast30_corrected_preview3x*' -and $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if(-not $npcCorrectedWindow){throw 'Corrected review is not selected'}
Add-Type -AssemblyName Microsoft.VisualBasic
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[Microsoft.VisualBasic.Interaction]::AppActivate($npcCorrectedWindow.Id)
[System.Windows.Forms.SendKeys]::SendWait('^0{ENTER}')
Start-Sleep -Milliseconds 300
$npcCorrectedScreen=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$npcCorrectedCapture=New-Object System.Drawing.Bitmap($npcCorrectedScreen.Width,$npcCorrectedScreen.Height)
$npcCorrectedGraphics=[System.Drawing.Graphics]::FromImage($npcCorrectedCapture)
$npcCorrectedGraphics.CopyFromScreen($npcCorrectedScreen.Location,[System.Drawing.Point]::Empty,$npcCorrectedScreen.Size)
$npcCorrectedCapture.Save('C:/Users/emery/OneDrive/Desktop/projects/C-game/build_tmp/npc_review/cast30_corrected/aseprite_corrected_fitted.png')
$npcCorrectedGraphics.Dispose()
$npcCorrectedCapture.Dispose()
$npcCorrectedWindow | Select-Object Id,MainWindowTitle
