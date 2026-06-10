; Instalador do CUTED Beta (Inno Setup 6+).
; Compilar: iscc packaging\installer.iss /DAppDir="<dist>\CUTED" /DAppVersion="2026.06.10"
;
; Decisoes:
; - Instalacao per-user (sem admin), em {localappdata}\Programs\CUTED.
; - Desinstalacao NUNCA apaga dados do usuario: Documents\CUTED Workspace,
;   Videos\CUTED Renders e %USERPROFILE%\.cuted ficam intactos.
; - Sem assinatura no beta: o guia de instalacao documenta o aviso SmartScreen.

#ifndef AppDir
  ; Saida padrao do build.ps1 (fora do OneDrive); sobrescrever com /DAppDir=...
  #define AppDir GetEnv("LOCALAPPDATA") + "\cuted-build\dist\CUTED"
#endif
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{8C1B7C52-5A57-4A6B-9B5B-2E61F1C0D3A4}
AppName=CUTED
AppVersion={#AppVersion}
AppPublisher=CUTED
DefaultDirName={localappdata}\Programs\CUTED
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=CUTED-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=CUTED
CloseApplications=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Area de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "{#AppDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\CUTED"; Filename: "{app}\cuted.exe"
Name: "{userdesktop}\CUTED"; Filename: "{app}\cuted.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\cuted.exe"; Description: "Abrir o CUTED agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Apenas arquivos do app. Workspace, renders e ~/.cuted sao preservados.
Type: filesandordirs; Name: "{app}"
