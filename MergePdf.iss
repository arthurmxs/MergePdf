; Instalador Windows gerado com Inno Setup.
#define MyAppName "MergePdf"
#define MyAppPublisher "arthurmxs"
#define MyAppURL "https://github.com/arthurmxs/MergePdf"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

[Setup]
AppId={{D08C7D75-80E5-42B8-8A75-35E10D6EAB84}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist\installer
OutputBaseFilename=MergePdf-Setup
SetupIconFile=assets\app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Files]
Source: "dist\MergePdf.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\MergePdf.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\MergePdf.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Run]
Filename: "{app}\MergePdf.exe"; Description: "Abrir o MergePdf"; Flags: nowait postinstall skipifsilent
