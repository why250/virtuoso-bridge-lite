# 高层 `export_netlist()` API 是怎样创建出来的

本文以已经验证的 `test_tb/res_tb/maestro` 为证据，说明高层
`client.maestro.export_netlist()` 为什么存在、在代码中由哪些部分构成，以及
一次调用从 Python 到本地文件经历了什么。

## 起点：已有的低层能力

Cadence 提供的核心 SKILL 操作是：

```skill
maeCreateNetlistForCorner(test corner remoteDirectory ?session session)
```

项目原本已经将它封装为低层 API：

```python
client.maestro.create_netlist_for_corner(
    "test_tb_res_tb_1", "Nominal", "/tmp/netlist", session="fnxSession1"
)
```

它只负责发送一条已验证的 SKILL 命令。调用者仍需自己决定：打开哪个
Maestro session、如何找到 test/corner、创建远端临时目录、下载哪些文件、关闭
session，以及怎样避免覆盖旧的本地结果。

`export_netlist()` 就是把这些固定而容易遗漏的步骤放到一个稳定的公共 API 中，
而不替代 Cadence 的原生 netlister。

## API 的形状

```python
client.maestro.export_netlist(
    lib,
    cell,
    *,
    test=None,
    corner="Nominal",
    output_root="output",
    overwrite=False,
)
```

它返回 `MaestroNetlistExport`：

```python
MaestroNetlistExport(
    test="test_tb_res_tb_1",
    corner="Nominal",
    output_dir=Path(...),
    input_scs=Path(... / "input.scs"),
    netlist=Path(... / "netlist"),
)
```

返回路径对象而不是原始 SKILL 文本，让后续 Python 程序能直接读取或传递产物。

## 从调用到文件的实现链

```text
client.maestro.export_netlist("test_tb", "res_tb")
        |
        v
MaestroOps facade  (maestro/ops.py)
        |
        v
export_netlist()  (maestro/writer.py)
        |
        +-- open_session(lib, cell)
        |     -> maeOpenSetup(... "maestro")
        |
        +-- maeGetSetup(?session ...)
        |     -> test_tb_res_tb_1
        |
        +-- maeGetSetup(?typeName "corners" ?session ...)
        |     -> Nominal
        |
        +-- create_netlist_for_corner(...)
        |     -> maeCreateNetlistForCorner(...)
        |
        +-- download_file(.../netlist/input.scs)
        +-- download_file(.../netlist/netlist)
        |
        +-- rm -rf <API 创建的 /tmp 目录>
        +-- close_session(session)
```

`MaestroOps` 只把独立函数绑定成 `client.maestro.*` 方法；真正的工作流位于
`writer.py`。这样保留了项目既有的函数式实现和兼容性，同时向用户提供一致的
面向对象入口。

## 关键设计决定

### 1. 用后台 session，而不是依赖 GUI 焦点

网表导出不需要运行仿真，也不需要用户点击 Maestro 窗口。API 自己通过
`maeOpenSetup` 打开临时后台 session，结束时关闭它。因此不会误用当前聚焦的
其他 Maestro，也不会保存或修改配置。

### 2. 先读取配置，再调用 netlister

`test=None` 只有在配置恰好只有一个 test 时才允许自动选择；多个 test 时抛错。
`corner="Nominal"` 会验证 `Nominal` 确实存在。这样避免了“第一个 test/corner”
被静默选中而导出错误网表。

在 `test_tb/res_tb` 里，配置返回唯一 test `test_tb_res_tb_1` 和唯一 corner
`Nominal`，所以默认调用无歧义。

### 3. 明确区分远端临时产物和本地产物

Cadence 总是把生成结果写在远端路径；API 使用唯一的
`/tmp/vb_maestro_netlist_<uuid>` 避免并发冲突，再通过既有
`client.download_file()` 传回本地。它不会另起 SCP 或 SSH 实现。

默认本地目录编码了 library、cell、test 和 corner：

```text
output/<lib>/<cell>/netlist/<test>__<corner>/
```

对于本例，这就是：

```text
output/test_tb/res_tb/netlist/test_tb_res_tb_1__Nominal/
```

### 4. 默认不覆盖已有网表

如果上述目录已存在，API 在调用 Cadence 前抛出 `FileExistsError`。只有调用者
明确传 `overwrite=True`，才会替换 `input.scs` 与 `netlist`。这是为了防止不同
时间导出的网表被无意替换。

### 5. 两个输出文件的含义

`netlist` 是电路本身。本例为：

```spectre
V0 (net2 0) vsource dc=1 type=dc
R0 (net2 0) resistor r=1K
```

`input.scs` 是可直接给 Spectre 的完整输入：它包含该电路、`ade_e.scs`、PDK
模型、温度、仿真选项和 DC operating-point 分析。高层 API 下载两者，是因为
设计审阅通常需要前者，而独立复现实例通常需要后者。

## 如何验证这个封装

创建 API 时做了两层验证：

1. daemon-free 单元测试覆盖单 test 自动选择、多 test 错误、corner 验证、输出
   目录覆盖保护、文件下载和 session 清理。
2. 在 Virtuoso Studio IC25.1 的 `test_tb/res_tb/maestro` 上 live validation：
   成功生成并下载 `test_tb_res_tb_1/Nominal` 的 `input.scs` 和 `netlist`。

因此，这个高层 API 的作用不是产生新的网表格式，而是把已验证的原生
`maeCreateNetlistForCorner` 调用变成安全、可复用且可测试的完整导出工作流。
