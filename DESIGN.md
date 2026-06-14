# DeepSeek API 消费监控桌面弹窗 — 设计方案

> 版本：v1.0 | 日期：2026-06-14 | 状态：待开发

---

## 一、项目概述

在 Windows 11 桌面上显示一个常驻的半透明弹窗，实时展示 DeepSeek API 的后台余额和当日总消费额度，风格类似 macOS 小组件（毛玻璃、圆角、小巧）。

### 核心功能（精简版）

| 功能 | 说明 |
|------|------|
| 💰 后台余额 | 显示 DeepSeek 账户当前总余额（CNY） |
| 📉 今日消费 | 自当日 00:00 起累计的 API 消费金额 |
| 🔄 自动刷新 | 每隔 N 分钟自动拉取最新余额 |
| 📌 桌面置顶 | 窗口始终悬浮在最前（可配置） |
| 🖱️ 系统托盘 | 最小化到托盘，不占任务栏空间 |

> **已移除：** Token 消耗统计 — DeepSeek 余额 API 不提供 token 用量数据，无法准确获取，故不在 v1.0 范围。

---

## 二、技术选型

### 最终选择：Python 3.11+ + PyQt6

| 维度 | 评估 |
|------|------|
| **透明窗口** | Qt 原生支持 `WA_TranslucentBackground` + `FramelessWindowHint` |
| **置顶** | `WindowStaysOnTopHint` 开箱即用 |
| **系统托盘** | `QSystemTrayIcon` 原生支持 |
| **打包体积** | PyInstaller 打包后约 35-45 MB |
| **开发效率** | Python 生态成熟，`requests` + `PyQt6` 即可 |
| **Win11 适配** | Qt6 对 Win11 圆角/亚克力效果支持良好 |

### 备选方案（不推荐）

| 方案 | 不推荐原因 |
|------|-----------|
| Electron | 体积 150MB+，杀鸡用牛刀 |
| Tauri | 需 Rust 环境，开发周期长 |
| WPF (.NET) | 透明窗口实现复杂，需要额外 Win32 API |
| tkinter | 不支持真正的透明/毛玻璃效果 |

---

## 三、数据源

### DeepSeek 官方余额 API

```
GET https://api.deepseek.com/user/balance
Authorization: Bearer <YOUR_API_KEY>
Accept: application/json
```

**响应示例：**

```json
{
  "is_available": true,
  "balance_infos": [
    {
      "currency": "CNY",
      "total_balance": "110.00",
      "granted_balance": "10.00",
      "topped_up_balance": "100.00"
    }
  ]
}
```

| 字段 | 说明 |
|------|------|
| `is_available` | 余额是否足够（判断能否继续调用 API） |
| `total_balance` | 总余额 = 充值余额 + 赠送余额 |
| `topped_up_balance` | 充值余额（永不过期） |
| `granted_balance` | 赠送余额（可能有有效期） |

### 今日消费计算方式

DeepSeek 余额 API **不直接提供"今日消费"数据**，采用**本地快照差值法**：

```
今日消费 = 今日首次余额 - 当前余额
```

**流程：**

```
程序启动
  │
  ├─→ [1] 读取本地 snapshot.json
  │      └─ 获取 today_first_balance（今日首次记录的余额）
  │
  ├─→ [2] 调用 /user/balance API
  │      └─ 获得 current_balance
  │
  ├─→ [3] 日期判断
  │      ├─ 若跨天 → 重置 today_first_balance = current_balance
  │      └─ 若同日 → 今日消费 = today_first_balance - current_balance
  │
  ├─→ [4] 更新 snapshot.json
  │
  └─→ [5] 刷新 UI 显示
```

**特殊情况处理：**
- **首次启动**（无历史快照）：`today_first_balance = current_balance`，今日消费 = 0
- **充值后余额增加**：今日消费可能为负数 → 显示"¥0.00"并重置基准
- **跨天切换**：新的一天首次刷新时自动重置 `today_first_balance`

---

## 四、UI/UX 设计

### 4.1 主窗口布局

```
┌──────────────────────────────────┐
│  🔷 DeepSeek              ─ □ ✕ │  ← 标题栏（可拖拽移动窗口）
├──────────────────────────────────┤
│                                  │
│        💰 后 台 余 额            │  ← 标签（11pt，灰色）
│                                  │
│        ¥  108.50                 │  ← 大数字（26pt，深色 Bold）
│                                  │
│    充值 ¥100.00  ｜  赠送 ¥8.50  │  ← 明细小字（9pt，灰色）
│                                  │
│  ────────────────────────────    │  ← 分割线
│                                  │
│     📉 今日消费                  │
│        ¥  1.50                   │  ← 中号数字（18pt）
│                                  │
│  上次更新: 14:30:05              │  ← 时间戳（8pt，右下角）
│  ┌──────────────────────────┐    │
│  │  🔄 刷新      ⚙ 设置     │    │  ← 底部操作栏
│  └──────────────────────────┘    │
└──────────────────────────────────┘
```

**窗口尺寸：** 260 × 210 px（紧凑卡片式）

### 4.2 视觉规范

| 属性 | 值 |
|------|-----|
| 窗口大小 | 260 × 210 px |
| 圆角 | 16px |
| 背景 | `rgba(255, 255, 255, 0.78)` + 毛玻璃模糊 |
| 边框 | `1px solid rgba(255,255,255,0.4)` |
| 阴影 | `0 8px 32px rgba(0, 0, 0, 0.10)` |
| 字体族 | `Microsoft YaHei` (中文) / `Segoe UI` (数字) |
| 余额数字 | 26pt, Bold, `#1a1a1a` |
| 消费数字 | 18pt, `#e74c3c`（红色表示支出） |
| 窗口默认位置 | 屏幕右上角，贴边 20px |
| 置顶 | 默认开启（可配置关闭） |

### 4.3 交互行为

| 操作 | 行为 |
|------|------|
| 拖拽标题栏 | 移动窗口位置 |
| 点击 🔄 | 立即手动刷新 |
| 点击 ⚙ | 打开设置面板 |
| 点击 ✕ | 最小化到系统托盘（不退出） |
| 双击托盘图标 | 显示/隐藏窗口 |
| 右键托盘图标 | 弹出菜单：显示、刷新、设置、退出 |
| 鼠标悬停余额 | Tooltip 显示完整余额明细 |
| 滚轮 | 无操作（避免误触） |

### 4.4 状态显示

| 状态 | 视觉表现 |
|------|---------|
| **正常** | 白色毛玻璃，数据正常显示 |
| **刷新中** | 刷新按钮旋转动画，数据显示上次值 |
| **网络错误** | 余额位置变灰，显示"⚠ 无法连接"，保留上次数据 |
| **API Key 未配置** | 显示"⚡ 请配置 API Key"，点击跳转设置 |
| **余额不足** | 余额数字变橙色警告（`is_available: false`） |

---

## 五、设置面板

```
┌──────────────────────────────────┐
│  设置                     ─ □ ✕ │
├──────────────────────────────────┤
│  API Key                        │
│  ┌────────────────────────────┐ │
│  │ sk-xxxxxxxxxxxxxxxxxxxxxxxx│ │ ← 密码框（掩码显示）
│  └────────────────────────────┘ │
│  [测试连接]                      │
│                                  │
│  刷新间隔                        │
│  ○ 1 分钟  ● 5 分钟  ○ 10 分钟  │
│  ○ 30 分钟 ○ 自定义: ___ 分钟    │
│                                  │
│  窗口行为                        │
│  ☑ 始终置顶                      │
│  ☑ 显示系统托盘图标               │
│  ☐ 开机自动启动                   │
│                                  │
│  外观                            │
│  透明度: [━━━━━━━○──] 85%       │
│                                  │
│            [恢复默认] [保存]      │
└──────────────────────────────────┘
```

---

## 六、数据存储

### 文件位置

```
%APPDATA%\DeepSeekMonitor\snapshot.json
```
（实际路径：`C:\Users\<用户名>\AppData\Roaming\DeepSeekMonitor\snapshot.json`）

### 数据结构

```json
{
  "api_key": "<base64_encoded>",
  "refresh_interval_minutes": 5,
  "window_opacity": 0.85,
  "always_on_top": true,
  "show_tray_icon": true,
  "window_x": 1660,
  "window_y": 40,
  "today_first_balance": 110.00,
  "today_first_time": "2026-06-14T00:05:00",
  "last_balance": 108.50,
  "last_updated": "2026-06-14T14:30:00",
  "balance_history": [
    {"time": "2026-06-13T23:55:00", "balance": 110.00},
    {"time": "2026-06-14T00:05:00", "balance": 110.00},
    {"time": "2026-06-14T08:00:00", "balance": 109.20}
  ]
}
```

| 字段 | 说明 |
|------|------|
| `api_key` | Base64 编码的 API Key（非明文，简单防护） |
| `refresh_interval_minutes` | 自动刷新间隔 |
| `window_opacity` | 窗口透明度 (0.3 - 1.0) |
| `window_x` / `window_y` | 上次关闭时的窗口位置 |
| `today_first_balance` | 今日首次记录的余额（基准线） |
| `today_first_time` | 基准线记录时间 |
| `last_balance` | 最近一次查询到的余额 |
| `last_updated` | 最近一次查询时间 |
| `balance_history` | 最近 30 条余额快照（滚动覆盖） |

### 配置文件（可选）

首次运行时若未检测到 API Key，在项目同级目录生成 `.env` 模板：

```env
DEEPSEEK_API_KEY=sk-your-key-here
```

方便高级用户直接编辑。

---

## 七、项目文件结构

```
deepseek-monitor/
├── main.py                    # 程序入口，初始化 QApplication
├── api/
│   └── deepseek_client.py     # DeepSeek API 封装（余额查询）
├── ui/
│   ├── overlay_window.py      # 主弹窗（透明毛玻璃卡片）
│   ├── settings_dialog.py     # 设置对话框
│   ├── tray_icon.py           # 系统托盘图标与菜单
│   └── styles.py              # QSS 样式常量
├── core/
│   ├── config.py              # 配置读写（snapshot.json 管理）
│   ├── calculator.py          # 消费差值计算 + 跨天逻辑
│   └── scheduler.py           # QTimer 定时刷新调度
├── utils/
│   └── crypto_utils.py        # API Key 简单编解码
├── assets/
│   ├── icon.ico               # 应用图标
│   ├── icon.png               # 托盘图标 (16×16 / 32×32)
│   └── icon@2x.png            # 高 DPI 图标
├── requirements.txt           # Python 依赖清单
├── build.bat                  # PyInstaller 一键打包脚本
└── DESIGN.md                  # 本设计文档
```

---

## 八、数据流图

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   snapshot   │ ←── │   Config Manager │ ←── │   Calculator    │
│   .json      │     │   (读/写配置)     │     │   (差值计算)     │
└──────────────┘     └────────┬─────────┘     └────────┬────────┘
                              │                        │
                              ▼                        ▼
                     ┌─────────────────┐     ┌──────────────────┐
                     │   API Client    │────▶│  Overlay Window  │
                     │ /user/balance   │     │  (UI 渲染)        │
                     └─────────────────┘     └────────┬─────────┘
                                                      │
                              ┌───────────────────────┤
                              ▼                       ▼
                     ┌──────────────┐        ┌──────────────┐
                     │  QTimer 定时  │        │  用户手动操作  │
                     │  (自动刷新)   │        │  (点击刷新)    │
                     └──────────────┘        └──────────────┘
```

---

## 九、开发阶段计划

| 阶段 | 内容 | 产出物 |
|------|------|--------|
| **Phase 1** | API 客户端 + 本地存储 + 差值计算 | 命令行可验证数据流 |
| **Phase 2** | PyQt6 透明窗口 + 毛玻璃 + 基础布局 | 可见的桌面弹窗 |
| **Phase 3** | 系统托盘 + 设置面板 + 完整交互 | 完整体验闭环 |
| **Phase 4** | PyInstaller 打包为单文件 .exe | 可分发版本 |
| **Phase 5** | 开机自启 + 皮肤自定义 + bug 修复 | 迭代增强 |

---

## 十、风险清单

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|---------|
| DeepSeek API 接口变更 | 低 | 高 | 封装在单一 client 模块，一处修改 |
| 充值后「今日消费」显示负数 | 中 | 低 | 检测余额增加时重置基准线 |
| 网络波动导致刷新失败 | 中 | 低 | 失败保留上次数据，显示错误标记 |
| PyInstaller 打包杀软误报 | 中 | 中 | 代码签名 / 提供源码运行方式 |
| API Key 本地泄露风险 | 低 | 中 | Base64 编码 + `%APPDATA%` 用户隔离目录 |
| 高 DPI 下窗口模糊 | 低 | 低 | Qt6 原生支持 `AA_EnableHighDpiScaling` |

---

## 十一、依赖清单

```
# requirements.txt
PyQt6>=6.5.0          # UI 框架
PyQt6-Qt6>=6.5.0      # Qt6 运行时
requests>=2.31.0       # HTTP 客户端
```

> 仅 2 个第三方依赖，极简。

---

## 十二、设计决策总结

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 技术栈 | Python + PyQt6 | 透明窗口原生支持，开发快 |
| 窗口风格 | 无边框 + 毛玻璃 | 模仿 macOS 小组件，现代感 |
| 数据来源 | `/user/balance` API | 官方唯一余额接口 |
| 消费计算 | 本地差值法 | API 不提供消费数据，只能自算 |
| Token 统计 | **不做** | 无法准确获取，不做假数据 |
| API Key 存储 | Base64 编码 + 用户目录隔离 | 简单防护，不引入加密依赖 |
| 打包方式 | PyInstaller 单文件 .exe | 便携，无需安装 Python |
| 刷新频率 | 默认 5 分钟 | 平衡实时性与 API 请求频率 |

---

*待用户确认后进入 Phase 1 开发。*
