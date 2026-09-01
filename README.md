# 华南农业大学电费 Home Assistant 集成

通过学校旧版电费接口读取宿舍电表数据的 Home Assistant 自定义集成，支持 UI 配置并符合 HACS Integration 仓库结构。

## 功能

每个房间会创建一个设备和四个传感器：

- 今日用电量（kWh）
- 今日电费（元），按照“今日用电量 × 0.63 元/kWh”计算
- 电表设立以来的累计用电量（kWh）
- 当前余额（元）；实体属性包含余额刷新时间和在线状态

添加集成时可以设置轮询间隔，默认每 60 分钟更新一次。登录 token、timestamp 和 sign 均在内存中动态生成，无需保存账号或 Cookie。

> 学校接口仅提供 HTTP。房间信息会发送到 `http://cz.scau.edu.cn`，请仅在可信网络环境中使用。

## 开发阶段手动部署

1. 找到 Home Assistant 配置目录（与 `configuration.yaml` 同级，通常为 `/config`）。
2. 将本仓库整个 `custom_components/scau_electricity` 目录复制到 Home Assistant，最终路径为 `/config/custom_components/scau_electricity`。
3. 完整重启 Home Assistant；仅重新加载 YAML 无法加载新的 Python 集成。
4. 打开 **设置 → 设备与服务 → 添加集成**，搜索“华南农业大学电费”。
5. 输入房间名称、房间 ID 与轮询间隔（分钟，默认为 60）。测试数据如下：

   - 房间名称：`泰山2#301`
   - 房间 ID：`121931`

提交时会立即连接服务并验证房间。若失败，请确认 Home Assistant 主机能访问 `http://cz.scau.edu.cn`，并查看日志中的 `custom_components.scau_electricity`。

## 更新与卸载

手动更新时覆盖 `/config/custom_components/scau_electricity` 后重启。卸载时先在“设备与服务”删除配置条目，再删除组件目录并重启。

## HACS 说明

根目录已提供 `hacs.json`。发布到 GitHub 后可添加为 HACS 自定义 Integration 仓库。正式申请进入 HACS 默认仓库前，还需创建 GitHub Release、启用 HACS/hassfest 校验，并向 Home Assistant Brands 提交品牌资源。

## 接口与限制

- `/login` 返回临时会话字段。
- `/api/zndb/getDBRYL` 返回当日及累计用电量。
- `/api/zndb/getDBYE` 返回余额，接口的“分”会转换为“元”。
- 这是依赖学校非公开旧接口的第三方集成，服务端字段或访问策略变化可能导致暂时不可用。

## 许可证

本项目采用 [MIT License](LICENSE)。
