# Bridge 的结构化 Virtuoso 会话检查

## 目的与边界

对正在运行的 Virtuoso 做检查时，优先通过 `virtuoso-bridge` 的
结构化查询获取状态，而不是依赖截图或人工读取 GUI。本流程只读取
Virtuoso 的窗口和 Maestro/ADE 配置，不保存 cellview、不运行仿真、
也不改变窗口或会话状态。

## 连接与环境确认

bridge 从项目 `.env`（或显式指定的环境文件）读取远端主机、端口等
配置。`virtuoso-bridge status` 检查 SSH tunnel 与 CIW 中已加载的
SKILL daemon 是否可响应，并返回 Virtuoso 版本、远端主机和工作目录。

这一步确认的是 Python 客户端能够通过 tunnel 向目标 Virtuoso 进程
发送 SKILL 查询；它不通过 OS 截图或窗口自动化猜测进程状态。

## “当前”窗口和 Maestro 会话的判定

`current` 是 **Virtuoso 内部当前焦点窗口**，不是操作系统当前前台
应用，也不是画面中视觉上最靠前的窗口。bridge 将只读 SKILL 发送到
CIW，由 Virtuoso 的 HI（Human Interface）API 返回该窗口对象：

```skill
let((w)
  w = hiGetCurrentWindow()
  list(
    w~>windowNum
    hiGetWindowName(w)
    w->davSession
    maeGetSessions()
  )
)
```

各字段的作用如下：

| 查询 | 含义 |
|---|---|
| `hiGetCurrentWindow()` | Virtuoso GUI 事件系统维护的当前窗口对象。 |
| `w~>windowNum` | 稳定地将当前窗口和窗口列表对应起来。 |
| `hiGetWindowName(w)` | 用于识别窗口类型，如 ADE Explorer、schematic 或 layout。 |
| `w->davSession` | ADE Explorer/Assembler 窗口绑定的 Maestro session ID。 |
| `maeGetSessions()` | 所有打开的 Maestro session，用来交叉验证并发现其他会话。 |

`virtuoso-bridge windows` 先以 `hiGetWindowList()` 列举所有 Virtuoso
窗口，再将 `hiGetCurrentWindow()` 返回的 `windowNum` 标为 focused；若该
窗口含有 `davSession`，则显示它绑定的 Maestro session。

若用户切换到终端、浏览器等其他应用，`hiGetCurrentWindow()` 仍表达
Virtuoso 上一次处于活动状态的内部窗口，而不会改为 OS 的前台窗口。
当模态对话框阻塞 CIW 时，查询也可能被阻塞；此时才需要 GUI/X11
诊断手段。

## Maestro 的结构化快照

`virtuoso-bridge snapshot` 首先读取当前窗口标题并将其分类。当它是
Maestro/ADE 窗口时，针对同一个 `davSession` 发出只读查询，例如：

```skill
maeGetSetup(?session session)
maeGetEnabledAnalysis(test ?session session)
maeGetAnalysis(test "stb" ?session session)
maeGetAnalysis(test "dc" ?session session)
```

由此获取测试名称、已启用 analysis 和每个 analysis 的配置。默认的
CLI 快照输出简要配置；`snapshot --json` 或 Python 的 Maestro reader
可用于需要更完整内存结构的检查。指定 `snapshot -o ROOT` 会写出磁盘
快照，因此不属于严格的只读检查。

对当前 schematic/layout 的结构化读取则以 `geGetEditCellView()` 取得
当前编辑 cellview，并由 reader 查询 instances、nets、pins、CDF 参数等
数据库对象属性；同样不是图像识别。

## 截图的角色

截图是补充诊断能力，而非会话识别的主路径。它适合检查模态对话框、
GUI 报错、显示状态或波形外观；但 session ID、analysis 参数、设计
连通性和对象属性应以 SKILL/数据库查询为准。使用截图会生成图像文件，
因而在严格只读检查中应仅在确有需要时明确请求。
