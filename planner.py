import os
import json
from openai import OpenAI
from dotenv import load_dotenv


# =========================================================
# 环境变量
# =========================================================

load_dotenv()


# =========================================================
# DeepSeek Client
# =========================================================

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


MODEL_ID = "deepseek-chat"


# =========================================================
# AI硕士课程基础要求
#
# 这里不是职业要求。
# 它代表当前AI硕士课程体系中常见的基础能力。
# =========================================================

PROGRAM_REQUIREMENTS = """
【编程基础】
- Python基础语法
- 条件与循环
- 列表与字典
- 函数
- 类与对象
- NumPy
- Pandas
- JSON
- API
- requests
- Git与GitHub

【数学基础】
- 向量
- 矩阵
- 矩阵乘法
- 点积
- 张量与Shape
- 导数
- 偏导数
- 梯度
- 链式法则
- 基础概率
- 条件概率
- 贝叶斯公式
- 期望与均值
- 方差
- 概率分布
- 指数
- 对数
- 熵与交叉熵

【机器学习】
- 人工智能基本概念
- 算法基本概念
- 机器学习基本概念
- 监督学习
- 回归与分类
- 训练集、验证集、测试集
- 过拟合与欠拟合
- 损失函数
- 模型评估
- Precision / Recall / F1
- 逻辑回归
- 朴素贝叶斯
- SVM
- 决策树
- 随机森林
- Boosting

【深度学习】
- 神经元
- 权重与偏置
- Sigmoid
- ReLU
- Softmax
- 前向传播
- 梯度下降
- 反向传播
- 多层神经网络
- CNN
- Attention
- Transformer

【NLP】
- 正则表达式
- 文本预处理
- Tokenization
- 词频
- N-gram
- Language Model
- Perplexity
- Embedding

【AI / Agent开发】
- LLM基本概念
- Token
- Context
- Temperature
- Top-k / Top-p
- Prompt Engineering
- Structured Output
- Function Calling
- Tool Calling
- Agent基本概念
- Agent Loop
- ReAct
- RAG
- Memory
- Multi-Agent
- MCP
- PRD与需求分析
- HTML
- CSS
- JavaScript
- Streamlit
- 幻觉与结果验证
"""


# =========================================================
# 职业方向参考
#
# Planner 可以参考这些方向，
# 但不能机械按照模板推荐。
# =========================================================

CAREER_REFERENCE = """
【AI / LLM Agent工程师】
重点能力：
Python、API、JSON、LLM、Prompt Engineering、
Function Calling、Tool Calling、RAG、Memory、
Agent Loop、ReAct、Multi-Agent、MCP、Streamlit。

【机器学习工程师】
重点能力：
Python、NumPy、Pandas、概率统计、机器学习、
数据处理、模型训练、模型评估、特征工程、
逻辑回归、树模型、Boosting。

【深度学习工程师】
重点能力：
Python、NumPy、矩阵、梯度、链式法则、
神经网络、前向传播、反向传播、
CNN、Attention、Transformer。

【NLP工程师】
重点能力：
Python、概率、文本处理、N-gram、
Language Model、Embedding、逻辑回归、
朴素贝叶斯、Attention、Transformer。

【计算机视觉工程师】
重点能力：
Python、NumPy、线性代数、微积分、
梯度、神经网络、反向传播、CNN、
深度学习基础。

【数据科学家】
重点能力：
Python、Pandas、NumPy、概率统计、
数据分析、机器学习、模型评估、
数据可视化和实验分析。

【数据分析师】
重点能力：
Python、Pandas、数据处理、
基础统计、数据可视化、
业务分析和结果解释。

【AI软件工程师】
重点能力：
Python、API、JSON、Git、
软件开发、LLM应用、RAG、
Agent、Streamlit、前后端基础。

【AI产品经理】
重点能力：
AI基本概念、LLM能力边界、
Prompt、Agent基本概念、
PRD、需求分析、结果验证、
AI产品设计与沟通。

【AI研究员 / 博士方向】
重点能力：
线性代数、概率统计、微积分、
机器学习、深度学习、
论文阅读、实验设计、
研究问题定义和模型理解。
"""


# =========================================================
# 清理模型输出
# =========================================================

def clean_json_text(text):

    if not text:
        return ""

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


# =========================================================
# Planner Agent
# =========================================================

def planner_agent(
        user_profile,
        progress,
        target_course=None,
        career_goal=None
):

    # =====================================================
    # 兼容旧版app.py
    #
    # 如果仍然传 target_course，
    # 就把它当作 career_goal。
    # =====================================================

    if not career_goal:

        if target_course:

            career_goal = target_course

        else:

            career_goal = "待定"


    # =====================================================
    # 学习历史
    # =====================================================

    if progress:

        progress_text = json.dumps(
            progress,
            ensure_ascii=False,
            indent=2
        )

    else:

        progress_text = "暂无历史学习记录"


    # =====================================================
    # Prompt
    # =====================================================

    system_prompt = """
你是一个面向AI硕士学生的学习规划Agent。

你的任务不是简单推荐课程，而是根据：

1. AI硕士课程所需要的基础能力
2. 学生的专业背景
3. 学生自己填写的知识掌握程度
4. 未来职业目标
5. 真实学习和测试历史

判断学生当前最应该学习的一个具体知识点。

同时，你还需要进行职业方向规划。

职业规划不是永久固定的。

它应该根据学生当前能力和后续真实学习表现动态调整。

==================================================
学习规划原则
==================================================

证据优先级：

真实测试和学习历史
>
当前知识掌握情况
>
专业背景
>
职业目标

专业背景只能作为参考。

不能因为学生来自某个专业，
就直接假设他一定掌握某项知识。

也不能因为一次测试成绩不好，
就完全否定学生整个能力方向。

推荐知识点必须足够具体。

例如：

可以推荐：
- Python函数
- 矩阵乘法
- 条件概率
- Sigmoid函数
- 逻辑回归
- Function Calling
- RAG

不要推荐：

- 学习Python
- 学习数学
- 学习机器学习
- 学习AI

==================================================
学习阶段
==================================================

difficulty只能输出：

beginner
intermediate
advanced

对应含义：

beginner
=
基础建立

学生当前需要建立基本概念和直觉。

intermediate
=
能力强化

学生已经理解基础，
需要加强应用、推理和常见问题。

advanced
=
综合应用

学生已经具备较强基础，
适合综合问题、项目和复杂应用。

==================================================
职业方向规划
==================================================

如果职业目标是“待定”：

根据学生当前能力画像和学习历史，
推荐最适合的3个职业方向。

如果职业目标已经明确：

不要直接否定用户的选择。

判断当前职业目标与学生能力的匹配程度，
同时给出2个相邻或可替代方向。

职业方向必须能够随着后续学习记录变化。

current_match只能是：

"较低"
"一般"
"较高"

recommended_careers必须正好3个。

如果用户已有明确职业目标，
第一个原则上应该保留用户当前目标，
除非该方向明显与当前学习情况完全不符。

职业建议不是就业承诺，
只代表当前能力结构和学习方向的匹配程度。

==================================================
输出要求
==================================================

只输出合法JSON。

不要Markdown。
不要```json。
不要额外解释。

必须严格输出：

{
  "topic": "具体知识点",
  "reason": "为什么现在最应该学习这个知识点",
  "difficulty": "beginner/intermediate/advanced",
  "career_plan": {
    "current_match": "较低/一般/较高",
    "recommended_careers": [
      "职业1",
      "职业2",
      "职业3"
    ],
    "reason": "为什么当前推荐这些职业方向，以及未来可能根据什么变化进行调整"
  }
}
"""


    user_prompt = f"""
下面是AI硕士课程体系中常见的基础要求：

==============================
课程基础要求
==============================

{PROGRAM_REQUIREMENTS}


==============================
职业方向能力参考
==============================

{CAREER_REFERENCE}


==============================
学生画像
==============================

{user_profile}


==============================
学生未来职业目标
==============================

{career_goal}


==============================
历史学习和测试记录
==============================

{progress_text}


请完成两个任务：

1.
判断学生当前最应该补的一个具体知识点。

2.
根据学生当前能力、
未来职业目标和真实学习记录，
给出当前职业方向规划。

注意：

职业方向规划必须具有动态性。

如果未来学习成绩、
薄弱点或能力画像变化，
职业匹配度和推荐方向也应该可以变化。

只输出规定JSON。
"""


    # =====================================================
    # 调用模型
    # =====================================================

    try:

        response = client.chat.completions.create(

            model=MODEL_ID,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],

            temperature=0.3
        )


        raw_output = (
            response
            .choices[0]
            .message
            .content
        )


        cleaned_output = clean_json_text(
            raw_output
        )


        result = json.loads(
            cleaned_output
        )


        # =================================================
        # 基础字段检查
        # =================================================

        required_fields = [
            "topic",
            "reason",
            "difficulty",
            "career_plan"
        ]


        for field in required_fields:

            if field not in result:

                raise ValueError(
                    f"Planner缺少字段：{field}"
                )


        # =================================================
        # difficulty保护
        # =================================================

        if result["difficulty"] not in [
            "beginner",
            "intermediate",
            "advanced"
        ]:

            result["difficulty"] = (
                "beginner"
            )


        # =================================================
        # career_plan保护
        # =================================================

        career_plan = result.get(
            "career_plan",
            {}
        )


        if "current_match" not in career_plan:

            career_plan[
                "current_match"
            ] = "一般"


        if "recommended_careers" not in career_plan:

            career_plan[
                "recommended_careers"
            ] = [
                career_goal,
                "AI软件工程师",
                "机器学习工程师"
            ]


        if "reason" not in career_plan:

            career_plan[
                "reason"
            ] = (
                "将根据后续学习表现持续调整职业方向。"
            )


        result[
            "career_plan"
        ] = career_plan


        return result


    except json.JSONDecodeError:

        return {
            "error": "Planner返回的内容不是合法JSON。",
            "raw_output": raw_output
        }


    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================================
# 单独测试
# =========================================================

if __name__ == "__main__":

    test_profile = """
专业背景：
电气工程

未来职业目标：
AI / LLM Agent工程师

已有知识基础：
Python：B
数学基础：C
机器学习：C
深度学习：D
Agent开发：D
"""

    test_progress = {}

    result = planner_agent(
        user_profile=test_profile,
        progress=test_progress,
        career_goal="AI / LLM Agent工程师"
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )