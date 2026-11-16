import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from rag import search_course_material

from skills import (
    adaptive_explanation,
    quiz_generation
)


# =========================================================
# 环境变量
# =========================================================

load_dotenv()


# =========================================================
# DeepSeek
# =========================================================

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

MODEL_ID = "deepseek-chat"


# =========================================================
# JSON清理
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
# 学习阶段说明
# =========================================================

def get_difficulty_instruction(
        difficulty
):

    difficulty_map = {

        "beginner": """
当前阶段：基础建立。

教学要求：

1. 优先帮助学生建立正确的核心概念。
2. 使用简单、直观的语言。
3. 先讲直觉，再讲必要公式。
4. 不要一次加入过多高级知识。
5. 使用容易理解的具体例子。
""",

        "intermediate": """
当前阶段：能力强化。

教学要求：

1. 学生已经具备一定基础。
2. 重点解释原理、应用和常见错误。
3. 可以加入适量公式、代码或实际案例。
4. 强调知识之间的联系。
5. 测试学生能否真正应用知识。
""",

        "advanced": """
当前阶段：综合应用。

教学要求：

1. 学生已经具备较好的基础。
2. 减少过多基础定义。
3. 重点关注综合应用、实际场景和边界情况。
4. 可以加入更复杂的推理、代码或案例。
"""
    }


    return difficulty_map.get(
        difficulty,
        difficulty_map["beginner"]
    )


# =========================================================
# 整理 RAG 资料
# =========================================================

def build_course_context(
        rag_results
):

    if not rag_results:

        return (
            """
没有检索到与当前知识点直接相关的资料。

可以使用通用知识完成必要讲解，
但不要虚构内容来自 Global AI 课程资料
或用户上传资料。
"""
        ), []


    course_context = ""

    source_list = []


    for index, result in enumerate(
        rag_results,
        start=1
    ):

        filename = (
            result.get(
                "filename",
                "未知文件"
            )
        )


        page = (
            result.get(
                "page"
            )
        )


        content = (
            result.get(
                "content",
                ""
            )
        )


        source_type = (
            result.get(
                "source_type",
                "course"
            )
        )


        # =================================================
        # 来源类型
        # =================================================

        if source_type == "course":

            source_label = (
                "Global AI课程资料"
            )

        else:

            source_label = (
                "用户补充资料"
            )


        # =================================================
        # 页面
        # =================================================

        if page:

            page_text = (
                f"第 {page} 页"
            )

        else:

            page_text = (
                "页码未知"
            )


        # =================================================
        # 给 Prompt
        # =================================================

        course_context += f"""

【资料 {index}】

资料类型：
{source_label}

文件：
{filename}

位置：
{page_text}

内容：
{content}

"""


        # =================================================
        # 给 app.py 显示
        # =================================================

        source_display = (
            f"{source_label}："
            f"{filename}"
        )


        if page:

            source_display += (
                f"（第 {page} 页）"
            )


        source_list.append(
            source_display
        )


    # =====================================================
    # 去重
    # =====================================================

    source_list = list(
        dict.fromkeys(
            source_list
        )
    )


    return (
        course_context,
        source_list
    )


# =========================================================
# Tutor Agent
# =========================================================

def tutor_agent(
        topic,
        difficulty="beginner",
        weak_points=None,
        attempt_count=1
):

    # =====================================================
    # 参数处理
    # =====================================================

    weak_points = (
        weak_points
        if weak_points
        else []
    )


    if attempt_count < 1:

        attempt_count = 1


    # =====================================================
    # Skill 1
    # 自适应讲解
    # =====================================================

    explanation_skill = (
        adaptive_explanation(
            weak_points=weak_points,
            attempt_count=attempt_count
        )
    )


    # =====================================================
    # Skill 2
    # 自适应出题
    # =====================================================

    quiz_skill = (
        quiz_generation(
            weak_points=weak_points,
            attempt_count=attempt_count
        )
    )


    # =====================================================
    # RAG
    #
    # rag.py 会同时检索：
    #
    # course_data
    # user_materials
    #
    # 并优先 Global AI 官方资料
    # =====================================================

    try:

        rag_results = (
            search_course_material(
                topic=topic,
                max_results=4,
                context_lines=5
            )
        )


    except Exception as e:

        print(
            f"RAG检索失败：{e}"
        )

        rag_results = []


    # =====================================================
    # 整理 RAG
    # =====================================================

    course_context, source_list = (
        build_course_context(
            rag_results
        )
    )


    # =====================================================
    # 学习阶段
    # =====================================================

    difficulty_instruction = (
        get_difficulty_instruction(
            difficulty
        )
    )


    # =====================================================
    # 薄弱点
    # =====================================================

    if weak_points:

        weak_points_text = "\n".join(
            f"- {point}"
            for point
            in weak_points
        )

    else:

        weak_points_text = (
            "这是第一次学习当前知识点，"
            "目前没有历史薄弱点。"
        )


    # =====================================================
    # System Prompt
    # =====================================================

    system_prompt = """
你是“Global AI课程引导型智能体”中的 Tutor Agent。

你的职责不是单纯回答问题，
而是根据课程资料、学生状态、上一轮薄弱点和 Skill，
完成一轮针对性学习与测试。


==================================================
一、资料优先级
==================================================

系统可能提供两类资料：

1. Global AI课程资料
2. 用户自己上传的补充学习资料


资料优先级：

Global AI课程资料 > 用户补充资料 > 通用知识


必须遵守：

- Global AI课程资料是课程学习的主要依据。
- 用户资料只作为补充解释和辅助学习。
- 如果两种资料表达不同，优先遵循 Global AI课程资料。
- 不要声称用户资料属于 Global AI官方课程。
- 不要把通用知识伪装成课程资料中的内容。


==================================================
二、教学目标
==================================================

每轮学习应尽量回答：

1. 当前知识点是什么？
2. 为什么 Global AI 学习中需要它？
3. 它是怎么工作的？
4. 它和其他相关知识有什么关系？
5. 学生最容易在哪里出错？


==================================================
三、Skill
==================================================

系统会给你两个 Skill：

1. adaptive_explanation
   决定本轮应该如何讲解。

2. quiz_generation
   决定本轮应该如何生成测试题。


Skill 是本轮教学必须遵守的策略。

不要忽略 Skill。


==================================================
四、重新学习
==================================================

如果 attempt_count > 1：

说明学生之前已经学习过当前知识点，
但没有完全掌握。

此时必须：

1. 不要简单复制上一轮讲法。
2. 根据 adaptive_explanation Skill 更换教学方式。
3. 重点处理 weak_points。
4. 使用新的例子、类比、数字或拆解方式。
5. 根据 quiz_generation Skill 重新生成新题。
6. 不要把上一轮题目原样再次生成。


==================================================
五、讲解难度
==================================================

讲解难度必须和当前 difficulty 匹配。

beginner：
重点建立基础概念。

intermediate：
重点加强原理和实际应用。

advanced：
重点综合应用和复杂场景。


==================================================
六、掌握度测验
==================================================

固定生成3道题：

第1题：
multiple_choice

第2题：
multiple_choice

第3题：
short_answer


选择题要求：

- 每题必须有 A / B / C / D 四个选项。
- 只能有一个正确答案。
- 正确答案不能直接出现在题干提示中。
- 题目应该检查理解，不只是死记硬背。


简答题要求：

- 学生可以用自己的话回答。
- 不要求逐字匹配参考答案。
- 必须提供 reference_points。
- reference_points 给 Evaluator Agent 做语义评分。
- 不要在题目中直接泄露 reference_points。


==================================================
七、重新出题
==================================================

如果 attempt_count > 1：

必须重新设计题目。

可以：

- 换场景
- 换数字
- 换问法
- 针对上一轮薄弱点
- 增加诊断性

但是不能：

- 原样复制上一轮题目
- 只改变选项顺序


==================================================
八、输出
==================================================

只能输出合法 JSON。

不要输出 Markdown 代码块。

JSON结构必须是：

{
  "topic": "知识点",

  "learning_goal": "本轮学习目标",

  "explanation": "本轮完整讲解",

  "key_points": [
    "核心要点1",
    "核心要点2",
    "核心要点3"
  ],

  "common_mistake": "常见误区",

  "example": "具体例子",

  "questions": [
    {
      "type": "multiple_choice",
      "question": "题目1",
      "options": {
        "A": "选项A",
        "B": "选项B",
        "C": "选项C",
        "D": "选项D"
      },
      "correct_answer": "B"
    },

    {
      "type": "multiple_choice",
      "question": "题目2",
      "options": {
        "A": "选项A",
        "B": "选项B",
        "C": "选项C",
        "D": "选项D"
      },
      "correct_answer": "C"
    },

    {
      "type": "short_answer",
      "question": "简答题",
      "reference_points": [
        "核心点1",
        "核心点2",
        "核心点3"
      ]
    }
  ]
}
"""


    # =====================================================
    # User Prompt
    # =====================================================

    user_prompt = f"""
==============================
当前知识点
==============================

{topic}


==============================
当前学习阶段
==============================

{difficulty_instruction}


==============================
当前是第几次学习
==============================

第 {attempt_count} 次


==============================
上一轮薄弱点
==============================

{weak_points_text}


==============================
Skill 1
自适应讲解
==============================

Skill名称：

{explanation_skill.get("skill", "")}


当前策略：

{explanation_skill.get("strategy", "")}


策略名称：

{explanation_skill.get("strategy_name", "")}


执行要求：

{explanation_skill.get("instruction", "")}


==============================
Skill 2
自适应出题
==============================

Skill名称：

{quiz_skill.get("skill", "")}


当前模式：

{quiz_skill.get("mode", "")}


模式名称：

{quiz_skill.get("mode_name", "")}


执行要求：

{quiz_skill.get("instruction", "")}


==============================
本轮可使用的学习资料
==============================

{course_context}


请完成本轮：

针对性学习
+
掌握度测验


要求：

1. 优先使用 Global AI课程资料。
2. 用户资料只作为补充。
3. 按当前 Skill 调整教学方法。
4. 如果是重新学习，重点处理上一轮 weak_points。
5. 必须生成2道选择题和1道简答题。
6. 只输出合法JSON。
"""


    # =====================================================
    # 调用 DeepSeek
    # =====================================================

    try:

        response = (
            client.chat.completions.create(
                model=MODEL_ID,

                messages=[
                    {
                        "role":
                            "system",

                        "content":
                            system_prompt
                    },

                    {
                        "role":
                            "user",

                        "content":
                            user_prompt
                    }
                ],

                temperature=0.5
            )
        )


        content = (
            response
            .choices[0]
            .message
            .content
        )


        print(
            "\n"
            "===================================="
        )

        print(
            "=== Tutor模型原始输出 ==="
        )

        print(
            "===================================="
        )

        print(
            content
        )


        # =================================================
        # 清理JSON
        # =================================================

        cleaned_content = (
            clean_json_text(
                content
            )
        )


        # =================================================
        # JSON解析
        # =================================================

        result = (
            json.loads(
                cleaned_content
            )
        )


        # =================================================
        # 基本字段检查
        # =================================================

        required_fields = [
            "topic",
            "learning_goal",
            "explanation",
            "key_points",
            "common_mistake",
            "example",
            "questions"
        ]


        for field in required_fields:

            if field not in result:

                raise ValueError(
                    f"Tutor缺少字段：{field}"
                )


        # =================================================
        # key_points检查
        # =================================================

        if not isinstance(
            result.get(
                "key_points"
            ),
            list
        ):

            raise ValueError(
                "key_points必须是列表"
            )


        # =================================================
        # Questions
        # =================================================

        questions = (
            result.get(
                "questions",
                []
            )
        )


        if not isinstance(
            questions,
            list
        ):

            raise ValueError(
                "questions必须是列表"
            )


        if len(questions) != 3:

            raise ValueError(
                "Tutor必须生成3道题"
            )


        # =================================================
        # 第1题
        # =================================================

        if (
            questions[0].get(
                "type"
            )
            != "multiple_choice"
        ):

            raise ValueError(
                "第1题必须是选择题"
            )


        # =================================================
        # 第2题
        # =================================================

        if (
            questions[1].get(
                "type"
            )
            != "multiple_choice"
        ):

            raise ValueError(
                "第2题必须是选择题"
            )


        # =================================================
        # 第3题
        # =================================================

        if (
            questions[2].get(
                "type"
            )
            != "short_answer"
        ):

            raise ValueError(
                "第3题必须是简答题"
            )


        # =================================================
        # 检查两个选择题
        # =================================================

        for index in [
            0,
            1
        ]:

            question = (
                questions[
                    index
                ]
            )


            question_text = (
                question.get(
                    "question"
                )
            )


            if not question_text:

                raise ValueError(
                    f"第{index + 1}题缺少题目"
                )


            options = (
                question.get(
                    "options",
                    {}
                )
            )


            if not isinstance(
                options,
                dict
            ):

                raise ValueError(
                    f"第{index + 1}题 options 格式错误"
                )


            # =============================================
            # A-D
            # =============================================

            for option_key in [
                "A",
                "B",
                "C",
                "D"
            ]:

                if (
                    option_key
                    not in options
                ):

                    raise ValueError(
                        f"第{index + 1}题"
                        f"缺少选项"
                        f"{option_key}"
                    )


                if not str(
                    options[
                        option_key
                    ]
                ).strip():

                    raise ValueError(
                        f"第{index + 1}题"
                        f"选项"
                        f"{option_key}"
                        f"为空"
                    )


            # =============================================
            # correct_answer
            # =============================================

            correct_answer = (
                question.get(
                    "correct_answer"
                )
            )


            if correct_answer not in [
                "A",
                "B",
                "C",
                "D"
            ]:

                raise ValueError(
                    f"第{index + 1}题"
                    "正确答案格式错误"
                )


        # =================================================
        # 简答题
        # =================================================

        short_question = (
            questions[2]
        )


        if not short_question.get(
            "question"
        ):

            raise ValueError(
                "第3题缺少题目"
            )


        reference_points = (
            short_question.get(
                "reference_points",
                []
            )
        )


        if not isinstance(
            reference_points,
            list
        ):

            raise ValueError(
                "第3题 reference_points 必须是列表"
            )


        if not reference_points:

            raise ValueError(
                "第3题缺少 reference_points"
            )


        # =================================================
        # 给 app.py 附加资料来源
        # =================================================

        result[
            "sources"
        ] = source_list


        # =================================================
        # 学习阶段
        # =================================================

        result[
            "difficulty"
        ] = difficulty


        # =================================================
        # 第几次学习
        # =================================================

        result[
            "attempt_count"
        ] = attempt_count


        # =================================================
        # Skill信息
        # =================================================

        result[
            "skills_used"
        ] = [

            {
                "skill":
                    explanation_skill.get(
                        "skill",
                        "adaptive_explanation"
                    ),

                "strategy":
                    explanation_skill.get(
                        "strategy",
                        ""
                    ),

                "name":
                    explanation_skill.get(
                        "strategy_name",
                        "自适应讲解"
                    )
            },

            {
                "skill":
                    quiz_skill.get(
                        "skill",
                        "quiz_generation"
                    ),

                "strategy":
                    quiz_skill.get(
                        "mode",
                        ""
                    ),

                "name":
                    quiz_skill.get(
                        "mode_name",
                        "自适应出题"
                    )
            }
        ]


        # =================================================
        # 是否使用RAG
        # =================================================

        result[
            "rag_used"
        ] = (
            len(
                rag_results
            )
            > 0
        )


        # =================================================
        # 返回
        # =================================================

        return result


    # =====================================================
    # JSON错误
    # =====================================================

    except json.JSONDecodeError as e:

        return {

            "error":
                f"Tutor没有返回合法JSON：{e}",

            "raw_output":
                content
                if "content" in locals()
                else ""
        }


    # =====================================================
    # 其他错误
    # =====================================================

    except Exception as e:

        return {

            "error":
                str(e),

            "raw_output":
                content
                if "content" in locals()
                else ""
        }


# =========================================================
# 单独测试
# =========================================================

if __name__ == "__main__":

    test_result = (
        tutor_agent(
            topic="逻辑回归",

            difficulty="beginner",

            weak_points=[
                "Sigmoid函数",
                "分类阈值"
            ],

            attempt_count=2
        )
    )


    print(
        "\n"
        "===================================="
    )

    print(
        "=== Tutor测试结果 ==="
    )

    print(
        "===================================="
    )


    print(
        json.dumps(
            test_result,
            ensure_ascii=False,
            indent=2
        )
    )