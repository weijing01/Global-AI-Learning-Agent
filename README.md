# Global AI 课程引导型智能体（手机网页演示版）

本项目来自你上传的 PythonProject2。保留 `Planner`、`Tutor`、`Evaluator`、`RAG`、`Skill`、`Memory`，使用 Streamlit 作为手机和电脑均可访问的网页入口。

## 第一步：本地运行

建议 Python 3.11–3.13：

```bash
python -m pip install -r requirements.txt
```

在项目根目录创建 `.env`，填入（不要上传这个文件）：

```env
DEEPSEEK_API_KEY=你的实际密钥
```

运行：

```bash
python -m streamlit run app.py
```

打开终端输出的网址。

## 第二步：上传 GitHub

1. 新建仓库，上传本压缩包中**项目文件夹里的内容**（包括隐藏的 `.gitignore`、`.streamlit/config.toml`）。
2. 不上传 `.env`、`.venv`、`progress.json`、`student_profile.json`、`rag_cache/` 和私人 PDF。
3. 如果拥有合法上传权限，可将课程 PDF 放入 `course_data/`，否则该文件夹保持空白（RAG 会缺少官方讲义）。

## 第三步：Streamlit Community Cloud

1. 前往 https://share.streamlit.io ，用 GitHub 登录，创建应用。
2. 选择新仓库、主分支和入口文件 `app.py`。
3. 在应用设置的 **Secrets** 中填写（不要加多余注释）：

```toml
DEEPSEEK_API_KEY = "你的实际密钥"
```

4. 部署后使用生成的 `https://...streamlit.app` 地址在手机上测试。

## 重要限制

- **当前代码仅适合个人/受控课堂演示，不适合公开多用户上线。** `memory.py` 目前使用共享的 `progress.json` 和 `student_profile.json`，用户上传 PDF 也保存在共享的 `user_materials/`，不同访客可能访问到同一份数据。请勿公开传播应用链接让多人录入真实个人资料。
- Community Cloud 的本地文件存储不保证重启后长期保留。真正面向多名学生使用前应加登录、按用户隔离数据、持久化数据库和上传权限限制。
- `course_data/` 原压缩包中没有 PDF。本包没有擅自补入课程资料。
- 本项目只完成**静态代码检查与部署结构整理**；未验证真实 DeepSeek API 调用或在线部署。
- 本次文件以用户提供的中文版代码为基础，原压缩包中不含 `language.py`，不能假定已经实现完整中英韩界面。
