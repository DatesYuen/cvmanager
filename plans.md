# CV Manager - 学术简历管理系统 实施计划

## Context

需要从零构建一个学术简历管理系统，支持上传DOCX格式简历并自动解析提取结构化信息（论文、项目、专利、软著等13个类别），支持差异化更新、用户权限管理、审核流程、AI Agent接口、附件管理等功能。项目根目录当前仅有一个示例DOCX简历文件。

## 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 后端框架 | **FastAPI** | 异步、自动OpenAPI文档、适合REST API |
| 前端框架 | **Vue 3 + Element Plus** | 现代UI、表格/表单组件丰富、中文支持好 |
| 数据库 | **SQLite + SQLAlchemy** | 部署简单、ORM支持迁移 |
| 数据库迁移 | **Alembic** | SQLAlchemy标准迁移工具 |
| DOCX解析 | **python-docx** | 成熟稳定的Word文档解析库 |
| 认证 | **JWT (python-jose + passlib)** | 无状态认证、前后端分离 |
| 前端构建 | **Vite** | 快速开发服务器和构建 |

## 项目结构

```
cvmanager/
├── backend/
│   ├── main.py                  # FastAPI入口、CORS配置
│   ├── config.py                # 配置管理
│   ├── database.py              # 数据库连接和会话
│   ├── models/                  # SQLAlchemy模型
│   │   ├── __init__.py
│   │   ├── user.py              # 用户模型(User)
│   │   ├── person.py            # 人员模型(Person)
│   │   ├── resume.py            # 简历版本模型(Resume)
│   │   ├── profile.py           # 个人简介(Profile, Education, WorkExperience)
│   │   ├── paper.py             # 论文(Paper, PaperAuthor)
│   │   ├── project.py           # 项目(Project)
│   │   ├── award.py             # 获奖(Award)
│   │   ├── patent.py            # 专利(Patent)
│   │   ├── software_copyright.py # 软著(SoftwareCopyright)
│   │   ├── student_award.py     # 指导学生获奖(StudentAward)
│   │   ├── conference.py        # 承办会议(Conference)
│   │   ├── special_issue.py     # 承办特刊(SpecialIssue)
│   │   ├── academic_role.py     # 学术兼职(AcademicRole)
│   │   ├── academic_report.py   # 学术报告(AcademicReport)
│   │   ├── teaching_platform.py # 教学平台建设(TeachingPlatform)
│   │   ├── industry_standard.py # 行业标准(IndustryStandard)
│   │   ├── attachment.py        # 附件(Attachment)
│   │   └── review.py            # 审核记录(ReviewRecord)
│   ├── schemas/                 # Pydantic schemas (请求/响应)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── person.py
│   │   ├── paper.py
│   │   ├── project.py
│   │   ├── ... (每个实体对应schema)
│   │   └── review.py
│   ├── routers/                 # API路由
│   │   ├── __init__.py
│   │   ├── auth.py              # 登录、token刷新
│   │   ├── users.py             # 用户CRUD(管理员)
│   │   ├── persons.py           # 人员CRUD
│   │   ├── resumes.py           # 简历上传/下载/历史
│   │   ├── papers.py            # 论文CRUD + 筛选
│   │   ├── projects.py          # 项目CRUD + 筛选
│   │   ├── patents.py           # 专利CRUD + 筛选
│   │   ├── ... (每个实体对应router)
│   │   ├── attachments.py       # 附件上传/下载
│   │   ├── reviews.py           # 审核管理
│   │   ├── export.py            # 导出功能
│   │   └── ai_agent.py          # AI Agent接口
│   ├── parsers/                 # 简历解析模块
│   │   ├── __init__.py
│   │   ├── docx_reader.py       # DOCX文件读取，提取段落和表格
│   │   ├── section_splitter.py  # 按标题关键词拆分简历章节
│   │   ├── extractors/          # 各类内容提取器
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # 提取器基类(含置信度计算)
│   │   │   ├── profile.py       # 个人简介提取
│   │   │   ├── paper.py         # 论文提取(多格式正则)
│   │   │   ├── project.py       # 项目提取
│   │   │   ├── patent.py        # 专利提取
│   │   │   ├── software_copyright.py # 软著提取
│   │   │   ├── award.py         # 获奖提取
│   │   │   ├── student_award.py
│   │   │   ├── conference.py
│   │   │   ├── special_issue.py
│   │   │   ├── academic_role.py
│   │   │   ├── academic_report.py
│   │   │   ├── teaching_platform.py
│   │   │   └── industry_standard.py
│   │   └── diff_engine.py       # 简历差异对比引擎
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth_service.py      # 认证逻辑
│   │   ├── resume_service.py    # 简历上传/解析/差异处理
│   │   ├── review_service.py    # 审核流程
│   │   ├── export_service.py    # 导出逻辑
│   │   └── ai_agent_service.py  # AI Agent服务(预留)
│   ├── external/                # 外部接口(预留)
│   │   ├── __init__.py
│   │   ├── paper_api.py         # 论文信息补全接口(CrossRef/CNKI)
│   │   ├── patent_api.py        # 专利信息获取接口
│   │   └── base.py              # 外部API基类
│   ├── alembic/                 # 数据库迁移
│   │   └── ...
│   └── uploads/                 # 文件存储目录
│       ├── resumes/             # 简历文件
│       └── attachments/         # 附件文件
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.js         # Vue Router配置
│   │   ├── stores/              # Pinia状态管理
│   │   │   ├── auth.js
│   │   │   └── app.js
│   │   ├── api/                 # API调用封装
│   │   │   ├── index.js         # axios实例(含token拦截器)
│   │   │   ├── auth.js
│   │   │   ├── persons.js
│   │   │   ├── resumes.js
│   │   │   ├── papers.js
│   │   │   └── ...
│   │   ├── views/
│   │   │   ├── Login.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── PersonList.vue       # 人员列表
│   │   │   ├── PersonDetail.vue     # 人员详情(含所有简历数据tab)
│   │   │   ├── ResumeUpload.vue     # 简历上传+解析结果
│   │   │   ├── ReviewPage.vue       # 审核页面
│   │   │   ├── UserManagement.vue   # 用户管理(管理员)
│   │   │   └── ExportPage.vue       # 导出+筛选页面
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppLayout.vue    # 主布局(侧边栏+顶栏)
│   │   │   │   └── Sidebar.vue
│   │   │   ├── tables/
│   │   │   │   ├── PaperTable.vue
│   │   │   │   ├── ProjectTable.vue
│   │   │   │   ├── PatentTable.vue
│   │   │   │   └── ... (每类数据对应表格组件)
│   │   │   ├── ReviewTable.vue      # 审核表格(含通过/拒绝按钮)
│   │   │   ├── FilterPanel.vue      # 动态筛选条件面板
│   │   │   ├── AttachmentManager.vue # 附件管理组件
│   │   │   └── ConfidenceBadge.vue  # 置信度标签
│   │   └── styles/
│   │       └── global.css
│   └── public/
├── requirements.txt
├── alembic.ini
└── README.md
```

## 实施步骤

### 阶段1：后端基础架构 (数据库 + 认证)

**1.1 项目初始化**
- 创建 `requirements.txt`：fastapi, uvicorn, sqlalchemy, alembic, python-docx, python-jose, passlib, python-multipart, aiofiles
- 创建 `backend/config.py`：数据库路径、JWT密钥、上传路径等配置
- 创建 `backend/database.py`：SQLAlchemy引擎和会话工厂

**1.2 数据库模型** (`backend/models/`)
- **User**: id, username, password_hash, role(admin/user), permissions(JSON), is_active, created_at
- **Person**: id, name, created_by, created_at, updated_at
- **Resume**: id, person_id(FK), file_path, original_filename, version, uploaded_by, uploaded_at (保留历史版本)
- **Profile**: id, person_id(FK), introduction(text), phone, email, address
- **Education**: id, person_id(FK), start_date, end_date, school, major, degree
- **WorkExperience**: id, person_id(FK), start_date, end_date, organization, position
- **Paper**: id, person_id(FK), title, journal, year, doi, issue, volume, pages, raw_text, confidence, review_status
- **PaperAuthor**: id, paper_id(FK), name, order, is_first_author, is_corresponding_author
- **Project**: id, person_id(FK), project_type, name, project_number, start_date, end_date, role, amount, raw_text, confidence, review_status
- **Award**: id, person_id(FK), award_name, project_name, participants(text), awarding_body, raw_text, confidence, review_status
- **Patent**: id, person_id(FK), patent_name, patent_number, status, raw_text, confidence, review_status
- **PatentApplicant**: id, patent_id(FK), name, order
- **SoftwareCopyright**: id, person_id(FK), applicant, name, registration_date, registration_number, raw_text, confidence, review_status
- **StudentAward**: id, person_id(FK), award_name, level, role, award_date, raw_text, confidence, review_status
- **Conference**: id, person_id(FK), name, date, role, website, raw_text, confidence, review_status
- **SpecialIssue**: id, person_id(FK), issue_name, journal_name, date, role, raw_text, confidence, review_status
- **AcademicRole**: id, person_id(FK), title, start_date, end_date, raw_text, confidence, review_status
- **AcademicReport**: id, person_id(FK), name, report_type, date, raw_text, confidence, review_status
- **TeachingPlatform**: id, person_id(FK), name, issuing_body, approval_date, position, raw_text, confidence, review_status
- **IndustryStandard**: id, person_id(FK), name, publish_date, role, raw_text, confidence, review_status
- **Attachment**: id, entity_type, entity_id, file_path, original_filename, uploaded_by, uploaded_at
- **ReviewRecord**: id, entity_type, entity_id, person_id, action(approve/reject), reviewer_id, comment, reviewed_at

每个内容实体都包含: `raw_text`(原始文本), `confidence`(提取置信度0-1), `review_status`(pending/approved/rejected)

**1.3 认证系统**
- `backend/services/auth_service.py`：密码hash(bcrypt)、JWT生成/验证
- `backend/routers/auth.py`：POST /api/auth/login, POST /api/auth/refresh
- 初始化创建默认admin账户(admin/admin123)

**1.4 用户管理API**
- `backend/routers/users.py`：CRUD接口，仅admin可访问
- 权限字段为JSON，支持细粒度控制：`{"can_create_person": true, "can_delete_person": false, ...}`

### 阶段2：简历解析引擎

**2.1 DOCX读取器** (`backend/parsers/docx_reader.py`)
- 使用python-docx提取所有段落文本和表格内容
- 保留段落样式信息（标题级别、粗体等）用于章节识别

**2.2 章节拆分器** (`backend/parsers/section_splitter.py`)
- 定义章节关键词映射：
  ```python
  SECTION_KEYWORDS = {
      "profile": ["个人简介", "基本信息", "个人信息", "简介"],
      "paper": ["论文", "发表论文", "学术论文", "期刊论文", "发表的论文"],
      "project": ["项目", "科研项目", "主持项目", "参与项目", "课题"],
      "award": ["获奖", "奖励", "科研获奖", "荣誉"],
      "patent": ["专利", "发明专利", "实用新型"],
      "software_copyright": ["软著", "软件著作", "计算机软件著作"],
      "student_award": ["指导学生", "学生获奖", "指导研究生"],
      "conference": ["会议", "学术会议", "承办会议"],
      "special_issue": ["特刊", "专刊"],
      "academic_role": ["学术兼职", "兼职", "社会兼职"],
      "academic_report": ["学术报告", "报告", "特邀报告"],
      "teaching_platform": ["平台", "教学平台", "学科建设"],
      "industry_standard": ["标准", "行业标准"],
  }
  ```
- 基于标题样式和关键词匹配拆分段落到对应章节

**2.3 内容提取器** (`backend/parsers/extractors/`)

每个提取器继承 `BaseExtractor`：
```python
class BaseExtractor:
    def extract(self, text: str) -> list[dict]:
        """返回提取结果列表，每个结果包含字段值和置信度"""
    def calculate_confidence(self, result: dict) -> float:
        """根据匹配到的字段数量/质量计算置信度"""
```

**论文提取器** (核心难点，需支持多种格式)：
- 策略：按行拆分 → 对每行尝试多个正则模式 → 取最高置信度结果
- 模式1 (英文期刊): `作者列表. 标题. 期刊名. 年, 卷(期):页. DOI`
- 模式2 (中文期刊): `作者列表. 标题. 期刊名, 年, 卷(期): 页.`
- 模式3 (会议): `作者列表. 标题. 会议名, 出版社:年,页.`
- 通讯作者识别：名字后有`*`
- 置信度计算：匹配到标题+期刊=0.6基础分，每多匹配一个字段+0.05-0.1

**项目提取器**：
- 识别模式：`类型：名称（编号）\n日期范围，身份（金额）`
- 支持跨行匹配（项目信息可能跨2-3行）
- 金额提取：正则匹配`(\d+万元?)`

**专利提取器**：
- 模式：`申请人列表，专利名称，申请号：CN..., 状态`
- 申请号正则：`CN\d{10,}\.?\d*`

**软著提取器**：
- 模式：`申请人.名称(版本)日期，登记号：...`

**其他提取器**类似，根据各自格式编写正则。

**2.4 置信度计算规则**
- 必填字段匹配: 每个+0.2-0.3
- 可选字段匹配: 每个+0.05-0.1
- 格式规范性加分: 日期格式正确+0.05, 编号格式正确+0.05
- 总分归一化到[0, 1]

### 阶段3：差异对比引擎

**3.1 差异引擎** (`backend/parsers/diff_engine.py`)
- 对比维度：以 `raw_text` 做文本相似度(SequenceMatcher)
- 同类型条目两两比对，相似度>0.8视为同一条目
- 新增条目：新简历中有但旧简历中无 → 标记为pending review
- 修改条目：匹配到但有差异 → 更新字段，保留review_status
- 删除条目：旧简历中有但新简历中无 → 不自动删除，标记提示用户

### 阶段4：API路由层

**4.1 简历上传与解析**
- `POST /api/resumes/upload/{person_id}` → 上传DOCX，存储文件，触发解析
- `GET /api/resumes/{person_id}/history` → 获取历史简历列表
- `GET /api/resumes/{resume_id}/download` → 下载历史DOCX
- 解析流程：读取DOCX → 拆分章节 → 各提取器提取 → 差异对比 → 写入数据库

**4.2 各实体CRUD**
- 每个实体类型一套标准CRUD：GET列表(含分页/筛选), GET详情, POST创建, PUT更新, DELETE删除
- 筛选接口支持动态条件：`GET /api/papers?year=2022&journal=xxx&author=xxx`
- 筛选条件从数据库表列动态生成

**4.3 审核接口**
- `GET /api/reviews/pending/{person_id}` → 获取待审核条目
- `POST /api/reviews/approve` → 通过审核(支持批量)
- `POST /api/reviews/reject` → 拒绝
- `POST /api/reviews/batch-approve?confidence_threshold=0.8` → 一键审批高置信度条目

**4.4 附件接口**
- `POST /api/attachments/upload` → 上传附件(entity_type + entity_id)
- `GET /api/attachments/{id}/download` → 下载
- `GET /api/attachments?entity_type=paper&entity_id=1` → 查看某条目附件

**4.5 AI Agent接口** (预留)
- `POST /api/ai/extract` → AI提取低置信度条目
- `POST /api/ai/analyze` → AI分析简历
- `POST /api/ai/fill-form` → AI填写表格
- 接口定义好输入输出格式，内部实现为TODO占位

**4.6 外部数据接口** (预留)
- `POST /api/external/paper-lookup` → 论文信息补全(CrossRef API)
- `POST /api/external/patent-lookup` → 专利信息查询
- 接口定义好，内部实现为TODO占位

**4.7 导出接口**
- `POST /api/export/items` → 根据筛选条件导出(JSON/Excel格式)

### 阶段5：前端实现

**5.1 项目搭建**
- Vue 3 + Vite + Element Plus + Vue Router + Pinia + Axios
- 配置API代理到后端8000端口

**5.2 布局与路由**
- 登录页 → 主布局(左侧菜单+顶栏用户信息+主内容区)
- 路由：/login, /dashboard, /persons, /persons/:id, /upload/:person_id, /reviews, /users, /export

**5.3 核心页面**
- **Dashboard**: 统计卡片(人员数、待审核数、论文数等) + 最近上传记录
- **PersonList**: 人员列表表格 + 新增/搜索 + 操作列(查看/编辑/删除)
- **PersonDetail**: 顶部个人信息卡片 + Tabs切换(论文/项目/专利/...每类一个Tab)
  - 每个Tab内是可编辑表格，支持行内编辑、删除、添加
  - 每行有置信度标签(颜色编码：绿>0.8, 黄0.5-0.8, 红<0.5)
  - 每行有附件按钮(上传/查看附件)
- **ResumeUpload**: 文件拖拽上传区 + 解析进度 + 差异对比结果预览
- **ReviewPage**: 待审核条目表格，含通过/拒绝按钮，顶部一键审批按钮+置信度阈值滑块
- **UserManagement**: 用户CRUD表格(仅管理员可见)
- **ExportPage**: 选择数据类型 → 动态筛选面板 → 预览 → 导出

**5.4 UI设计要点**
- Element Plus暗色/亮色主题切换
- 卡片式布局，圆角阴影
- 表格使用斑马纹、固定表头
- 响应式布局适配不同屏幕

### 阶段6：集成测试与完善

- 使用示例DOCX(`庞善臣简介(20260412).docx`)进行端到端测试
- 验证各提取器准确性，调优正则和置信度阈值
- 验证差异对比功能(修改docx内容后重新上传)
- 验证审核流程
- 验证附件上传下载

## 关键文件清单

| 文件 | 作用 |
|------|------|
| `backend/main.py` | FastAPI应用入口 |
| `backend/models/*.py` | 全部数据模型(约17个文件) |
| `backend/parsers/section_splitter.py` | 简历章节拆分 |
| `backend/parsers/extractors/paper.py` | 论文提取器(最复杂) |
| `backend/parsers/diff_engine.py` | 差异对比引擎 |
| `backend/routers/resumes.py` | 简历上传解析API |
| `backend/routers/reviews.py` | 审核API |
| `backend/routers/ai_agent.py` | AI Agent预留接口 |
| `frontend/src/views/PersonDetail.vue` | 人员详情页(最复杂) |
| `frontend/src/views/ReviewPage.vue` | 审核页面 |

## 验证方式

1. 启动后端 `uvicorn backend.main:app --reload`
2. 启动前端 `cd frontend && npm run dev`
3. 访问前端登录(admin/admin123)
4. 上传示例DOCX `庞善臣简介(20260412).docx`
5. 验证解析结果：各章节是否正确拆分，论文/项目/专利等字段是否正确提取
6. 验证审核流程：查看待审核列表，一键审批高置信度条目，手动审批低置信度条目
7. 修改DOCX内容后重新上传，验证差异对比：仅新增/修改的条目需要审核
8. 测试附件上传/下载
9. 测试导出功能
10. 测试用户管理(新增普通用户，设置权限)
