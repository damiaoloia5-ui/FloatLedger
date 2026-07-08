# FloatLedger

FloatLedger 是一个 Windows 桌面悬浮窗工具，用于实时查看 AI API 账户余额和当日消耗。支持 DeepSeek 等厂商。程序首次启动时由用户自行输入 DeepSeek API Key，仓库和安装包不内置作者或客户的 API Key。

## 下载

当前安装包已放在仓库内：

- [FloatLedger_Setup_1.0.0.exe](releases/FloatLedger_Setup_1.0.0.exe)

正式发布到 GitHub 时，建议同时创建 GitHub Release，并把 `releases/FloatLedger_Setup_1.0.0.exe` 上传为 Release 附件，这样客户可以直接从 Releases 页面下载。

## 功能

- 常驻桌面悬浮窗口显示 DeepSeek API 余额。
- 自动计算当日消耗。
- 支持 1 / 5 / 10 / 30 分钟刷新间隔。
- 支持窗口置顶、透明度、浅色/深色主题。
- 支持系统托盘、开机自启、多语言界面。
- 首次运行自动提示配置 API Key。

## API Key 安全说明

- 仓库内不包含任何真实 DeepSeek API Key。
- 安装包不应包含用户本地配置文件或 API Key。
- 每个客户首次运行时自行输入自己的 API Key。
- API Key 仅保存在客户本机 `%APPDATA%\FloatLedger\snapshot.json`。
- 当前实现使用 Base64 编码保存 API Key，这不是强加密，只是避免明文直接显示；安全性主要依赖 Windows 用户目录权限。
- 不要把 `snapshot.json`、`.env`、日志、截图或任何真实 `sk-...` 密钥提交到 GitHub。

## 从源码运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## 构建安装包

构建环境：

- Windows 10 / 11
- Python 3.11 或更高版本
- Inno Setup 6，用于生成安装包

运行：

```batch
build.bat
```

产物：

- `dist\FloatLedger.exe`：单文件便携版
- `output\FloatLedger_Setup_1.0.0.exe`：安装包

发布前请重新确认 `dist/`、`output/`、`build/` 中没有本地配置文件或密钥。默认 `.gitignore` 会排除这些构建目录，只保留 `releases/` 下用于发布的安装包副本。

## GitHub 发布

详细步骤见 [docs/GITHUB_RELEASE.md](docs/GITHUB_RELEASE.md)。

## 隐私

见 [PRIVACY.md](PRIVACY.md)。
