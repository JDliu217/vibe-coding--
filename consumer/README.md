# 鲜拾 · 生鲜电商消费端

这是攻防实验里的消费单元。当前实现正常购物：注册、登录、浏览、购物车、下单、库存变化、订单查询和管理后台。不包含优惠券、促销、秒杀、真实支付、短信和风控。

攻击端仍在仓库的 `attacker/`，使用另一个数据库 `attack_console`。本目录只使用 `consumer_shop`。

## 本地启动

本机验证时没有安装 Docker，所以用 Python 虚拟环境和 Next.js 直接启动。`docker-compose.yml` 仍可用于有 Docker 的环境，数据库默认连宿主机 MySQL。

```powershell
cd consumer
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH = "$pwd\libs\common"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\seed.py
```

五个服务需要各自的 `PYTHONPATH` 只包含 `libs\common`，并用 `--app-dir` 指向对应服务：

| 服务 | 端口 | 目录 |
| --- | --- | --- |
| 网关 | 8090 | services/api-gateway |
| 鉴权 | 8091 | services/auth-service |
| 商品 | 8092 | services/catalog-service |
| 库存 | 8093 | services/inventory-service |
| 订单 | 8094 | services/order-service |

```powershell
$env:PYTHONPATH = "$pwd\libs\common"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir services\auth-service --port 8091
```

其余服务把目录和端口换成上表。前端：

```powershell
cd frontend
npm install
npm run dev
```

打开 http://localhost:3000 。浏览器请求 `/api` 会被 Next.js 转发到网关 `127.0.0.1:8090`。

数据库连接读取 `consumer/.env`。如果这里没有密码，会借用攻击端 `.env` 里的主机、端口、用户和密码，但库名固定为 `consumer_shop`。示例见 `.env.example`，不要提交真实密码。

## 演示账号

| 角色 | 手机号 | 密码 |
| --- | --- | --- |
| 管理员 | 13800000000 | Admin123456 |
| 用户 | 13900001001 | User123456 |

普通注册永远是用户角色，不能自行变成管理员。

## 已做的技术选择

- 网关也用 FastAPI，不用 Node。五个后端服务都通过 HTTP 协作。
- 五个服务共用一个 MySQL 库，但只通过接口改自己的表。商品改价不会回写历史订单。
- 金额用整数分。主键用自增整数。
- 密码用 bcrypt。登录态用 JWT，有效期 7 天。
- 下单必须带 `Idempotency-Key`。同一用户、同一标识、同一内容返回同一订单；内容不同返回冲突。
- 库存预占按订单号幂等。多件商品在一次数据库事务里全部成功或全部不生效。
- 创建成功后库存从预占确认为扣减。取消已创建订单会恢复一次库存；已完成订单不能取消；重复取消不再加库存。
- 卡在“创建中”的订单用 `python scripts/recover_orders.py` 收敛，不使用消息队列。
- 购物车保存在浏览器本地，按用户编号隔离；未登录使用 guest。

## 文档

- [需求整理](docs/PRD.md)
- [架构](docs/architecture.md)
- [接口](docs/api.md)
