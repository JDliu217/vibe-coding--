# a04caf4审查证据

目标提交 `a04caf4c57e334a796adf171593b8d5621d09f50`，基线 `15972701720df0952a8d87d48d7cffb78d1a6a85`。验证完成后才提交本目录，原报告不重新绑定到归档提交。

- [审查结果](审查结果.md)：3项确认的新P2及边界。
- [完整RQG报告](修改说明.md)与[最终输出](verify-output.txt)：退出1；工具生成的 `final_status: PENDING_VERIFY` 不由只读verify回写，以输出为准。
- [后端结果](backend-results.json)与[脚本](backend-review.py.txt)：真实MySQL事务、回滚、并发。
- [浏览器结果](browser-results.json)与[脚本](browser-review.mjs.txt)：受控API下的响应交错。
- [完整链路结果](integration-results.json)与[脚本](integration-review.mjs.txt)：真实前端/API/MySQL，只延迟已提交响应，不替换数据库结果。
- [静态Trace](trace-output.txt)与[检索Top10](search-output.txt)：辅助所有权判断，不替代行为验证。

测试工具为官方MySQL 8.4、仓库requirements、外部httpx 0.28.1、Playwright 1.56.1和系统Chromium。脚本中的 `/workspace` 是实际运行环境位置，跨机器复现需准备独立数据库并调整路径。数据库只用合成种子资源，检查脚本作为文本证据保存，不自动执行或设置Git hook。
