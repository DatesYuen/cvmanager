# CV Manager

`CV Manager` 是一个面向高校/科研场景的学术简历管理系统，用于上传和解析 `DOCX` 简历，将论文、项目、专利、软著、获奖等内容抽取为结构化数据，并提供人员管理、用户权限、审核、附件管理、导出等能力。

当前项目采用前后端分离架构：

- 后端：`FastAPI + SQLAlchemy + SQLite`
- 前端：`Vue 3 + Vite + Element Plus + Pinia`

## 主要功能

当前版本已经实现或预留了以下能力：

- 用户登录与认证，支持管理员和普通用户
- 用户管理：管理员可新增、编辑、禁用用户
- 人员管理：新增、编辑、删除人员档案
- 简历上传：上传 `DOCX` 简历并自动解析
- 简历历史：保留历史版本并支持下载
- 内容抽取：支持论文、项目、专利、软著、指导学生获奖、会议、特刊、学术兼职、学术报告、教学平台、行业标准等类别
- 差异化更新：重新上传简历时，基于文本相似度对已有条目进行匹配与更新
- 审核流程：支持待审核列表、手动审核、按置信度批量通过
- 附件管理：条目级附件上传、下载、删除
- 数据导出：支持按条件筛选并导出 `JSON` / `Excel`
- AI 接口预留：为低置信度抽取、简历分析、表单填写保留接口
- 外部补全接口预留：为论文、专利信息补全保留接口

## 项目结构

```text
cvmanager/
├── backend/                  # FastAPI 后端
│   ├── main.py               # 应用入口
│   ├── models/               # 数据模型
│   ├── routers/              # API 路由
│   ├── parsers/              # DOCX 读取、章节拆分、内容提取、差异比对
│   ├── services/             # 业务逻辑
│   └── uploads/              # 简历和附件存储目录
├── frontend/                 # Vue 3 前端
├── prompt.md                 # 原始需求说明
├── plans.md                  # 实施计划
├── requirements.txt          # 后端依赖
└── 庞善臣简介(20260412).docx # 测试样例简历
```

## 运行环境

建议环境：

- Python `3.10+`
- Node.js `18+`
- npm `9+`

## 快速启动

### 1. 启动后端

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

后端默认地址：

- API 服务：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`

说明：

- 首次启动会自动创建 SQLite 数据库 `cvmanager.db`
- 首次启动会自动创建默认管理员账号
- 上传文件会存储到 `backend/uploads/`

### 2. 启动前端

打开第二个终端，进入 `frontend` 目录：

```powershell
cd frontend
npm install
npm run dev
```

前端默认地址：

- `http://127.0.0.1:3000`

前端开发服务器已配置代理：

- `/api` -> `http://127.0.0.1:8000`

## 默认账号

系统启动后会自动创建管理员账号：

- 用户名：`admin`
- 密码：`admin123`

建议首次登录后立即修改密码。

## 使用流程

推荐按下面顺序体验系统：

1. 使用管理员账号登录前端
2. 进入“人员管理”新增一个人员
3. 进入该人员详情页，点击“上传简历”
4. 上传根目录中的测试文件 `庞善臣简介(20260412).docx`
5. 查看系统解析出的论文、项目、专利等结构化数据
6. 进入“审核页面”处理待审核条目
7. 进入“导出页面”按条件筛选并导出数据

## 数据与存储说明

- 数据库：`cvmanager.db`
- 简历文件目录：`backend/uploads/resumes/`
- 附件目录：`backend/uploads/attachments/`

当前数据库默认使用 SQLite，适合本地开发和原型验证。如果后续需要多用户正式部署，可切换到 MySQL 或 PostgreSQL。

## 关键接口

常用接口示例：

- 登录：`POST /api/auth/login`
- 当前用户：`GET /api/auth/me`
- 人员管理：`/api/persons`
- 简历上传：`POST /api/resumes/upload/{person_id}`
- 简历历史：`GET /api/resumes/{person_id}/history`
- 审核：`/api/reviews/*`
- 附件：`/api/attachments/*`
- 导出：`POST /api/export/items`
- AI 预留接口：`/api/ai/*`
- 外部补全预留接口：`/api/external/*`

## 当前状态

目前项目已经具备可运行的原型能力，适合继续开发和联调。尤其是以下主链路已经打通：

- 登录
- 用户管理
- 人员管理
- 简历上传
- 内容解析
- 审核
- 附件管理
- 数据导出

## 已知限制

当前版本仍有一些属于“预留”或“待继续优化”的部分：

- AI 能力接口已定义，但尚未接入真实模型服务
- 外部论文/专利补全接口已定义，但尚未接入第三方平台
- 简历解析目前主要依赖规则和正则，复杂格式下仍需继续优化
- 数据库迁移工具依赖已加入，但当前主要通过 `Base.metadata.create_all()` 自动建表
- 前端尚未补充生产部署说明与构建产物发布流程

## 常见问题

### 1. 前端启动时报 `vite is not recognized`

这是因为前端依赖尚未安装。先执行：

```powershell
cd frontend
npm install
```

再执行：

```powershell
npm run dev
```

### 2. 登录失败怎么办

先确认后端已经启动，并且数据库初始化完成。默认管理员账号是：

- `admin / admin123`

如果数据库中已有旧数据，也可以直接删除根目录下的 `cvmanager.db` 后重新启动后端进行初始化。

### 3. 上传后没有解析出理想结果

当前解析逻辑基于章节识别、规则匹配和多种提取器组合，对格式规整的学术简历效果较好。若简历格式变化较大，可能需要继续补充对应类别的提取规则。

## 后续开发建议

如果准备继续扩展本项目，建议优先推进：

- 接入真实 AI 服务处理低置信度条目
- 接入 CrossRef / 专利查询等外部数据源
- 完善更多类别的解析准确率
- 增加测试用例与端到端联调脚本
- 增加生产环境部署方案

## 参考文档

- 需求说明：[prompt.md](./prompt.md)
- 实施计划：[plans.md](./plans.md)

