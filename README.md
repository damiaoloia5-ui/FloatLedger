# DeepSeek 余额监控

一款 Windows 桌面工具，在桌面上显示常驻的半透明弹窗，实时展示 DeepSeek API 账户余额和当日消费。

## 功能

- 💰 **后台余额** — 实时显示 DeepSeek 账户总余额（CNY）
- 📉 **今日消费** — 自动计算当日 API 消费金额
- 🔄 **自动刷新** — 可配置 1/5/10/30 分钟自动刷新
- 📌 **桌面置顶** — 毛玻璃半透明卡片，始终悬浮在最前
- 🖱️ **系统托盘** — 最小化到托盘，不占任务栏空间
- 🌙 **深色模式** — 支持浅色/深色主题切换
- 🚀 **开机自启** — 可选开机自动运行

## 使用

1. 首次启动会提示输入 DeepSeek API Key（以 `sk-` 开头）
2. API Key 可在 [DeepSeek 开放平台](https://platform.deepseek.com/api_keys) 获取
3. 输入后自动查询余额并显示在桌面弹窗中
4. 点击 ⚙ 可打开设置面板

## 快捷操作

| 操作 | 行为 |
|------|------|
| 拖拽标题栏 | 移动窗口 |
| 点击 🔄 | 立即刷新 |
| 点击 ⚙ | 打开设置 |
| 点击 ✕ | 最小化到托盘 |
| 双击托盘图标 | 显示/隐藏窗口 |
| 右键托盘图标 | 弹出菜单 |

## 数据存储

配置文件位于：`%APPDATA%\DeepSeekMonitor\snapshot.json`

API Key 以 Base64 编码存储，非明文保存。

## 系统要求

- Windows 10 / 11（64 位）
- 无需安装 Python，独立运行

## 从源码构建

```batch
# 安装依赖并打包
build.bat

# 产出：
#   dist\DeepSeekMonitor.exe    （便携版）
#   output\DeepSeekMonitor_Setup_*.exe  （安装包，需安装 Inno Setup 6）
```

## 卸载

- **安装包版本**：通过「设置 → 应用」或开始菜单中的卸载程序卸载
- **便携版本**：直接删除 .exe 文件即可；如需清除配置，删除 `%APPDATA%\DeepSeekMonitor` 目录
