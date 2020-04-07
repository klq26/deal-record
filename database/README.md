封装数据库操作。

1）fundDBHelper 更新库内基金信息（基础信息 fund_info，各类基金历史净值表 nav_100032 等，还有分红表 dividend，拆分表 split 等）。
2）dealRecordDBHelper 按各自方式写入，查询成交记录（分用户，分 APP 按时间，对应时间之前最近一个分红或拆分日等）。
