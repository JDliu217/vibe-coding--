# 接口

浏览器只访问网关 `/api`。错误统一为：

```json
{"error": {"code": "INSUFFICIENT_STOCK", "message": "库存不足", "traceId": "..."}}
```

响应头带 `x-request-id`。各服务的 OpenAPI 在对应端口的 `/docs`。

| 方法 | 路径 | 身份 |
| --- | --- | --- |
| POST | /api/auth/register | 公开 |
| POST | /api/auth/login | 公开 |
| GET | /api/auth/me | 登录 |
| GET | /api/catalog/categories | 公开 |
| GET | /api/catalog/products | 公开 |
| GET | /api/catalog/products/{id} | 公开 |
| POST | /api/orders | 登录，需要 Idempotency-Key |
| GET | /api/orders/my | 登录 |
| GET | /api/orders/{id} | 订单主人或管理员 |
| POST | /api/orders/{id}/complete | 订单主人或管理员 |
| POST | /api/orders/{id}/cancel | 订单主人或管理员 |
| GET | /api/admin/overview | 管理员 |
| GET/POST | /api/admin/products | 管理员 |
| PATCH | /api/admin/products/{id} | 管理员 |
| GET | /api/admin/inventory | 管理员 |
| PATCH | /api/inventory/{productId} | 管理员 |
| GET | /api/admin/orders | 管理员 |

商品列表和详情由网关补上可用库存。库存服务失败时，网关返回 503，不返回缺少库存的成功数据。
