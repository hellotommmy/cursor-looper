# Cursor Looper

自动重复发送指令给 Cursor AI 的小工具。当 AI 完成一轮工作（文件夹无变动）后，自动重新发送同一条指令，适用于需要持续推动大工程量任务的场景。

## 工作原理

1. 启动后输入一条指令和重复次数
2. 工具通过键盘自动化将指令发送到 Cursor 聊天框
3. 监控工作区文件变化，判断 AI 是否在工作
4. 当连续 N 秒无文件变化，判定本轮完成
5. 自动发送下一轮指令，直到达到指定次数

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python cursor_looper.py
```

### 指定监控目录

```bash
python cursor_looper.py -w "C:\Users\你的项目路径"
```

### 自定义参数

```bash
python cursor_looper.py -w . -t 45 -k "ctrl+l" --start-wait 180
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-w, --workspace` | `.` | 要监控的工作区目录 |
| `-t, --idle-timeout` | `30` | 文件无变化多少秒后判定 AI 完成 |
| `-k, --hotkey` | `ctrl+l` | 打开 Cursor 聊天的快捷键 |
| `--start-wait` | `120` | 等待 AI 开始工作的超时秒数 |
| `--send-delay` | `1.0` | 按下聊天快捷键后等待多久再粘贴 |

## 使用流程

1. 打开 Cursor IDE，并确保聊天面板可用
2. 在**另一个终端**中启动本工具
3. 输入要重复执行的指令
4. 输入重复次数（0 为无限循环）
5. **立即切换回 Cursor 窗口**（工具会在 2 秒后发送指令）
6. 工具会自动循环执行

## 注意事项

- 发送指令时需要 Cursor 窗口在前台，因为使用了键盘模拟
- 按 `Ctrl+C` 可随时中断循环
- 输入 `quit` / `exit` / `q` 退出程序
- `.git`、`node_modules` 等目录的变化会被自动忽略

## License

MIT
