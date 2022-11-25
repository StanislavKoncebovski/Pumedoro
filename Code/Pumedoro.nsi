; The name of the installer - might be changed later
Name "Pumedoro"

; The file to write
OutFile "Pumedoro.exe"

; The default installation directory
InstallDir "$DESKTOP\Pumedoro"

; Request application privileges for Windows Vista
RequestExecutionLevel user

; Pages
Page Directory
Page Instfiles
;--------------------------------
; The stuff to install
Section "Files" 
  ; Set output path to the installation directory.
  ; CreateDirectory "$INSTDIR"
  SetOutPath "$INSTDIR"
  
  ; Put files there
  File ".\Training_Data.csv"
  File ".\Pumedoro.db3"
  File ".\pumedoro_*.py"
  
SectionEnd ; end the section
