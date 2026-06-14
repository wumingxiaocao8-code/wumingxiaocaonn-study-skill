# Bloom 2 Sigma Learning Tutor

一个面向深度学习和长期复习的 AI 学习 Skill 框架。它把 Bloom 掌握学习理论改造成可执行的对话流程，让 AI 不只是回答问题，而是像一对一导师一样帮助你拆分材料、诊断理解、教学、追问、测验、纠错、复习和记录。

这个仓库保存的是框架本身，不包含个人学习记录。你可以把它安装到 Claude Code、Codex 或其他支持 Skill 目录结构的本地 Agent 环境中，用来精读一本书、学习陌生领域、做专题深挖、复习旧知识，或学习 Python/量化代码。

## 适合什么场景

- 系统学习一本书，而不是只让 AI 总结章节。
- 继续上次学习进度，让 AI 读取状态并恢复到中断位置。
- 按模块推进学习，未达到目标掌握度前不跳到下一模块。
- 通过苏格拉底式追问、测试和纠错检查自己是否真的理解。
- 自动维护错题本、复习队列、概念图和学习会话记录。
- 对经济学、政治经济学、历史、陌生领域研究、Python 和量化代码做结构化学习。

## 核心流程

学习模式使用一个固定循环：

```text
ACTIVATE/ORIENT -> DIAGNOSE -> TEACH -> QUESTION -> TEST -> CORRECT -> REVIEW -> RECORD
```

- `ACTIVATE/ORIENT`：先说明当前模块在全书或主题中的位置、要解决的问题、依赖的旧概念和后续关系。
- `DIAGNOSE`：判断学习者已有理解和缺口。
- `TEACH`：只讲当前模块真正需要掌握的内容。
- `QUESTION`：用追问检查理解深度。
- `TEST`：通过解释题、迁移题或代码题评估掌握度。
- `CORRECT`：定位错误类型，补缺口，而不是简单给答案。
- `REVIEW`：安排复习和薄弱点重测。
- `RECORD`：更新学习记录、错题、复习队列和索引。

## 项目结构

```text
.
├── SKILL.md                         # Skill 主入口和行为协议
├── references/                      # 教学循环、掌握度、记录格式、文件安全等规则
├── scripts/                         # 书籍结构检查和 Markdown 拆分工具
├── examples/                        # 测试场景和使用样例
├── .claude/skills/...               # Claude Code 可直接使用的副本
└── .agents/skills/...               # Agent/Codex 环境使用的副本或嵌套仓库
```

其中 `SKILL.md` 是最重要的文件。它定义了触发条件、八大模式、模块拆分规则、掌握度量表、新会话恢复协议、文件写入安全规则和引用索引。

## 快速开始

### Claude Code

把 `.claude/skills/bloom-2-sigma-learning-tutor/` 放到你的 Claude Code skills 目录，或在当前仓库中直接使用这份副本。

### Codex / Agent 环境

把 `.agents/skills/bloom-2-sigma-learning-tutor/` 放到你的 Agent skills 目录，或复制根目录的 `SKILL.md`、`references/`、`scripts/`、`examples/` 组成同名 skill。

### 常用触发语

- `开始学习这本书`
- `继续学习`
- `复习今天到期内容`
- `整理本次学习记录`
- `更新掌握度`
- `生成错题本`
- `跨书关联这个概念`
- `拆分这本书`
- `详细讲讲`
- `从头讲起`
- `零基础学历史`

## Helper 脚本

仓库包含两个 Python helper：

- `scripts/inspect_book_structure.py`：检查 Markdown 书稿的章节、节、小节和字数结构，并给出模块拆分建议。
- `scripts/split_markdown_book.py`：把 Markdown 全书按章节和小节拆成多个文件，便于逐模块学习。

运行测试：

```powershell
python -B -m unittest scripts.test_book_scripts -v
```

## 学习记录和隐私

这个框架会在实际使用时读写学习记录，例如：

```text
learning-records/
history/
```

这些目录通常包含个人学习进度、错题、复习队列、会话记录和原始材料，不建议作为框架的一部分公开提交。本仓库的目标是发布可复用的学习 Skill 框架，而不是公开个人学习资料。

## 版本

- `v1.0.0`：2026-05-09 初始版本。
- 当前 `master`：包含新会话恢复、模块拆分脚本修复、Windows 输出兼容、文件安全和测试覆盖等改进。

## License

Personal learning framework. Use and adapt at your own discretion.
