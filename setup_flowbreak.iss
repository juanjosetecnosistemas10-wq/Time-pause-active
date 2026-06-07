; Inno Setup script for FlowBreak
; To compile: Run this file with Inno Setup Compiler (innosetup.com)

[Setup]
AppName=FlowBreak
AppVersion=2.0.0
AppPublisher=FlowBreak
AppPublisherURL=https://github.com/tu_usuario/Time-pause-active
AppSupportURL=https://github.com/tu_usuario/Time-pause-active
DefaultDirName={autopf}\FlowBreak
DefaultGroupName=FlowBreak
UninstallDisplayIcon={app}\FlowBreak.exe
UninstallDisplayName=FlowBreak
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=FlowBreak_Setup
SetupIconFile=FlowBreak.ico
WizardStyle=modern
PrivilegesRequired=admin
DisableProgramGroupPage=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
spanish.WelcomeLabel1=Bienvenido a la instalaci\u00f3n de FlowBreak
spanish.WelcomeLabel2=FlowBreak te ayuda a tomar pausas activas durante tu jornada laboral.\n\nSe recomienda cerrar otras aplicaciones antes de continuar.
spanish.FinishedLabel1=La instalaci\u00f3n se ha completado
spanish.FinishedLabel2=FlowBreak se iniciar\u00e1 autom\u00e1ticamente al cerrar este asistente.
english.WelcomeLabel1=Welcome to FlowBreak Setup
english.WelcomeLabel2=FlowBreak helps you take active breaks during your workday.\n\nIt is recommended to close other applications before continuing.
english.FinishedLabel1=Setup completed
english.FinishedLabel2=FlowBreak will start automatically when you close this wizard.

[Files]
Source: "dist\FlowBreak.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "FlowBreak.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "FlowBreak_256.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\FlowBreak"; Filename: "{app}\FlowBreak.exe"; IconFilename: "{app}\FlowBreak.ico"
Name: "{group}\Desinstalar FlowBreak"; Filename: "{uninstallexe}"; IconFilename: "{app}\FlowBreak.ico"
Name: "{commondesktop}\FlowBreak"; Filename: "{app}\FlowBreak.exe"; IconFilename: "{app}\FlowBreak.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"
Name: "autostart"; Description: "Iniciar FlowBreak con Windows"; GroupDescription: "Autoarranque:"

[Run]
Filename: "{app}\FlowBreak.exe"; Description: "Ejecutar FlowBreak"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\FlowBreak.exe"; Parameters: "--uninstall"; Flags: runhidden waituntilterminated

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  RunKey: string;
  Path: string;
begin
  if CurStep = ssPostInstall then
  begin
    if IsTaskSelected('autostart') then
    begin
      RunKey := 'Software\Microsoft\Windows\CurrentVersion\Run';
      Path := ExpandConstant('{app}\FlowBreak.exe');
      if not RegWriteStringValue(HKEY_CURRENT_USER, RunKey, 'FlowBreak', Path) then
        MsgBox('No se pudo configurar el autoarranque.', mbError, MB_OK);
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  RunKey: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    RunKey := 'Software\Microsoft\Windows\CurrentVersion\Run';
    RegDeleteValue(HKEY_CURRENT_USER, RunKey, 'FlowBreak');
  end;
end;
