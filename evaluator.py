import os
import json

from dotenv import load_dotenv
from openai import OpenAI


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
# 规范化选择题答案
#
# 支持：
# A
# a
# A.
# A 选项
# =========================================================

def normalize_choice(answer):

    if answer is None:
        return ""

    answer = str(answer).strip().upper()

    if not answer:
        return ""

    first_char = answer[0]

    if first_char in [
        "A",
        "B",
        "C",
        "D"
    ]:
        return first_char

    return answer


# =========================================================
# 根据总分决定下一步
# =========================================================

def decide_action(score):

    if score < 60:
        return "relearn"

    elif score < 80:
        return "practice_more"

    else:
        return "next_topic"


# =========================================================
# 简答题语义评分
# =========================================================

def evaluate_short_answer(
        topic,
        question,
        reference_points,
        user_answer
):

    # =====================================================
    # 没回答
    # =====================================================

    if not str(user_answer).strip():

        return {
            "score": 0,
            "weak_points": [
                "简答题未作答"
            ],
            "feedback": (
                "简答题没有作答，"
                "因此暂时无法确认对该知识点的实际理解。"
            )
        }


    # =====================================================
    # System Prompt
    # =====================================================

    system_prompt = """
你是 Evaluator Agent。

你现在只负责评价一道简答题。

这不是关键词匹配任务。

学生可以使用任何合理的语言表达。

你必须根据学生答案表达的真实语义，
判断学生是否理解了知识点。

==================================================
评分原则
==================================================

这道简答题满分50分。

评分时重点判断：

1. 核心概念是否正确
2. 是否覆盖参考要点中的主要思想
3. 是否存在明显错误理解
4. 是否能够用自己的语言说明
5. 表达方式不同不能因此扣分

reference_points只是参考语义要点。

不能要求学生逐字匹配。

例如：

参考答案写：

“return把结果返回给调用者”

学生写：

“return会把函数算出来的值交给外面的程序继续用”

这应该认为语义正确。

==================================================
评分建议
==================================================

45-50：
理解非常完整，核心概念正确，没有明显遗漏。

35-44：
理解基本正确，但缺少少量关键细节。

25-34：
理解了一部分，但存在明显遗漏。

10-24：
只有少量正确内容，理解不稳定。

0-9：
基本没有理解，或者存在严重错误。

==================================================
输出要求
==================================================

只输出合法JSON。

不要Markdown。
不要额外解释。

格式：

{
  "score": 0,
  "weak_points": [
    "薄弱点1",
    "薄弱点2"
  ],
  "feedback": "针对简答题的简短评价"
}
"""


    # =====================================================
    # User Prompt
    # =====================================================

    user_prompt = f"""
当前学习主题：

{topic}


简答题：

{question}


参考语义要点：

{json.dumps(
    reference_points,
    ensure_ascii=False,
    indent=2
)}


学生答案：

{user_answer}


请根据学生答案表达的实际语义进行评分。

不要因为措辞和参考要点不同就判错。
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

            temperature=0.1
        )


        content = (
            response
            .choices[0]
            .message
            .content
        )


        print(
            "\n=== 简答题评分模型原始输出 ==="
        )

        print(
            content
        )


        content = clean_json_text(
            content
        )


        result = json.loads(
            content
        )


        short_score = result.get(
            "score",
            0
        )


        # =================================================
        # 保证分数是数字
        # =================================================

        try:

            short_score = float(
                short_score
            )

        except (
            TypeError,
            ValueError
        ):

            short_score = 0


        # =================================================
        # 简答题最高50
        # =================================================

        short_score = max(
            0,
            min(
                50,
                short_score
            )
        )


        return {
            "score": short_score,

            "weak_points": result.get(
                "weak_points",
                []
            ),

            "feedback": result.get(
                "feedback",
                ""
            )
        }


    except Exception as e:

        return {
            "score": 0,

            "weak_points": [
                "简答题评分失败"
            ],

            "feedback": (
                f"简答题自动评分发生错误：{e}"
            )
        }


# =========================================================
# Evaluator Agent
# =========================================================

def evaluator_agent(
        topic,
        questions,
        user_answers
):

    # =====================================================
    # 基础数据检查
    # =====================================================

    if not isinstance(
        questions,
        list
    ):

        return {
            "error": "questions必须是列表"
        }


    if len(questions) != 3:

        return {
            "error": "Evaluator需要正好3道题"
        }


    if not isinstance(
        user_answers,
        list
    ):

        return {
            "error": "user_answers必须是列表"
        }


    if len(user_answers) != 3:

        return {
            "error": "需要提供3道题的答案"
        }


    # =====================================================
    # 检查题型
    # =====================================================

    question_1 = questions[0]
    question_2 = questions[1]
    question_3 = questions[2]


    if (
        question_1.get("type")
        != "multiple_choice"
    ):

        return {
            "error": "第1题必须是选择题"
        }


    if (
        question_2.get("type")
        != "multiple_choice"
    ):

        return {
            "error": "第2题必须是选择题"
        }


    if (
        question_3.get("type")
        != "short_answer"
    ):

        return {
            "error": "第3题必须是简答题"
        }


    # =====================================================
    # 第1题
    # 25分
    # =====================================================

    answer_1 = normalize_choice(
        user_answers[0]
    )


    correct_1 = normalize_choice(
        question_1.get(
            "correct_answer",
            ""
        )
    )


    if (
        answer_1
        and
        answer_1 == correct_1
    ):

        score_1 = 25

        result_1 = "正确"

    else:

        score_1 = 0

        result_1 = "错误"


    # =====================================================
    # 第2题
    # 25分
    # =====================================================

    answer_2 = normalize_choice(
        user_answers[1]
    )


    correct_2 = normalize_choice(
        question_2.get(
            "correct_answer",
            ""
        )
    )


    if (
        answer_2
        and
        answer_2 == correct_2
    ):

        score_2 = 25

        result_2 = "正确"

    else:

        score_2 = 0

        result_2 = "错误"


    # =====================================================
    # 第3题
    # AI语义评分
    # 50分
    # =====================================================

    short_evaluation = (
        evaluate_short_answer(

            topic=topic,

            question=question_3.get(
                "question",
                ""
            ),

            reference_points=(
                question_3.get(
                    "reference_points",
                    []
                )
            ),

            user_answer=(
                user_answers[2]
            )
        )
    )


    score_3 = (
        short_evaluation.get(
            "score",
            0
        )
    )


    # =====================================================
    # 总分
    # =====================================================

    total_score = (
        score_1
        +
        score_2
        +
        score_3
    )


    total_score = round(
        total_score,
        1
    )


    # =====================================================
    # 薄弱点
    # =====================================================

    weak_points = []


    # 第1题错了
    if score_1 == 0:

        weak_points.append(
            f"选择题1："
            f"{question_1.get('question', '')}"
        )


    # 第2题错了
    if score_2 == 0:

        weak_points.append(
            f"选择题2："
            f"{question_2.get('question', '')}"
        )


    # 加入简答题分析出来的薄弱点
    for point in (
        short_evaluation.get(
            "weak_points",
            []
        )
    ):

        if point not in weak_points:

            weak_points.append(
                point
            )


    # =====================================================
    # 下一步
    # =====================================================

    action = decide_action(
        total_score
    )


    # =====================================================
    # 综合反馈
    # =====================================================

    feedback_parts = []


    # =====================================================
    # 选择题反馈
    # =====================================================

    choice_score = (
        score_1
        +
        score_2
    )


    if choice_score == 50:

        feedback_parts.append(
            "两道选择题均回答正确，"
            "说明基础概念掌握较稳定。"
        )


    elif choice_score == 25:

        feedback_parts.append(
            "两道选择题中答对1题，"
            "基础概念仍有部分需要巩固。"
        )


    else:

        feedback_parts.append(
            "两道选择题均未答对，"
            "建议重新确认当前知识点的基本概念。"
        )


    # =====================================================
    # 简答题反馈
    # =====================================================

    short_feedback = (
        short_evaluation.get(
            "feedback",
            ""
        )
    )


    if short_feedback:

        feedback_parts.append(
            short_feedback
        )


    feedback = " ".join(
        feedback_parts
    )


    # =====================================================
    # 返回最终结果
    # =====================================================

    return {

        "score":
            total_score,

        "weak_points":
            weak_points,

        "feedback":
            feedback,

        "action":
            action,


        # =================================================
        # 下面这些属于详细结果
        #
        # app.py暂时不显示也没关系
        # 后面如果需要展示每道题得分可以直接使用
        # =================================================

        "details": {

            "question_1": {
                "type":
                    "multiple_choice",

                "user_answer":
                    answer_1,

                "correct_answer":
                    correct_1,

                "result":
                    result_1,

                "score":
                    score_1,

                "max_score":
                    25
            },


            "question_2": {
                "type":
                    "multiple_choice",

                "user_answer":
                    answer_2,

                "correct_answer":
                    correct_2,

                "result":
                    result_2,

                "score":
                    score_2,

                "max_score":
                    25
            },


            "question_3": {
                "type":
                    "short_answer",

                "user_answer":
                    user_answers[2],

                "score":
                    score_3,

                "max_score":
                    50,

                "feedback":
                    short_feedback
            }
        }
    }


# =========================================================
# 单独测试
# =========================================================

if __name__ == "__main__":

    topic = "Python函数"


    questions = [

        {
            "type":
                "multiple_choice",

            "question":
                "Python中哪个关键字用于返回函数结果？",

            "options": {
                "A": "print",
                "B": "return",
                "C": "input",
                "D": "import"
            },

            "correct_answer":
                "B"
        },


        {
            "type":
                "multiple_choice",

            "question":
                "下面关于函数参数的说法，哪一个正确？",

            "options": {
                "A": "参数只能是数字",
                "B": "函数不能有多个参数",
                "C": "参数可以把数据传入函数",
                "D": "参数必须叫x"
            },

            "correct_answer":
                "C"
        },


        {
            "type":
                "short_answer",

            "question":
                "请用自己的话说明print和return的区别。",

            "reference_points": [
                "print主要用于显示或输出内容",
                "return把结果返回给函数调用者",
                "return返回的结果可以继续被其他代码使用"
            ]
        }
    ]


    user_answers = [
        "B",
        "C",
        (
            "print只是把结果显示出来，"
            "return会把函数计算的值交出去，"
            "这样外面的代码还能继续使用这个结果。"
        )
    ]


    result = evaluator_agent(
        topic=topic,
        questions=questions,
        user_answers=user_answers
    )


    print(
        "\n=== Evaluator结果 ==="
    )


    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )