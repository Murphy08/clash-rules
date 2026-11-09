# Clash routing fragments

**3x-ui 基础路由（每天北京时间 00:00 直接同步 ACL4SSR）**

[https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/3x-ui.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/3x-ui.yaml)

将此地址填入 3x-ui 的「全局路由规则 HTTPS URL」，保存后刷新面板订阅。保留「节点选择」「PROXY」「兜底选择」和内联规则，最后一条为 `MATCH,兜底选择`。

参考 [kuchiki111/3x-ui-clash-ymal](https://github.com/kuchiki111/3x-ui-clash-ymal) 的生成逻辑，采用相同的规则源、顺序和三个策略组；每天直接下载 [ACL4SSR 源库](https://github.com/ACL4SSR/ACL4SSR/tree/master/Clash/Providers) 中的 `LocalAreaNetwork`、`UnBan`、`BanAD`、`BanProgramAD`、`ProxyGFWlist`、`ChinaDomain`、`ChinaIp`，展开为内联规则。规则和分组设置见 [本地策略](config/3x-ui-policy.yaml)，校验值见 [同步报告](reports/3x-ui.json)。

「兜底选择」默认直连，也可切换为「节点选择」。实际节点由 3x-ui 提供；所有规则已内联，无需客户端下载远程规则提供者。下载或校验失败时保留最后有效文件。GitHub 定时任务可能延迟。

## 分组配置（每周同步）

Files are 3x-ui global routing fragments. They contain proxy groups, rule providers, and rules; node definitions and credentials remain in 3x-ui.

The scheduled workflow runs every Monday at 00:00 China Standard Time. It refreshes the catalog from `sub-web-modify`; temporary non-404 failures keep their last valid generated file. Sources returning HTTP 404 are excluded from later runs.

Only profiles converted and validated successfully are listed below. Unsupported templates and sources requiring authentication are omitted; details are in [the latest report](reports/latest.json).

| Configuration | Raw YAML |
| --- | --- |
| 默认 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-c8d09cf955.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-c8d09cf955.yaml) |
| 默认（自动测速） | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-3d18f9d7ec.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-3d18f9d7ec.yaml) |
| 默认（索尼电视专用） | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-80d97a0a11.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-80d97a0a11.yaml) |
| ACL_全分组 Dream修改版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d79f9177ef.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d79f9177ef.yaml) |
| ACL_精简分组 Dream修改版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-74e2fb0542.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-74e2fb0542.yaml) |
| emby-TikTok-流媒体分组-去广告加强版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-eb70cd8ead.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-eb70cd8ead.yaml) |
| 流媒体通用分组 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-a4366cb30c.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-a4366cb30c.yaml) |
| ACL_默认版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-aa3fc0a878.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-aa3fc0a878.yaml) |
| ACL_无测速版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d705ef4916.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d705ef4916.yaml) |
| ACL_去广告版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-7d3f7571aa.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-7d3f7571aa.yaml) |
| ACL_多国家版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-464cfa63e0.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-464cfa63e0.yaml) |
| ACL_无Reject版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-ebe81f7195.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-ebe81f7195.yaml) |
| ACL_无测速精简版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-a106927163.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-a106927163.yaml) |
| ACL_全分组版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-4c54cfcccc.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-4c54cfcccc.yaml) |
| ACL_全分组谷歌版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-6d61cd6c6d.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-6d61cd6c6d.yaml) |
| ACL_全分组多模式版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-612da306fe.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-612da306fe.yaml) |
| ACL_全分组奈飞版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-b9de01036e.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-b9de01036e.yaml) |
| ACL_精简版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-ae7a0ef570.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-ae7a0ef570.yaml) |
| ACL_去广告精简版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-0899621214.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-0899621214.yaml) |
| ACL_Fallback精简版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-47b53945dd.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-47b53945dd.yaml) |
| ACL_多国家精简版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-736848f7dc.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-736848f7dc.yaml) |
| ACL_多模式精简版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-a69caca566.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-a69caca566.yaml) |
| 常规规则 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-15095693ea.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-15095693ea.yaml) |
| PharosPro无测速 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-9b97e29531.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-9b97e29531.yaml) |
| OoHHHHHHH | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-e6a1d5fbe1.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-e6a1d5fbe1.yaml) |
| CFW-TAP | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-6c7ef8b075.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-6c7ef8b075.yaml) |
| lhl77全分组（定期更新） | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-575cc7e190.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-575cc7e190.yaml) |
| lhl77简易版（定期更新） | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d1bc3aaf98.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d1bc3aaf98.yaml) |
| ConnersHua 神机规则 Outbound | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d184814532.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d184814532.yaml) |
| ConnersHua 神机规则 Inbound 回国专用 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-0ad3474cb1.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-0ad3474cb1.yaml) |
| lhie1 洞主规则（使用 Clash 分组规则） | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-8b45914f11.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-8b45914f11.yaml) |
| lhie1 洞主规则完整版 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d1cb8bef16.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d1cb8bef16.yaml) |
| eHpo1 规则 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-9a2719967f.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-9a2719967f.yaml) |
| 品云专属配置（仅香港区域分组） | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-59559d3ce2.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-59559d3ce2.yaml) |
| 品云专属配置（全地域分组） | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-1770ee57e0.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-1770ee57e0.yaml) |
| nzw9314 规则 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-cd3ddb6fe6.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-cd3ddb6fe6.yaml) |
| maicoo-l 规则 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-b48a890e92.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-b48a890e92.yaml) |
| DlerCloud Platinum 李哥定制规则 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-9036b897ff.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-9036b897ff.yaml) |
| DlerCloud Gold 李哥定制规则 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-0edb50fef4.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-0edb50fef4.yaml) |
| DlerCloud Silver 李哥定制规则 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-df2e093e45.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-df2e093e45.yaml) |
| ProxyStorage自用 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-41c86d096a.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-41c86d096a.yaml) |
| ShellClash修改版规则 (by UlinoyaPed) | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-c0da4291ba.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-c0da4291ba.yaml) |
| LinkCube | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-20d7fe46fa.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-20d7fe46fa.yaml) |
| 咸鱼 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-0c4b6ac0d0.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-0c4b6ac0d0.yaml) |
| CNIX | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-02e2ff820d.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-02e2ff820d.yaml) |
| Nirvana | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-aeb31188ce.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-aeb31188ce.yaml) |
| V2Pro | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-75060bcc14.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-75060bcc14.yaml) |
| 史迪仔-自动测速 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-dc371f43b8.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-dc371f43b8.yaml) |
| 史迪仔-负载均衡 | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-8ed5ceaa2a.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-8ed5ceaa2a.yaml) |
| Maying | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-3c8e205f2d.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-3c8e205f2d.yaml) |
| Ytoo | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d7d4fd15c1.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-d7d4fd15c1.yaml) |
| NyanCAT | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-2982ce3d05.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-2982ce3d05.yaml) |
| Nexitally | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-cf1e90430a.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-cf1e90430a.yaml) |
| SoCloud | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-6d16aad30c.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-6d16aad30c.yaml) |
| ARK | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-3d62b4bf24.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-3d62b4bf24.yaml) |
| N3RO | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-f32adc9e13.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-f32adc9e13.yaml) |
| Scholar | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-3c479754a6.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-3c479754a6.yaml) |
| NeteaseUnblock | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-83e3d34dfc.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-83e3d34dfc.yaml) |
| Basic | [https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-aa2c96dacf.yaml](https://raw.githubusercontent.com/Murphy08/clash-rules/main/dist/profile-aa2c96dacf.yaml) |

Source catalog: [sub-web-modify Subconverter.vue](https://raw.githubusercontent.com/youshandefeiyang/sub-web-modify/master/src/views/Subconverter.vue)
