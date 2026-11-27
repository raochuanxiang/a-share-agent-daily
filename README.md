# A股智能体概念股日报

工作日北京时间 11:00 自动获取 Eastmoney AI/智能体概念板块成分股，按综合热度排序取 Top 10，为每只股票附短摘要和当日新闻链接，并推送飞书。

见 [部署说明](docs/deploy.md) 与 [流程图](docs/flowchart.mmd)。运行前需在 GitHub 仓库添加 Actions Secret `FEISHU_WEBHOOK`。

评分采用成交额和涨跌幅的横截面百分位；当前程序的资金流、新闻提及热度暂为中性分，报告会明示这一限制，不能视为原定权重的完整实现。
