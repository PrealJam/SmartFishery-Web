# SmartFishery 多身份系统 & 供应商管理功能 - 任务清单

> 使用 sequential-task-runner 技能执行此任务清单
> 本清单实现多身份登录（渔场管理员/鱼苗供应商）和供应链管理功能

---

## [ ] 任务5：数据库设计与表结构扩展

**描述**: 为支持供应商管理和订单系统，创建关键数据库表并修改现有表结构

**要求**:

1. 创建 `suppliers` 表（供应商企业信息）
   - 字段: id, name, contact_person, phone, email, address, registration_date, status(active/inactive), notes, created_at
   - 主键: id，唯一索引: name

2. 创建 `seedling_products` 表（鱼苗产品库）
   - 字段: id, supplier_id(FK), product_name, species, grade, unit_price, cost_price, growth_cycle_days, survival_rate, image_url, description, is_active, created_at, updated_at
   - 索引: idx_supplier_id, idx_species, idx_is_active

3. 创建 `seedling_inventory` 表（库存管理）
   - 字段: id, supplier_id(FK), product_id(FK), quantity, last_updated_at, updated_by
   - 索引: idx_supplier_product

4. 创建 `purchase_orders` 表（采购订单主表）
   - 字段: id, supplier_id(FK), pond_id(FK), created_by(FK users), order_date, expected_delivery_date, actual_delivery_date, status(draft/confirmed/shipped/received/invoiced), total_amount, notes, created_at, updated_at
   - 索引: idx_supplier_id, idx_pond_id, idx_status, idx_order_date

5. 创建 `order_items` 表（订单详情）
   - 字段: id, order_id(FK), product_id(FK), quantity, unit_price, subtotal, created_at

6. 修改 `users` 表
   - 添加字段: supplier_id(nullable FK to suppliers), role 增加 'supplier' 选项
   - 索引: idx_supplier_id

7. 修改 `ponds` 表
   - 添加字段: default_supplier_id(nullable FK to suppliers)

8. 编写迁移脚本，备份现有数据后执行 DDL

**产出**:

- 修改 `smart_fishery_db_2026-04-15_113721.sql` 添加所有新表 DDL 和索引
- 新建 `migrations/001_add_supplier_tables.sql` 迁移脚本

---

## [ ] 任务6：后端API与权限控制层实现

**描述**: 实现供应商管理、鱼苗产品、采购订单的 API 端点，以及细粒度的权限检查装饰器

**要求**:

1. 在 `app.py` 中扩展 User 模型
   - 添加 supplier_id 字段和 Supplier 关系
   - 创建 Supplier、SeedlingProduct、SeedlingInventory、PurchaseOrder、OrderItem ORM 模型

2. 创建权限装饰器 (app.py 中新增)
   - `@role_required(roles=['admin', 'supplier'])` - 角色验证装饰器
   - `@supplier_scope_check` - 供应商数据隔离验证（确保商家仅能访问自己的数据）
   - 验证失败返回 403 Forbidden 和清晰的错误消息

3. 实现管理员端 API 端点 (app.py)
   - `GET /api/suppliers` - 供应商列表（分页、搜索、排序）[@role_required(['admin'])]
   - `POST /api/suppliers/add` - 新增供应商
   - `POST /api/suppliers/<id>/edit` - 编辑供应商信息
   - `DELETE /api/suppliers/<id>` - 删除供应商（逻辑删除）
   - `GET /api/suppliers/<id>/products` - 某供应商的产品列表
   - `GET /api/purchase-orders` - 所有采购订单（含筛选、分页）
   - `POST /api/purchase-orders/create` - 创建采购订单
   - `GET /api/seedling-management/stats` - 鱼苗采购汇总统计

4. 实现商家端 API 端点 (app.py)
   - `GET /api/my-products` - 自己的鱼苗产品列表 [@role_required(['supplier'])]
   - `POST /api/my-products/add` - 添加新产品
   - `POST /api/my-products/<id>/edit` - 编辑产品信息
   - `PUT /api/my-products/<id>/inventory` - 更新库存
   - `GET /api/my-orders` - 自己收到的采购订单
   - `POST /api/my-orders/<id>/update-status` - 更新订单状态（确认/发货）
   - `GET /api/my-sales-stats` - 销售统计与财务数据

5. 优化登录接口
   - `/login` POST 端点添加 `identity` 参数（'admin' 或 'supplier'）
   - 验证用户名/密码后，额外验证用户的角色是否与选中的身份匹配
   - 响应中添加 `role`, `supplier_id`, `supplier_name` 字段

6. 为所有 API 端点添加输入验证
   - 使用 Marshmallow 或简单的 JSON Schema 验证

7. 记录操作审计日志
   - 关键操作（创建订单、更新库存、改订单状态）记录到 system_logs 表

**产出**:

- 修改 [app.py](app.py) - 新增 5 个 ORM 模型、3 个装饰器、15+ 个 API 端点
- 新建 `validators.py` - 数据验证工具

---

## [ ] 任务7：登录页面优化与身份选择

**描述**: 为登录页面添加身份选择功能（管理员/供应商），并优化页面交互

**要求**:

1. 修改 [templates/login.html](templates/login.html)
   - 在登录表单上方添加身份选择模块
     - Radio 按钮组：选项 1 (管理员) 和选项 2 (供应商)
     - 默认选中"管理员"
   - 表单包含: 用户名、密码、身份选择、登录按钮、记住我(可选)
   - 样式: 沿用现有深色主题，使用 Bootstrap 4.6
   - 添加身份切换时的视觉反馈

2. 修改登录表单提交逻辑
   - 通过 hidden input 字段将选中的 identity 值传到后端 `/login`
   - 后端验证: 该用户名是否存在、密码是否正确、用户角色是否与选中的身份匹配
   - 失败时返回明确的错误消息

3. 登录成功后
   - 前端从响应中读取 `role` 和 `supplier_name`
   - 管理员重定向到 `/dashboard`（渔场管理员仪表板）
   - 供应商重定向到 `/supplier-dashboard`（商家仪表板）

**产出**:

- 修改 [templates/login.html](templates/login.html)
- 修改 [static/js/main.js](static/js/main.js) - 增强登录表单提交逻辑

---

## [ ] 任务8：商家专属平台页面创建

**描述**: 为供应商创建完整的管理平台，包括仪表板、产品管理、订单管理、财务统计

**要求**:

1. 创建商家仪表板页面 [templates/supplier-dashboard.html](templates/supplier-dashboard.html) (新建)
   - 顶部 KPI 卡片: 本月销售额、待确认订单数、库存预警、应收款
   - 最近订单表格（采购方、产品、数量、订单状态、操作按钮）
   - 销售趋势图表（过去 30 天）
   - 快速操作区: 查看产品库、更新库存按钮

2. 创建商家产品管理页面 [templates/supplier-products.html](templates/supplier-products.html) (新建)
   - 产品表格: 产品名、物种、等级、库存、单价、成本、操作按钮
   - 功能按钮: 新增产品、编辑、删除、上传图片、管理库存
   - 搜索和筛选（按物种、等级）
   - 产品编辑模态框: 包含所有字段（名称、物种、等级、单价、成本、生长周期、存活率、描述、图片）

3. 创建商家订单管理页面 [templates/supplier-orders.html](templates/supplier-orders.html) (新建)
   - 订单表格: 订单号、采购方鱼塘、产品、数量、单价、订单状态、下单日期、操作
   - 状态筛选: 草稿/已确认/已发货/已收货/已对账
   - 操作按钮: 查看详情、确认订单、标记发货、生成发货单
   - 订单详情模态框: 显示完整订单信息、项目列表、时间线

4. 创建商家财务统计页面 [templates/supplier-stats.html](templates/supplier-stats.html) (新建)
   - 统计指标卡: 本月销售额、本月订单数、平均客单价、应收款总额
   - 图表 1: 月度销售额趋势（线图）
   - 图表 2: 产品销售分布（饼图）
   - 财务表格: 本月交易明细、金额、订单状态、操作
   - 日期范围选择器（支持自定义查询）

5. 修改 [templates/base.html](templates/base.html)
   - 导航栏右侧添加当前身份显示 (🏢 "管理员" 或 🐟 "供应商: XXX")
   - 侧边栏菜单根据 role 动态显示（商家仅显示: 仪表板、产品管理、订单管理、财务统计）
   - 添加身份切换/登出菜单

6. 所有新页面使用现有的深色主题、Bootstrap 4.6、Font Awesome 6.0

**产出**:

- 新建 [templates/supplier-dashboard.html](templates/supplier-dashboard.html)
- 新建 [templates/supplier-products.html](templates/supplier-products.html)
- 新建 [templates/supplier-orders.html](templates/supplier-orders.html)
- 新建 [templates/supplier-stats.html](templates/supplier-stats.html)
- 修改 [templates/base.html](templates/base.html)

---

## [ ] 任务9：管理员供应商管理页面创建

**描述**: 为管理员创建鱼苗采购管理页面，包括供应商管理和采购订单跟踪

**要求**:

1. 创建鱼苗管理页面 [templates/seedling-management.html](templates/seedling-management.html) (新建)
   - 上方两个 Tab 按钮：供应商管理 / 采购管理
2. Tab 1: 供应商管理
   - 供应商卡片网格（类似设备卡片风格）
     - 卡片显示: 供应商名称、联系人、电话、邮箱、状态(活跃/停用)、操作按钮
   - 搜索和筛选（按名称、状态）
   - 操作按钮: 新增供应商、编辑、删除、查看历史订单、查看产品库
   - 新增/编辑供应商模态框: 名称、联系人、电话、邮箱、地址、备注
   - 供应商详情侧面板: 显示该供应商的统计信息（已供应产品数、总销售额、最近订单）

3. Tab 2: 采购管理
   - 采购订单表格（分页、排序、筛选）
     - 列: 订单号、供应商、采购鱼塘、产品及数量、订单金额、订单状态、下单日期、更新日期、操作
   - 高级筛选: 按供应商、状态、日期范围、金额范围
   - 操作按钮: 新建采购单、查看详情、编辑、取消
   - 新建采购单表单: 选择供应商 → 显示供应商产品列表 → 选择产品 → 填写数量 → 设置交货期 → 提交
   - 订单详情模态框: 完整订单信息、时间线(草稿 → 已确认 → 已发货 → 已收货 → 已对账)、项目列表

4. 修改 [templates/base.html](templates/base.html) 侧边栏
   - 在现有菜单下添加新项: 📦 鱼苗管理 → `/seedling-management`
   - 仅对 admin 角色显示此菜单

5. 页面样式沿用现有深色主题、导航栏、侧边栏结构

**产出**:

- 新建 [templates/seedling-management.html](templates/seedling-management.html)
- 修改 [templates/base.html](templates/base.html) - 添加菜单项

---

## [ ] 任务10：前端路由、权限隔离与集成测试

**描述**: 实现前端路由、权限检查、菜单动态渲染，以及完整的集成测试

**要求**:

1. 在 [app.py](app.py) 中添加新路由（HTML 页面）
   - `GET /supplier-dashboard` - 商家仪表板 [@login_required]
   - `GET /supplier-products` - 商家产品管理 [@login_required, @role_required(['supplier'])]
   - `GET /supplier-orders` - 商家订单管理 [@login_required, @role_required(['supplier'])]
   - `GET /supplier-stats` - 商家财务统计 [@login_required, @role_required(['supplier'])]
   - `GET /seedling-management` - 管理员鱼苗管理 [@login_required, @role_required(['admin'])]
   - 所有路由返回 render_template()，将当前用户信息(role, supplier_name)传入

2. 前端权限隐藏逻辑 [static/js/main.js](static/js/main.js)
   - 页面加载时调用 `/api/current-user` 获取当前用户信息
   - 根据 role 动态显示/隐藏菜单项和功能按钮
   - 若用户尝试访问无权限页面，跳转回对应的仪表板并显示错误提示

3. 修改 [templates/base.html](templates/base.html)
   - 侧边栏菜单添加条件渲染 (Jinja2 if 语句)
     - 仅 admin 显示: 鱼苗管理、系统设置
     - 仅 supplier 显示: 产品管理、订单管理、财务统计
     - 都显示: 仪表板
   - 顶部右侧显示身份和供应商名称
   - 菜单中添加身份切换选项（实际是登出并重新登录选择不同身份）

4. 集成测试清单 (在 README 或 TESTING.md 中记录)
   - [ ] 管理员身份登录 → 进入管理员仪表板 ✅
   - [ ] 商家身份登录 → 进入商家仪表板 ✅
   - [ ] 管理员访问供应商管理页面 → 成功加载 ✅
   - [ ] 管理员创建采购订单 → 订单入库 ✅
   - [ ] 商家收到采购订单 → 在订单管理页可见 ✅
   - [ ] 商家更新订单状态(确认/发货) → 管理员侧同步更新 ✅
   - [ ] 商家仅能看到自己的产品和订单 ✅
   - [ ] 商家访问其他供应商数据 → 403 Forbidden ✅
   - [ ] 商家访问管理员页面 → 重定向并提示权限不足 ✅
   - [ ] 财务统计图表正常渲染 ✅

5. 性能优化
   - API 接口支持分页（page, per_page 参数）
   - 列表页面添加懒加载或虚拟滚动（if 数据超过 1000 条）
   - 为关键查询添加缓存（如供应商列表缓存 1 分钟）

6. 错误处理与用户提示
   - API 返回错误时，前端显示友好的 Toast 通知
   - 权限被拒绝时，显示 "您没有权限访问此资源，请联系管理员"
   - 网络错误时，显示重试按钮

**产出**:

- 修改 [app.py](app.py) - 添加 6 个新路由
- 修改 [static/js/main.js](static/js/main.js) - 权限检查和菜单渲染逻辑
- 修改 [templates/base.html](templates/base.html) - 条件菜单渲染
- 新建 `TESTING.md` - 集成测试文档

---

## [ ] 任务11：数据初始化与种子数据更新

**描述**: 为新的表结构准备种子数据，初始化测试用的供应商、产品、订单数据

**要求**:

1. 修改 [seed_data.py](seed_data.py)
   - 添加 `add_suppliers()` 函数 - 创建 3-5 个测试供应商（如"清源鱼苗场"、"锦鲤养殖基地"）
   - 添加 `add_seedling_products()` 函数 - 为每个供应商添加 5-8 种鱼苗产品（草鱼、鲈鱼、鲤鱼等）
   - 添加 `add_seedling_inventory()` 函数 - 为每个产品初始化库存（1000-5000尾）
   - 添加 `add_sample_users()` 函数 - 创建测试用户
     - admin/admin123 (角色: admin, supplier_id: NULL)
     - supplier1/supplier123 (角色: supplier, supplier_id: 1)
     - supplier2/supplier123 (角色: supplier, supplier_id: 2)
   - 添加 `add_sample_purchase_orders()` 函数 - 创建 10-20 个示例采购订单（含各种状态）

2. 修改 [seed_data.py](seed_data.py) 中的 `main()` 函数
   - 调用所有新增函数，创建完整的测试数据环境
   - 打印数据创建摘要（创建的供应商数、产品数、订单数等）

3. 在 `README.md` 中添加说明
   - 如何运行种子数据脚本
   - 测试账户列表和密码
   - 测试数据简要说明

**产出**:

- 修改 [seed_data.py](seed_data.py)
- 修改 [README.md](README.md)

---

## [ ] 任务12：文档更新与项目完成

**描述**: 编写 API 文档、系统架构文档、更新项目 README，标志项目功能完成

**要求**:

1. 创建 API 文档 [docs/API.md](docs/API.md) (新建)
   - 分为三部分: 认证、管理员 API、商家 API
   - 每个端点包含: 方法、路径、描述、参数、请求示例、响应示例、权限要求、错误码
   - 包含所有 15+ 个新 API 端点

2. 创建系统架构文档 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (新建)
   - 高层架构图（Mermaid 图表）: 前端 → Flask 后端 → 数据库
   - 数据库 ER 图（Mermaid）: 表之间的关系
   - 权限模型说明: RBAC、装饰器设计、数据隔离策略
   - 业务流程说明: 订单生命周期、库存管理流程

3. 创建集成测试文档 [docs/TESTING.md](docs/TESTING.md) (新建)
   - 测试清单（checkbox list）
   - 测试环境准备说明
   - 手动测试步骤（逐一验证功能）
   - 自动化测试建议

4. 更新 [README.md](README.md)
   - 添加 "多身份系统" 章节，说明管理员和商家的不同功能
   - 添加快速开始指南: 如何以不同身份登录
   - 更新项目特性列表
   - 链接到详细文档（API.md、ARCHITECTURE.md、TESTING.md）

5. 更新 [智慧渔场管理系统\_可行性分析与系统设计文档.md](智慧渔场管理系统_可行性分析与系统设计文档.md)
   - 新增 "供应链管理模块" 章节
   - 说明商家平台的功能和价值

6. 生成项目完成总结
   - 统计实现功能数、代码行数、新增表数等
   - 列出后续优化方向（缓存、实时推送、高级报表等）

**产出**:

- 新建 [docs/API.md](docs/API.md)
- 新建 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 新建 [docs/TESTING.md](docs/TESTING.md)
- 修改 [README.md](README.md)
- 修改 [智慧渔场管理系统\_可行性分析与系统设计文档.md](智慧渔场管理系统_可行性分析与系统设计文档.md)

---

<!--
📝 说明:

1. 本任务清单共 8 个任务（任务 5-12），建议按顺序完成
2. 任务 5 是基础（数据库），任务 6-9 是核心功能，任务 10-12 是测试和文档
3. 每个任务完成后会自动标记为 [x]，可随时查看进度
4. 遇到问题可在任务下方添加 **问题说明** 和 **解决方案** 来记录

💡 预计时间: 3-5 天（取决于并行工作方式）
   - 任务 5-6 可并行（2 天）
   - 任务 7-9 可并行（1.5-2 天）
   - 任务 10-12 顺序（1 天）

-->
