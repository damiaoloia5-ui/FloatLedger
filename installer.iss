; ==========================================================================
; FloatLedger — Inno Setup 安装脚本
; 版本: 1.0.0
;
; 使用方法:
;   1. 先运行 build.bat 生成 dist\FloatLedger.exe
;   2. 用 Inno Setup Compiler 编译此文件
;   3. 产出安装包: output\FloatLedger_Setup_1.0.0.exe
;
; 安全说明:
;   API Key 存储在 %APPDATA%\FloatLedger\snapshot.json，
;   运行时动态创建，永远不会被打包进安装程序。
; ==========================================================================

#define MyAppName        "FloatLedger"
#define MyAppNameZh     "DeepSeek 余额监控"
#define MyAppVersion    "1.0.0"
#define MyAppPublisher  "FloatLedger"
#define MyAppExeName    "FloatLedger.exe"
#define MyAppURL        "https://api.deepseek.com"

[Setup]
; ── 基本信息 ──
AppId={{A7B3C9D2-E4F5-6A8B-9C0D-1E2F3A4B5C6D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}

; ── 安装目录 ──
; 优先安装到 D 盘，D 盘不存在则回退到系统默认 Program Files
DefaultDirName={code:GetDefaultInstallDir}\{#MyAppName}
DefaultGroupName={#MyAppNameZh}

; ── 输出设置 ──
OutputDir=output
OutputBaseFilename=FloatLedger_Setup_{#MyAppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes

; ── 权限与架构 ──
; 使用 lowest 权限：写入 HKCU 注册表 + 安装到用户目录不需要管理员
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; ── 卸载 ──
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

; ── 界面 ──
WizardStyle=modern

; ── 杂项 ──
DisableProgramGroupPage=yes
CloseApplications=force

; ── 版本信息（右键 exe → 属性 → 详细信息） ──
VersionInfoVersion={#MyAppVersion}
VersionInfoProductName={#MyAppNameZh}

; ---------------------------------------------------------------------------
; 多语言支持（7 种安装界面语言）
; ---------------------------------------------------------------------------
[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "chinesetraditional"; MessagesFile: "installer_languages\ChineseTraditional.isl"
Name: "english";           MessagesFile: "compiler:Default.isl"
Name: "japanese";          MessagesFile: "compiler:Languages\Japanese.isl"
Name: "russian";           MessagesFile: "compiler:Languages\Russian.isl"
Name: "french";            MessagesFile: "compiler:Languages\French.isl"
Name: "spanish";           MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
; ── 简体中文 ──
chinesesimplified.LaunchApp=运行 {#MyAppNameZh}
chinesesimplified.LaunchAppDesc=立即启动 DeepSeek 余额监控
chinesesimplified.CreateDesktopIcon=创建桌面快捷方式(&D)
chinesesimplified.CreateDesktopIconDesc=在桌面创建快捷方式，方便快速启动
chinesesimplified.AutoStart=开机自动启动(&S)
chinesesimplified.AutoStartDesc=Windows 启动时自动运行 DeepSeek 余额监控
chinesesimplified.InstallComplete=安装完成
chinesesimplified.InstallCompleteDesc={#MyAppNameZh} 已成功安装到您的计算机。
chinesesimplified.UninstallDataPrompt=检测到用户配置数据目录：%n%n%1%n%n是否同时删除配置数据（包含 API Key 和余额历史记录）？

; ── 繁體中文 ──
chinesetraditional.LaunchApp=執行 {#MyAppNameZh}
chinesetraditional.LaunchAppDesc=立即啟動 DeepSeek 餘額監控
chinesetraditional.CreateDesktopIcon=建立桌面捷徑(&D)
chinesetraditional.CreateDesktopIconDesc=在桌面建立捷徑，方便快速啟動
chinesetraditional.AutoStart=開機自動啟動(&S)
chinesetraditional.AutoStartDesc=Windows 啟動時自動執行 DeepSeek 餘額監控
chinesetraditional.InstallComplete=安裝完成
chinesetraditional.InstallCompleteDesc={#MyAppNameZh} 已成功安裝到您的電腦。
chinesetraditional.UninstallDataPrompt=偵測到使用者設定資料目錄：%n%n%1%n%n是否同時刪除設定資料（包含 API Key 和餘額歷史記錄）？

; ── English ──
english.LaunchApp=Launch {#MyAppName}
english.LaunchAppDesc=Start FloatLedger now
english.CreateDesktopIcon=Create &desktop shortcut
english.CreateDesktopIconDesc=Place a shortcut on the desktop for quick access
english.AutoStart=Launch at &startup
english.AutoStartDesc=Automatically start FloatLedger when Windows starts
english.InstallComplete=Installation Complete
english.InstallCompleteDesc={#MyAppName} has been successfully installed.
english.UninstallDataPrompt=User configuration data found at:%n%n%1%n%nDo you also want to delete the configuration data (including API Key and balance history)?

; ── 日本語 ──
japanese.LaunchApp={#MyAppName} を起動
japanese.LaunchAppDesc=DeepSeek 残高モニターを今すぐ起動
japanese.CreateDesktopIcon=デスクトップにショートカットを作成(&D)
japanese.CreateDesktopIconDesc=デスクトップにショートカットを配置して素早く起動
japanese.AutoStart=Windows 起動時に自動実行(&S)
japanese.AutoStartDesc=Windows の起動時に DeepSeek 残高モニターを自動的に実行
japanese.InstallComplete=インストール完了
japanese.InstallCompleteDesc={#MyAppName} は正常にインストールされました。
japanese.UninstallDataPrompt=ユーザー設定データディレクトリが見つかりました：%n%n%1%n%n設定データ（API Key と残高履歴を含む）も削除しますか？

; ── Русский ──
russian.LaunchApp=Запустить {#MyAppName}
russian.LaunchAppDesc=Запустить Монитор баланса DeepSeek сейчас
russian.CreateDesktopIcon=Создать ярлык на &рабочем столе
russian.CreateDesktopIconDesc=Разместить ярлык на рабочем столе для быстрого доступа
russian.AutoStart=Запускать при &загрузке Windows
russian.AutoStartDesc=Автоматически запускать Монитор баланса DeepSeek при загрузке Windows
russian.InstallComplete=Установка завершена
russian.InstallCompleteDesc={#MyAppName} успешно установлен.
russian.UninstallDataPrompt=Обнаружен каталог пользовательских данных:%n%n%1%n%nУдалить также данные конфигурации (включая API Key и историю баланса)?

; ── Français ──
french.LaunchApp=Lancer {#MyAppName}
french.LaunchAppDesc=Démarrer le Moniteur de solde DeepSeek maintenant
french.CreateDesktopIcon=Créer un raccourci sur le &bureau
french.CreateDesktopIconDesc=Placer un raccourci sur le bureau pour un accès rapide
french.AutoStart=Lancer au &démarrage
french.AutoStartDesc=Démarrer automatiquement le Moniteur de solde DeepSeek au lancement de Windows
french.InstallComplete=Installation terminée
french.InstallCompleteDesc={#MyAppName} a été installé avec succès.
french.UninstallDataPrompt=Répertoire de données utilisateur détecté :%n%n%1%n%nVoulez-vous également supprimer les données de configuration (y compris la clé API et l'historique du solde) ?

; ── Español ──
spanish.LaunchApp=Ejecutar {#MyAppName}
spanish.LaunchAppDesc=Iniciar el Monitor de saldo DeepSeek ahora
spanish.CreateDesktopIcon=Crear acceso directo en el &escritorio
spanish.CreateDesktopIconDesc=Colocar un acceso directo en el escritorio para acceso rápido
spanish.AutoStart=Iniciar con &Windows
spanish.AutoStartDesc=Iniciar automáticamente el Monitor de saldo DeepSeek al arrancar Windows
spanish.InstallComplete=Instalación completa
spanish.InstallCompleteDesc={#MyAppName} se ha instalado correctamente.
spanish.UninstallDataPrompt=Se detectó el directorio de datos de usuario:%n%n%1%n%n¿Desea eliminar también los datos de configuración (incluyendo la clave API y el historial de saldo)?

; ---------------------------------------------------------------------------
; 安装文件
; ---------------------------------------------------------------------------
[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; ---------------------------------------------------------------------------
; 图标
; ---------------------------------------------------------------------------
[Icons]
; 开始菜单
Name: "{group}\{#MyAppNameZh}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppNameZh}}"; Filename: "{uninstallexe}"

; 桌面快捷方式（由 [Tasks] 条件控制）
Name: "{autodesktop}\{#MyAppNameZh}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; ---------------------------------------------------------------------------
; 可选任务
; ---------------------------------------------------------------------------
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:CreateDesktopIconDesc}"; Flags: unchecked
Name: "autostart";   Description: "{cm:AutoStart}";           GroupDescription: "{cm:AutoStartDesc}";           Flags: unchecked

; ---------------------------------------------------------------------------
; 注册表
; ---------------------------------------------------------------------------
[Registry]
; 开机自启（由 [Tasks] 条件控制）
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "FloatLedger"; \
    ValueData: """{app}\{#MyAppExeName}"""; \
    Flags: uninsdeletevalue; Tasks: autostart

; ---------------------------------------------------------------------------
; 运行
; ---------------------------------------------------------------------------
[Run]
; 安装完成后启动程序（用户可取消勾选）
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchApp}"; \
    Flags: nowait postinstall skipifsilent

; ---------------------------------------------------------------------------
; 卸载
; ---------------------------------------------------------------------------
[UninstallRun]
; 卸载前先尝试关闭运行中的程序
Filename: "taskkill"; Parameters: "/f /im {#MyAppExeName}"; \
    Flags: runhidden; RunOnceId: "KillApp"

[Code]
// ── 默认安装路径：D 盘优先 ──
// D 盘存在时默认安装到 D:\FloatLedger
// 否则回退到用户目录（最低权限，无需管理员）
function GetDefaultInstallDir(Default: string): string;
var
  DriveD: string;
begin
  DriveD := 'D:\';
  if DirExists(DriveD) then
    Result := 'D:\'
  else
    Result := ExpandConstant('{localappdata}\Programs\');
end;

// ── 卸载时询问是否删除用户数据（多语言） ──
function InitializeUninstall(): Boolean;
var
  DataPath: string;
  DeleteData: Integer;
begin
  Result := True;

  // 检查用户数据目录是否存在
  DataPath := ExpandConstant('{userappdata}') + '\FloatLedger';
  if DirExists(DataPath) then
  begin
    DeleteData := MsgBox(
      FmtMessage(CustomMessage('UninstallDataPrompt'), [DataPath]),
      mbConfirmation,
      MB_YESNO or MB_DEFBUTTON2
    );
    if DeleteData = IDYES then
    begin
      DelTree(DataPath, True, True, True);
    end;
  end;
end;
