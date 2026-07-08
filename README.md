<p align="center">
  <img src="assets/icon.png" alt="FloatLedger" width="96" height="96" />
</p>

<h1 align="center">FloatLedger</h1>

<p align="center">
  <strong>AI API 余额桌面悬浮窗</strong><br />
  半透明毛玻璃小组件，实时查看 DeepSeek 等厂商的 API 余额与当日消耗
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-blue?logo=windows" alt="Platform" />
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/GUI-PyQt6-green?logo=qt" alt="PyQt6" />
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License" />
</p>

---

## ✨ 功能

<table>
  <tr>
    <td width="50%">
      <h3>💰 实时余额</h3>
      <p>DeepSeek API 账户余额一目了然<br />充值余额 + 赠送余额分开展示</p>
    </td>
    <td width="50%">
      <h3>📉 今日消费</h3>
      <p>自动计算当日 API 消费金额<br />跨天自动重置，充值智能识别</p>
    </td>
  </tr>
  <tr>
    <td>
      <h3>🔄 定时刷新</h3>
      <p>1 / 5 / 10 / 30 分钟可调<br />自定义间隔 1–1440 分钟</p>
    </td>
    <td>
      <h3>🎨 双主题 · 7 语言</h3>
      <p>浅色 / 深色自动适配<br />简繁中英日俄法西七语切换</p>
    </td>
  </tr>
  <tr>
    <td>
      <h3>📌 桌面置顶</h3>
      <p>始终悬浮在最前，不占任务栏<br />透明度 30%–100% 可调</p>
    </td>
    <td>
      <h3>🖱️ 系统托盘</h3>
      <p>最小化隐藏到托盘<br />右键菜单快捷操作</p>
    </td>
  </tr>
</table>

---

## 📥 下载

前往 [GitHub Releases](https://github.com/damiaoloia5-ui/FloatLedger/releases) 下载最新安装包。

| 文件 | 说明 |
|------|------|
| `FloatLedger_Setup_x.x.x.exe` | 安装包（推荐）— 自动创建快捷方式 |
| `FloatLedger.exe` | 单文件便携版 — 解压即用 |

---

## 🔒 安全

- **仓库不包含任何 API Key** — 所有 `sk-` 字符串均为占位符
- **安装包不含密钥** — 每个用户首次运行时自行输入
- **本地存储** — API Key 仅保存在 `%APPDATA%\FloatLedger\snapshot.json`
- **编码防护** — 使用 Base64 编码防止明文泄露
- **日志安全** — `__repr__` 自动截断 `sk-xxxx***`

详见 [SECURITY.md](SECURITY.md)

---

## 🚀 从源码运行

```powershell
# 1. 创建虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
python main.py
```

---

## 🔨 构建安装包

**环境要求**
- Windows 10 / 11
- Python 3.11+
- [Inno Setup 6](https://jrsoftware.org/isdl.php)

```batch
build.bat
```

**产物**

| 路径 | 说明 |
|------|------|
| `dist\FloatLedger.exe` | 单文件便携版 (~40 MB) |
| `output\FloatLedger_Setup_x.x.x.exe` | Inno Setup 安装包 |

---

## 📁 项目结构

```
FloatLedger/
├── main.py                 # 程序入口
├── api/
│   └── deepseek_client.py  # DeepSeek API 客户端
├── core/
│   ├── config.py            # 配置与状态管理
│   ├── scheduler.py         # 定时刷新调度
│   └── calculator.py        # 消费差值计算
├── ui/
│   ├── overlay_window.py    # 主弹窗（透明毛玻璃）
│   ├── tray_icon.py         # 系统托盘
│   ├── settings_dialog.py   # 设置对话框
│   ├── styles.py            # 主题感知 QSS
│   ├── themes.py            # 浅色/深色主题定义
│   └── icon_factory.py      # 运行时图标生成
├── utils/
│   ├── crypto_utils.py      # API Key 编解码
│   └── autostart.py         # 开机自启
├── i18n/                    # 多语言翻译
├── assets/                  # 图标资源
└── docs/                    # 文档
```

---

## 📄 协议

MIT License

---

<p align="center">
  <sub>FloatLedger — 让 API 消费随时可见</sub>
</p>
