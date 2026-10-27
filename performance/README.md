# 第9周本地性能验收

本目录提供三个真实 JMeter 场景以及采集、复测、对比工具。使用独立的合成数据和密钥，不清空现有 `user.db`、`instance/user.db` 或银行数据。

## 本地环境

需要 Python 3.13、Java 17 或以上、Apache JMeter 5.6.3，以及项目运行依赖、pytest、psutil。当前本地测试服务器使用 Waitress 3.0.2，监听 `127.0.0.1:5099`，固定16个工作线程。Java/JMeter不会替换系统设置。

```powershell
python -m pip install --target .local/tools/python -r requirements-local-tools.txt
```

从 [Apache 官方目录](https://downloads.apache.org/jmeter/binaries/) 下载 JMeter 5.6.3 ZIP及SHA512，校验后解压到 `.local/tools/apache-jmeter-5.6.3`。脚本也支持 `--jmeter` 指定已有安装目录。

## 场景和口径

| 场景 | 目标接口 | 业务成功条件 |
|---|---|---|
| login.jmx | POST /api/v1/auth/login | HTTP 200、业务code 200、返回正式access_token |
| products.jmx | GET /api/ecommerce/products | 分类查询，第一页20条，卖家名称完整 |
| orders.jmx | POST /api/ecommerce/orders | HTTP 201、业务code 201、返回订单及一条订单项 |

下单前每个虚拟用户只登录一次，循环执行加购、下单。账号按线程号隔离；登录与加购样本保留在JTL中，但从下单接口指标中剔除。失败后继续施压，避免错误导致线程提前结束而降低实际负载。登录或加购失败会阻止整组通过验收。

正式采集配置为10/30/50并发，2秒逐步启动，前5秒预热，随后观测20秒，各条件重复2轮。每轮从同一初始数据恢复，包含100个普通用户、20个商户和20000件商品。每件初始库存1000000，避免测试数据耗尽混入性能错误。

p95按nearest-rank计算，包含失败请求的耗时；两轮原始样本合并后计算各条件p95。吞吐为窗口内目标接口请求数除以观测秒数；错误率由HTTP和业务断言共同决定。脚本不把Token、响应正文或请求正文写入JTL。

## 从干净目录复现

以下命令在仓库根目录执行。输出目录和数据目录必须使用新名字，工具会拒绝覆盖已有证据。Windows可将 `python` 替换为 `py -3.13`。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python tools/week9/prepare_baseline.py --output .local/week9/replay-baseline-source
python tools/week9/seed.py --data .local/week9/replay-fixture --source .local/week9/replay-baseline-source
python tools/week9/run_suite.py --source .local/week9/replay-baseline-source --fixture .local/week9/replay-fixture --output evidence/week9/replay-baseline --duration 20 --warmup 5 --repeats 2
python tools/week9/run_regression.py --output evidence/week9/replay-regression
python tools/week9/run_suite.py --fixture .local/week9/replay-fixture --output evidence/week9/replay-optimized --duration 20 --warmup 5 --repeats 2
python tools/week9/compare.py --baseline evidence/week9/replay-baseline --optimized evidence/week9/replay-optimized --output evidence/week9/replay-comparison
```

基线源码快照仅加入了双方共用的数据/密钥路径配置、相同连接池上限和相同监控，没有加入业务优化。快照及文件SHA256位于 `evidence/week9/baseline-source.zip` 和 `baseline-source.json`。当前优化代码运行前会在隔离副本创建新增索引；基线不创建这些索引。

## 证据目录

`evidence/week9/baseline` 与 `optimized` 保存每轮原始JTL、JMeter日志、完整运行参数、服务日志、逐请求指标和CPU/内存CSV；`comparison`保存重算的CSV、JSON及中文结果报告。`regression-final`保存最终新增回归和既有RBAC、隧道验收输出。以实际生成文件和退出码为准。

每阶段 `environment.json` 记录实际依赖、机器配置、源码SHA256和初始数据库SHA256。比较工具核验一致性，并逐一检查各接口/并发条件p95下降至少20%、错误率不高于1%、前置操作无失败、样本数至少100。没有预设绝对p95达标值，也不使用“已达标保持”分支规避下降门槛。

## 数据库和监控

本次正式测试的50并发登录第二轮出现全机CPU均值99.8%的异常竞争，原始比较未通过该行的p95门槛；所有失败结果保存在 `comparison-original/` 和原始阶段目录中。随后按执行前保存的 `confirmation/plan.json`，交替对基线、优化版本各补测两轮，使用全部四轮复核更新该条件。其他八个条件保留最初两轮，最终报告明确标注数据来源。

复现同一复核流程：

```powershell
python tools/week9/run_confirmation.py --fixture .local/week9/replay-fixture --baseline-source .local/week9/replay-baseline-source --output evidence/week9/replay-confirmation
python tools/week9/compare.py --baseline evidence/week9/replay-baseline --optimized evidence/week9/replay-optimized --confirmation evidence/week9/replay-confirmation --output evidence/week9/replay-comparison-confirmed
python tools/week9/build_monitor_report.py --baseline evidence/week9/replay-baseline --optimized evidence/week9/replay-optimized --confirmation evidence/week9/replay-confirmation --output evidence/week9/replay-comparison-confirmed
```

既有演示环境保留原路径约定：用户与审计默认位于仓库 `user.db`，电商ORM默认位于 `instance/user.db`。本地工具显式设置 `APP_USER_DB_PATH`、`APP_ECOMMERCE_DB_PATH`、`APP_AUDIT_DB_PATH`；测试时用户和电商共用隔离 `app.sqlite3`，审计写入独立 `audit.sqlite3`。双方配置相同。

`APP_METRICS_FILE`仅在需要时启用逐请求JSONL，不开放额外的公网监控接口，不记录SQL参数、密码和Token。SQL耗时/次数目前仅覆盖ORM语句执行，不含原生SQLite访问和事务提交等待。`resources.csv`采样测试服务进程CPU、内存、线程数及系统CPU。WAL保持 `synchronous=FULL`。

## 正确性和边界

回归包含库存争抢不超卖、同购物车重复下单、重复取消、部分失败时整单回滚、商品卖家与筛选语义、非法数量/分页、订单归属、MFA令牌限制，以及JWT缓存后的过期、篡改、注销检查。

JWT签名验证缓存只保留最多2048条，最长5秒，过期和注销仍逐次检查；它不复用会话密钥、Nonce或签名随机数。登录签发新增唯一jti。SM3原生实现与原实现进行已知输入对照，缺少原生SM3时回退。

压测使用现有业务JSON接口，安全隧道仍作为独立Demo回归。客户端和服务端共享本机，短时结果用于课程检查，不能推断生产最大容量。Redis不是本次必要依赖。
