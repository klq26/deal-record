# deal-record

收集自己来自各个网站或 APP 的基金历史成交情况，便于后续分类汇总，多维度统计。

spider 包负责去所有买过基金的网站进行数据抓取。通过 login 包下，非 github 管理的 cookie 等数据，把各个网站成交记录统一成一种 json 格式的数组。
category 负责为每笔成交记录或者每只基金填写资产配置分类信息，如果 categoryManager 不认识某只基金，检测时会打开对应的 qieman 和 tiantian 基金的详情页，管理员可以进行人工添加。
database 负责所有的数据库操作，包括建表，增加，查询数据等功能封装。
tools 负责一些后勤信息募集工作，比如交易过的基金，其基本信息、历史净值、分红拆分信息等内容的爬取、录入数据库等。
analytics 模块是功能核心，负责按不同要求查询每个 app、每个用户的当前持仓情况和历史清仓情况。支持按家庭查询，也支持按基金代码分类汇总。可以说，这个包的 output 内容，就是本项目的初衷所需要的。
app 包是 web 展示软件的 client / server 端代码，负责前后端代码书写。