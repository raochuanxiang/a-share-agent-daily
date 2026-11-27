# A股智能体概念股日报

GitHub Actions 工作日北京时间 11:00 获取东方财富 AI/智能体概念股，按成交额40%、涨跌幅30%、主力净流入20%、新闻条数10%计算热度并推送飞书。

新闻接口按个股请求且有频率限制，程序在前三项基础分排名前30的候选中统计新闻热度；这一项不是对所有成分股的全量排名。流程图见 [docs/flowchart.mmd](docs/flowchart.mmd)，部署说明见 [docs/deploy.md](docs/deploy.md)。

Webhook 仅通过 Actions Secret `FEISHU_WEBHOOK` 提供。公开源接口变化或持续限流时工作流报错，不生成假数据。仅供信息参考，不构成投资建议。

PNG 流程图：[docs/flowchart.png](docs/flowchart.png)
