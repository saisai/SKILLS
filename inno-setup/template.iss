; {__APP_NAME__} - production Windows installer (Inno Setup 6)
; Built after staging files into dist\{__DIST_FOLDER__}
; Compile: ISCC.exe {__APP_SLUG__}-setup.iss /DMyAppVersion=<version>

#ifndef MyAppVersion
#define MyAppVersion "{__DEFAULT_VERSION__}"
#endif
#define MyAppName "{__APP_NAME__}"
#define MyAppPublisher "{__APP_PUBLISHER__}"
#define MyAppURL "{__APP_URL__}"
#define MyAppExeName "{__APP_EXE__}"
#define RootDir "..\.."
#define DistDir "..\..\dist"
#define InstallerScripts "scripts"

[Setup]
AppId={{{__APP_ID__}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
PrivilegesRequired=admin
AllowNetworkDrive=no
AlwaysShowDirOnReadyPage=yes
OutputDir={#DistDir}
OutputBaseFilename={__PRODUCT_TOKEN__}-Setup-x64-{#MyAppVersion}
; OPTIONAL icon — keep only when the repo has this .ico
#if FileExists("{__ICON_RELATIVE_TO_ISS__}")
SetupIconFile="{#RootDir}\{__ICON_FROM_ROOT__}"
#endif
SolidCompression=yes
Compression=lzma2/max
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
CloseApplications=yes
CloseApplicationsFilter=*.exe
UsePreviousAppDir=yes
DisableProgramGroupPage=yes
DisableDirPage=no
UninstallDisplayIcon={app}\bin\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
SetupLogging=yes
RestartIfNeededByRun=no
ChangesEnvironment=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
FinishedLabel=Setup has finished installing [name] on your computer.{__FINISHED_HINT__}
SelectDirDesc=Where should [name] be installed?
SelectDirLabel3=Setup will install [name] into the following folder. You can keep the default on this drive, or Browse and choose a folder on any local disk (C:, D:, E:, …).
WizardSelectDir=Select Destination Location

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
; OPTIONAL path task — keep when the user should get {app}\bin on PATH
Name: "addtopath"; Description: "Add the application bin folder to PATH (requires a new shell)"; GroupDescription: "Other:"
; OPTIONAL seed task — keep only when install.ps1 accepts -Seed
; Name: "seeddata"; Description: "{__SEED_DESCRIPTION__}"; GroupDescription: "Database:"; Flags: checkedonce; Check: ShouldOfferSeed

[Dirs]
Name: "{app}\logs"
Name: "{app}\config"
; Add one Name per directory the app must have on first install (data, storage, service logs).

[Files]
; OPTIONAL preinstall — keep when scripts\preinstall.ps1 and scripts\common.ps1 exist
Source: "{#InstallerScripts}\preinstall.ps1"; Flags: dontcopy
Source: "{#InstallerScripts}\common.ps1"; Flags: dontcopy
Source: "{#InstallerScripts}\*"; DestDir: "{app}\installer"; Flags: ignoreversion
; OPTIONAL config overlay
Source: "config\*"; DestDir: "{app}\installer\config"; Flags: ignoreversion
; OPTIONAL SQL migrations — point at the repo's *.up.sql (or equivalent) folder
; Source: "{#RootDir}\{__MIGRATIONS_GLOB__}"; DestDir: "{app}\installer\migrations"; Flags: ignoreversion
Source: "{#DistDir}\{__DIST_FOLDER__}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\bin\{#MyAppExeName}"
; OPTIONAL browser shortcut — keep when the app has a local URL
Name: "{group}\Open in browser"; Filename: "{__APP_URL__}"
; OPTIONAL health check — keep when scripts\health-check.cmd exists
Name: "{group}\Health check"; Filename: "{app}\installer\health-check.cmd"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\bin\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\bin\{#MyAppExeName}"; Description: "Open {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Keep a line only when that cmd exists. Uninstall services before deleting data.
Filename: "{app}\installer\uninstall.cmd"; RunOnceId: "UninstallServices"; Flags: waituntilterminated; WorkingDir: "{app}"
Filename: "{app}\installer\remove-data.cmd"; RunOnceId: "RemoveData"; Flags: waituntilterminated; WorkingDir: "{app}"

[UninstallDelete]
; One entry per data or log directory this product creates. Always end with {app}.
Type: filesandordirs; Name: "{app}\config"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{commonappdata}\{__APP_NAME__}"
Type: filesandordirs; Name: "{app}"

; OPTIONAL PATH registry — keep together with the addtopath task and the [Code] PATH functions
[Registry]
#define EnvironmentRootKey "HKLM64"
#define EnvironmentKey "System\CurrentControlSet\Control\Session Manager\Environment"

Root: {#EnvironmentRootKey}; Subkey: "{#EnvironmentKey}"; ValueType: expandsz; ValueName: "Path"; ValueData: "{code:AddToPath|{app}\bin}"; Tasks: addtopath; Check: NeedsAddToPath(ExpandConstant('{app}\bin'))

[Code]
var
  UpgradeMode: Boolean;

function GetUninstallString: string;
var
  UninstallKey: string;
  UninstallString: string;
begin
  Result := '';
  UninstallKey := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1';
  if RegQueryStringValue(HKLM, UninstallKey, 'UninstallString', UninstallString) then begin
    Result := UninstallString;
    exit;
  end;
  if RegQueryStringValue(HKLM64, UninstallKey, 'UninstallString', UninstallString) then begin
    Result := UninstallString;
    exit;
  end;
  if RegQueryStringValue(HKCU, UninstallKey, 'UninstallString', UninstallString) then begin
    Result := UninstallString;
    exit;
  end;
  if RegQueryStringValue(HKCU64, UninstallKey, 'UninstallString', UninstallString) then
    Result := UninstallString;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  UpgradeMode := GetUninstallString() <> '';
end;

function NeedsAddToPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue({#EnvironmentRootKey}, '{#EnvironmentKey}', 'Path', OrigPath) then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;

function IsUpgrade: Boolean;
begin
  Result := UpgradeMode;
end;

; OPTIONAL — only with the seeddata task
function ShouldOfferSeed: Boolean;
begin
  Result := not FileExists(ExpandConstant('{app}\config\install-state.json'));
end;

function PowershellExe: string;
begin
  Result := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  if not FileExists(Result) then
    Result := 'powershell.exe';
end;

; OPTIONAL — only when preinstall.ps1 exists. Exit code 2: required port is taken.
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
  Args: string;
begin
  Result := '';
  NeedsRestart := False;

  WizardForm.StatusLabel.Caption := 'Stopping {#MyAppName} services...';
  ExtractTemporaryFile('common.ps1');
  ExtractTemporaryFile('preinstall.ps1');
  Args := '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{tmp}\preinstall.ps1') + '"';
  if not Exec(PowershellExe(), Args, ExpandConstant('{tmp}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) then begin
    Result := 'Failed to launch preinstall cleanup.';
    exit;
  end;
  if ResultCode = 2 then begin
    Result := '{__PORT_IN_USE_MESSAGE__}';
    exit;
  end;
  if ResultCode <> 0 then begin
    Result := 'Preinstall cleanup failed (exit code ' + IntToStr(ResultCode) + ').';
    exit;
  end;
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo, MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
begin
  Result := MemoDirInfo + NewLine + NewLine + MemoTasksInfo;
  if IsUpgrade() then
    Result := Result + NewLine + NewLine +
      'Existing installation detected. Data and configuration will be preserved. Application files will be updated.';
end;

; OPTIONAL — only when scripts\install.ps1 exists
function ExecInstall: Integer;
var
  Args: string;
  ResultCode: Integer;
begin
  Args := '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\installer\install.ps1') +
    '" -Root "' + ExpandConstant('{app}') + '" -Version "{#MyAppVersion}"';
  { OPTIONAL seed flag
  if WizardIsTaskSelected('seeddata') then
    Args := Args + ' -Seed';
  }
  WizardForm.StatusLabel.Caption := 'Installing Windows services and verifying health...';
  WizardForm.StatusLabel.Refresh;
  if not Exec(PowershellExe(), Args, ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := -1
  else
    Result := ResultCode;
end;

function ExtractInstallError(const LogPath: string): string;
var
  Lines: TArrayOfString;
  i, p: Integer;
  Line, Msg: string;
begin
  Result := '';
  if not FileExists(LogPath) then
    exit;
  if not LoadStringsFromFile(LogPath, Lines) then
    exit;
  for i := GetArrayLength(Lines) - 1 downto 0 do begin
    Line := Lines[i];
    p := Pos('[ERROR]', Line);
    if p = 0 then
      continue;
    Msg := Copy(Line, p + 8, Length(Line));
    while (Length(Msg) > 0) and (Msg[1] = ' ') do
      Msg := Copy(Msg, 2, Length(Msg));
    if (Length(Msg) >= 3) and (Copy(Msg, 1, 3) = 'at ') then
      continue;
    Result := Msg;
    exit;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Code: Integer;
  LogPath: string;
  Detail: string;
begin
  if CurStep <> ssPostInstall then
    exit;
  Code := ExecInstall();
  if Code <> 0 then begin
    LogPath := ExpandConstant('{app}\logs\install.log');
    Detail := ExtractInstallError(LogPath);
    if Detail <> '' then
      Detail := 'Details:' + #13#10 + Detail + #13#10#13#10;
    MsgBox('{#MyAppName} could not be started (exit code ' + IntToStr(Code) + ').' + #13#10#13#10 +
      'Files were copied, but the application may not be reachable yet.' + #13#10#13#10 +
      Detail +
      'Open this log for the full trace:' + #13#10 + LogPath + #13#10#13#10 +
      'Fix the issue, then run:' + #13#10 +
      ExpandConstant('{app}\installer\install.cmd'),
      mbError, MB_OK);
  end;
end;

procedure Explode(var Dest: TArrayOfString; Text: String; Separator: String);
var
  i, p: Integer;
begin
  i := 0;
  repeat
    SetArrayLength(Dest, i+1);
    p := Pos(Separator, Text);
    if p > 0 then begin
      Dest[i] := Copy(Text, 1, p-1);
      Text := Copy(Text, p + Length(Separator), Length(Text));
      i := i + 1;
    end else begin
      Dest[i] := Text;
      Text := '';
    end;
  until Length(Text) = 0;
end;

function AddToPath(Param: string): string;
var
  OrigPath: string;
begin
  RegQueryStringValue({#EnvironmentRootKey}, '{#EnvironmentKey}', 'Path', OrigPath);
  if (Length(OrigPath) > 0) and (OrigPath[Length(OrigPath)] = ';') then
    Result := OrigPath + Param
  else
    Result := OrigPath + ';' + Param;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Path: string;
  ThisAppPath: string;
  Parts: TArrayOfString;
  NewPath: string;
  i: Integer;
begin
  if CurUninstallStep = usPostUninstall then begin
    DelTree(ExpandConstant('{commonappdata}\{__APP_NAME__}'), True, True, True);
    DelTree(ExpandConstant('{app}'), True, True, True);
    exit;
  end;
  if CurUninstallStep <> usUninstall then
    exit;
  if not RegQueryStringValue({#EnvironmentRootKey}, '{#EnvironmentKey}', 'Path', Path) then
    exit;
  NewPath := '';
  ThisAppPath := ExpandConstant('{app}\bin');
  Explode(Parts, Path, ';');
  for i := 0 to GetArrayLength(Parts) - 1 do begin
    if CompareText(Parts[i], ThisAppPath) <> 0 then begin
      if NewPath <> '' then
        NewPath := NewPath + ';';
      NewPath := NewPath + Parts[i];
    end;
  end;
  RegWriteExpandStringValue({#EnvironmentRootKey}, '{#EnvironmentKey}', 'Path', NewPath);
end;
