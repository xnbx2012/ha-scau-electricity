# 华南农业大学电费 Home Assistant 集成

[English](README.md) | [简体中文](README_zh-CN.md)

通过学校旧版电费接口读取宿舍电表数据的 Home Assistant 自定义集成，能够读取用电量和电费余额数据，默认按照学校公布的 0.6259 元/kWh 进行电费计算，添加集成时可以自定义单价，余额和用电量是接口中直接读出的数据。

## 功能

每个房间会创建一个设备和四个传感器：

- 今日用电量（kWh；14 点刷新前为 0 时自动使用前一天数据）
- 今日电费（元），按照“今日用电量 × 0.6259 元/kWh”计算
- 电表设立以来的累计用电量（kWh）
- 当前余额（元）；实体属性包含余额刷新时间和在线状态

添加集成时可以设置轮询间隔，默认每 60 分钟更新一次，并可设置失败重试次数、重试间隔和电费单价，默认分别为 5 次、10 秒和 0.6259 元/kWh。登录 token、timestamp 和 sign 均在内存中动态生成，无需保存账号或 Cookie。

![HA 显示效果](image-1.png)

> 学校接口仅提供 HTTP。房间信息会发送到 `http://cz.scau.edu.cn` 以获取相应数据。

## 安装步骤

### 手动安装

1. 找到 Home Assistant 配置目录（与 `configuration.yaml` 同级，通常为 `/config`）。
2. 将本仓库整个 `custom_components/scau_electricity` 目录复制到 Home Assistant，最终路径为 `/config/custom_components/scau_electricity`。
3. 完整重启 Home Assistant；仅重新加载 YAML 无法加载新的 Python 集成。
4. 打开 **设置 → 设备与服务 → 添加集成**，搜索“华南农业大学电费”。
5. 输入房间名称、房间 ID、轮询间隔（分钟，默认为 60）、重试次数（默认为 5）、重试间隔（秒，默认为 10）和电费单价（默认为 0.6259 元/kWh）。对应于下面图中显示的房间数据：

   - 房间名称：`泰山2#301`
   - 房间 ID：`121931`

![房间名称和房间 ID](image.png)

提交时会立即连接服务并验证房间。若失败，请确认 Home Assistant 主机能访问 `http://cz.scau.edu.cn`，并查看日志中的 `custom_components.scau_electricity`。

### 更新与卸载

手动更新时覆盖 `/config/custom_components/scau_electricity` 后重启。卸载时先在“设备与服务”删除配置条目，再删除组件目录并重启。

### HACS 安装

暂未上架 HACS 默认仓库。

## MCP 服务

本仓库同时提供独立的 stdio MCP 服务，可读取相同的电表数据。uv 安装方式、客户端配置、可用工具以及后续 `uvx` 接入说明请查看 [MCP 配置文档](mcp/README.md)。

## 许可证

本项目采用 [MIT License](LICENSE)。
