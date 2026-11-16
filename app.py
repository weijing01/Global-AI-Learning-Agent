import os

import streamlit as st
from dotenv import load_dotenv

# Cloud: use Streamlit Secrets. Local: use .env. Never put real keys in code.
load_dotenv()
try:
    cloud_key = st.secrets.get("DEEPSEEK_API_KEY")
except (FileNotFoundError, KeyError, AttributeError):
    cloud_key = None
if cloud_key and not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = str(cloud_key)

if not os.getenv("DEEPSEEK_API_KEY"):
    st.error("未配置 DeepSeek API Key。请在 Streamlit Cloud → App settings → Secrets 中设置 DEEPSEEK_API_KEY。")
    st.stop()
import numpy as np
import matplotlib.pyplot as plt

from planner import planner_agent
from tutor import tutor_agent
from evaluator import evaluator_agent

from memory import (
    load_progress,
    save_progress,

    load_self_assessment,
    save_self_assessment,

    get_learning_records,
    get_learning_records_by_date,
    get_daily_summary,
    get_recurring_weak_points,
    get_learning_trend,
    get_memory_summary,

    get_topic_attempt_count,
    update_latest_record_action,

    clear_progress
)


# =========================================================
# 页面设置
# =========================================================

st.set_page_config(
    page_title="Global AI课程引导型智能体",
    page_icon="🎓",
    layout="wide"
)


# Responsive layout: compact headings and spacing on phones only.
st.markdown("""
<style>
@media (max-width: 640px) {
    .stMainBlockContainer, .block-container {
        padding-top: 0.75rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 4rem !important;
    }
    .stMainBlockContainer h1, .block-container h1 {
        font-size: 1.75rem !important;
        line-height: 1.3 !important;
        overflow-wrap: anywhere;
        margin: 0.45rem 0 0.65rem !important;
    }
    .stMainBlockContainer h2, .block-container h2 {
        font-size: 1.4rem !important;
        line-height: 1.35 !important;
        margin: 0.8rem 0 0.4rem !important;
    }
    .stMainBlockContainer h3, .block-container h3 {
        font-size: 1.2rem !important;
        line-height: 1.35 !important;
        margin: 0.65rem 0 0.3rem !important;
    }
    .stMainBlockContainer p, .block-container p,
    .stMainBlockContainer li, .block-container li {
        font-size: 0.96rem;
        line-height: 1.6;
        overflow-wrap: anywhere;
    }
    .stMainBlockContainer [data-testid="stVerticalBlock"] {
        gap: 0.7rem;
    }
    .stMainBlockContainer [data-testid="stMarkdownContainer"] pre {
        max-width: 100%;
        overflow-x: auto;
    }
    .stMainBlockContainer .stButton button,
    .stMainBlockContainer .stDownloadButton button {
        min-height: 2.65rem;
        white-space: normal;
        overflow-wrap: anywhere;
    }
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# Matplotlib 中文字体
# =========================================================

plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans"
]

plt.rcParams["axes.unicode_minus"] = False


# =========================================================
# 系统参数
# =========================================================

PASS_SCORE = 80

MAX_ATTEMPTS_PER_TOPIC = 3


# =========================================================
# 文件目录
# =========================================================

COURSE_DATA_DIR = "course_data"

USER_MATERIAL_DIR = "user_materials"


os.makedirs(
    COURSE_DATA_DIR,
    exist_ok=True
)

os.makedirs(
    USER_MATERIAL_DIR,
    exist_ok=True
)


# =========================================================
# 页面标题
# =========================================================

st.title(
    "🎓 Global AI课程引导型智能体"
)

st.write(
    "根据 Global AI 课程要求、未来职业目标、"
    "已有知识基础和真实学习表现，"
    "动态诊断知识缺口、调整学习路径并提供课程学习引导。"
)


# =========================================================
# Session State
# =========================================================

if "plan" not in st.session_state:
    st.session_state.plan = None


if "lesson" not in st.session_state:
    st.session_state.lesson = None


if "evaluation" not in st.session_state:
    st.session_state.evaluation = None


if "show_radar" not in st.session_state:
    st.session_state.show_radar = False


if "show_all_records" not in st.session_state:
    st.session_state.show_all_records = False


if "confirm_clear_records" not in st.session_state:
    st.session_state.confirm_clear_records = False


if "confirm_skip_topic" not in st.session_state:
    st.session_state.confirm_skip_topic = False


# =========================================================
# A-E 等级
# =========================================================

LEVEL_OPTIONS = [
    "E · 未掌握",
    "D · 入门",
    "C · 一般",
    "B · 熟悉",
    "A · 精通"
]


LEVEL_SCORE_MAP = {
    "E · 未掌握": 20,
    "D · 入门": 50,
    "C · 一般": 67,
    "B · 熟悉": 82,
    "A · 精通": 95
}


# =========================================================
# 分数 → 等级
# =========================================================

def score_to_grade(score):

    if score >= 90:
        return "A · 精通"

    elif score >= 75:
        return "B · 熟悉"

    elif score >= 60:
        return "C · 一般"

    elif score >= 40:
        return "D · 入门"

    return "E · 未掌握"


# =========================================================
# Action → 中文
# =========================================================

def action_to_text(action):

    action_map = {
        "relearn": "重新学习",
        "practice_more": "继续练习",
        "next_topic": "进入下一知识点",
        "replan": "重新规划学习路径",
        "user_skip": "用户选择暂时跳过"
    }

    return action_map.get(
        action,
        action if action else "暂无"
    )


# =========================================================
# 知识体系
# =========================================================

KNOWLEDGE_CATEGORIES = {

    "编程基础": [
        "Python基础语法",
        "条件与循环",
        "列表与字典",
        "函数",
        "类与对象",
        "NumPy",
        "Pandas",
        "JSON",
        "API",
        "requests",
        "Git与GitHub"
    ],

    "数学基础": [
        "向量",
        "矩阵",
        "矩阵乘法",
        "点积",
        "张量与Shape",

        "导数",
        "偏导数",
        "梯度",
        "链式法则",

        "基础概率",
        "条件概率",
        "贝叶斯公式",

        "期望与均值",
        "方差",
        "概率分布",

        "指数",
        "对数",
        "熵与交叉熵"
    ],

    "机器学习": [
        "人工智能基本概念",
        "算法基本概念",
        "机器学习基本概念",

        "监督学习",
        "回归与分类",

        "训练集验证集测试集",
        "过拟合与欠拟合",

        "损失函数",
        "模型评估",

        "Precision / Recall / F1",

        "逻辑回归",
        "朴素贝叶斯",
        "SVM",

        "决策树",
        "随机森林",
        "Boosting"
    ],

    "深度学习": [
        "神经元",
        "权重与偏置",

        "Sigmoid",
        "ReLU",
        "Softmax",

        "前向传播",
        "梯度下降",
        "反向传播",

        "多层神经网络",
        "CNN",

        "Attention",
        "Transformer"
    ],

    "NLP": [
        "正则表达式",
        "文本预处理",

        "Tokenization",
        "词频",

        "N-gram",
        "Language Model",
        "Perplexity",

        "Embedding"
    ],

    "AI / Agent开发": [
        "LLM基本概念",

        "Token",
        "Context",

        "Temperature",
        "Top-k / Top-p",

        "Prompt Engineering",

        "Structured Output",
        "Function Calling",
        "Tool Calling",

        "Agent基本概念",
        "Agent Loop",
        "ReAct",

        "RAG",
        "Memory",

        "Multi-Agent",
        "MCP",

        "PRD与需求分析",

        "HTML",
        "CSS",
        "JavaScript",

        "Streamlit",

        "幻觉与结果验证"
    ]
}


# =========================================================
# 职业选项
# =========================================================

CAREER_OPTIONS = [
    "待定",
    "AI / LLM Agent工程师",
    "机器学习工程师",
    "深度学习工程师",
    "NLP工程师",
    "计算机视觉工程师",
    "数据科学家",
    "数据分析师",
    "AI软件工程师",
    "AI产品经理",
    "AI研究员 / 博士方向",
    "其他 / 自定义"
]


# =========================================================
# 知识类别关键词
# =========================================================

CATEGORY_KEYWORDS = {

    "编程基础": [
        "Python",
        "函数",
        "类",
        "NumPy",
        "Pandas",
        "JSON",
        "API",
        "Git"
    ],

    "数学基础": [
        "向量",
        "矩阵",
        "点积",
        "导数",
        "偏导",
        "梯度",
        "概率",
        "贝叶斯",
        "期望",
        "方差",
        "指数",
        "对数",
        "熵"
    ],

    "机器学习": [
        "机器学习",
        "监督学习",
        "回归",
        "分类",
        "逻辑回归",
        "朴素贝叶斯",
        "SVM",
        "决策树",
        "随机森林",
        "Boosting",
        "Precision",
        "Recall",
        "F1"
    ],

    "深度学习": [
        "神经元",
        "Sigmoid",
        "ReLU",
        "Softmax",
        "反向传播",
        "CNN",
        "Attention",
        "Transformer"
    ],

    "NLP": [
        "NLP",
        "自然语言",
        "Tokenization",
        "N-gram",
        "Language Model",
        "Perplexity",
        "Embedding"
    ],

    "AI / Agent开发": [
        "LLM",
        "Prompt",
        "Function Calling",
        "Tool",
        "Agent",
        "ReAct",
        "RAG",
        "Memory",
        "Multi-Agent",
        "MCP",
        "Streamlit"
    ]
}


# =========================================================
# 推断类别
# =========================================================

def infer_category(topic):

    topic_lower = str(
        topic
    ).lower()

    for category, keywords in (
        CATEGORY_KEYWORDS.items()
    ):

        for keyword in keywords:

            if keyword.lower() in topic_lower:
                return category

    return "机器学习"


# =========================================================
# 初始化自评
# =========================================================

saved_self_assessment = (
    load_self_assessment()
)


for category, subjects in (
    KNOWLEDGE_CATEGORIES.items()
):

    for subject in subjects:

        key = (
            f"knowledge_{category}_{subject}"
        )

        if key not in st.session_state:

            saved_level = (
                saved_self_assessment
                .get(category, {})
                .get(
                    subject,
                    "E · 未掌握"
                )
            )

            if saved_level not in LEVEL_OPTIONS:

                saved_level = (
                    "E · 未掌握"
                )

            st.session_state[
                key
            ] = saved_level


# =========================================================
# 批量设置
# =========================================================

def set_category_knowledge(
        category,
        level
):

    for subject in (
        KNOWLEDGE_CATEGORIES.get(
            category,
            []
        )
    ):

        st.session_state[
            f"knowledge_{category}_{subject}"
        ] = level


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    # =====================================================
    # 学生信息
    # =====================================================

    st.header(
        "👤 学生信息"
    )


    professional_background = (
        st.text_input(
            "专业背景",
            placeholder=(
                "例如：电气工程、计算机、传媒、音乐"
            )
        )
    )


    selected_career = (
        st.selectbox(
            "未来想从事的职业",
            CAREER_OPTIONS
        )
    )


    if (
        selected_career
        == "其他 / 自定义"
    ):

        custom_career = (
            st.text_input(
                "请输入职业目标"
            )
        )

        career_goal = (
            custom_career.strip()
            if custom_career.strip()
            else "待定"
        )

    else:

        career_goal = (
            selected_career
        )


    if career_goal == "待定":

        st.caption(
            "如果暂时没有明确职业目标，"
            "系统会结合学习表现动态推荐方向。"
        )

    else:

        st.caption(
            "系统会随着后续学习表现动态调整职业匹配建议。"
        )


    # =====================================================
    # 已有知识基础
    # =====================================================

    st.divider()

    st.header(
        "📚 已有知识基础"
    )


    st.caption(
        "可以按知识类别批量设置，"
        "再单独修改具体知识点。"
    )


    knowledge_profile = {}


    for category, subjects in (
        KNOWLEDGE_CATEGORIES.items()
    ):

        with st.expander(
            category
        ):

            knowledge_profile[
                category
            ] = {}


            category_level = (
                st.selectbox(
                    "批量设置本类",
                    LEVEL_OPTIONS,
                    index=2,
                    key=f"batch_{category}"
                )
            )


            if st.button(
                f"应用到「{category}」",
                key=f"apply_{category}",
                use_container_width=True
            ):

                set_category_knowledge(
                    category,
                    category_level
                )

                st.rerun()


            st.divider()


            for subject in subjects:

                level = (
                    st.selectbox(
                        subject,
                        LEVEL_OPTIONS,
                        key=(
                            f"knowledge_"
                            f"{category}_"
                            f"{subject}"
                        )
                    )
                )


                knowledge_profile[
                    category
                ][subject] = level


    # =====================================================
    # 用户自己的学习资料
    # =====================================================

    st.divider()

    st.header(
        "📂 我的学习资料"
    )


    st.caption(
        "可以上传自己的 PDF 学习资料。"
        "这些资料会作为 Global AI 官方课程资料的补充知识来源。"
    )


    st.info(
        "Global AI 课程资料优先，"
        "个人上传资料用于补充解释和学习。"
    )


    uploaded_files = (
        st.file_uploader(
            "上传 PDF 学习资料",
            type=["pdf"],
            accept_multiple_files=True,
            key="user_material_uploader"
        )
    )


    # =====================================================
    # 保存上传文件
    # =====================================================

    if uploaded_files:

        newly_added = []


        for uploaded_file in (
            uploaded_files
        ):

            # 防止目录路径注入
            safe_filename = (
                os.path.basename(
                    uploaded_file.name
                )
            )


            save_path = (
                os.path.join(
                    USER_MATERIAL_DIR,
                    safe_filename
                )
            )


            if not os.path.exists(
                save_path
            ):

                with open(
                    save_path,
                    "wb"
                ) as f:

                    f.write(
                        uploaded_file.getbuffer()
                    )


                newly_added.append(
                    safe_filename
                )


        if newly_added:

            for filename in newly_added:

                st.success(
                    f"已添加：{filename}"
                )


            st.caption(
                "新资料会在下一次 Tutor 检索时自动进入知识库。"
            )


    # =====================================================
    # 已上传文件
    # =====================================================

    existing_materials = [

        filename

        for filename
        in os.listdir(
            USER_MATERIAL_DIR
        )

        if filename.lower().endswith(
            ".pdf"
        )
    ]


    if existing_materials:

        with st.expander(
            f"📚 已添加的学习资料（{len(existing_materials)}）"
        ):

            for filename in sorted(
                existing_materials
            ):

                st.write(
                    f"📄 {filename}"
                )


    else:

        st.caption(
            "目前还没有添加个人学习资料。"
        )


    # =====================================================
    # 学习记录
    # =====================================================

    st.divider()

    st.header(
        "📖 学习记录"
    )


    all_records = (
        get_learning_records()
    )


    daily_records = (
        get_learning_records_by_date()
    )


    if not all_records:

        st.caption(
            "目前还没有学习记录。"
        )


    else:

        # =================================================
        # 学习趋势
        # =================================================

        trend = (
            get_learning_trend()
        )


        st.caption(
            "📈 最近学习趋势："
            f"{trend.get('trend_text', '数据不足')}"
        )


        dates = list(
            daily_records.keys()
        )


        if (
            st.session_state
            .show_all_records
        ):

            dates_to_show = (
                dates
            )

        else:

            dates_to_show = (
                dates[:3]
            )


        # =================================================
        # 每日记录
        # =================================================

        for date_index, date in enumerate(
            dates_to_show
        ):

            records = (
                daily_records[
                    date
                ]
            )


            daily_summary = (
                get_daily_summary(
                    date
                )
            )


            study_count = (
                daily_summary.get(
                    "study_count",
                    0
                )
            )


            average_score = (
                daily_summary.get(
                    "average_score",
                    0
                )
            )


            with st.expander(
                (
                    f"📅 {date}"
                    f"｜{study_count}次学习"
                    f"｜平均{average_score}分"
                ),
                expanded=(
                    date_index == 0
                )
            ):

                st.markdown(
                    "#### 📊 当日总结"
                )


                c1, c2 = (
                    st.columns(2)
                )


                with c1:

                    st.metric(
                        "学习次数",
                        study_count
                    )


                with c2:

                    st.metric(
                        "平均成绩",
                        average_score
                    )


                mastered = (
                    daily_summary.get(
                        "mastered_topics",
                        []
                    )
                )


                if mastered:

                    st.markdown(
                        "**✅ 达到掌握标准**"
                    )


                    for topic in mastered:

                        st.write(
                            f"- {topic}"
                        )


                unfinished = (
                    daily_summary.get(
                        "unfinished_topics",
                        []
                    )
                )


                if unfinished:

                    st.markdown(
                        "**📌 仍需继续**"
                    )


                    for topic in unfinished:

                        st.write(
                            f"- {topic}"
                        )


                daily_weak = (
                    daily_summary.get(
                        "weak_points",
                        []
                    )
                )


                if daily_weak:

                    st.markdown(
                        "**🔍 当日薄弱点**"
                    )


                    for item in (
                        daily_weak[:5]
                    ):

                        point = (
                            item.get(
                                "weak_point",
                                ""
                            )
                        )


                        count = (
                            item.get(
                                "count",
                                1
                            )
                        )


                        if count > 1:

                            st.write(
                                f"- {point}"
                                f"（出现 {count} 次）"
                            )

                        else:

                            st.write(
                                f"- {point}"
                            )


                st.divider()

                st.markdown(
                    "#### 📝 当日学习详情"
                )


                for record in records:

                    topic = (
                        record.get(
                            "topic",
                            ""
                        )
                    )


                    record_datetime = (
                        record.get(
                            "datetime",
                            ""
                        )
                    )


                    if (
                        record_datetime
                        and
                        len(record_datetime)
                        >= 16
                    ):

                        display_time = (
                            record_datetime[
                                11:16
                            ]
                        )

                    else:

                        display_time = (
                            ""
                        )


                    score = (
                        record.get(
                            "score",
                            0
                        )
                    )


                    attempt = (
                        record.get(
                            "attempt",
                            1
                        )
                    )


                    action = (
                        record.get(
                            "action",
                            ""
                        )
                    )


                    weak_points = (
                        record.get(
                            "weak_points",
                            []
                        )
                    )


                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"**{topic}**"
                        )


                        st.caption(
                            f"🕒 {display_time}"
                        )


                        st.write(
                            f"第 **{attempt}** 次尝试"
                        )


                        st.write(
                            f"成绩："
                            f"**{score} / 100**"
                        )


                        st.write(
                            "状态："
                            +
                            action_to_text(
                                action
                            )
                        )


                        if weak_points:

                            st.markdown(
                                "**薄弱点：**"
                            )


                            for point in weak_points:

                                st.write(
                                    f"- {point}"
                                )


        # =================================================
        # 展开所有记录
        # =================================================

        if len(dates) > 3:

            if st.button(
                (
                    "收起历史学习记录"
                    if
                    st.session_state
                    .show_all_records
                    else
                    "查看全部学习记录"
                ),
                key="toggle_records",
                use_container_width=True
            ):

                st.session_state.show_all_records = (
                    not
                    st.session_state.show_all_records
                )

                st.rerun()


        st.caption(
            f"累计学习 "
            f"{len(all_records)} 次，"
            f"共 {len(daily_records)} 天"
        )


        # =================================================
        # 长期薄弱点
        # =================================================

        recurring = (
            get_recurring_weak_points(
                limit=5
            )
        )


        if recurring:

            with st.expander(
                "🧠 长期薄弱点"
            ):

                for item in recurring:

                    st.write(
                        f"- "
                        f"{item.get('weak_point', '')} "
                        f"（出现 "
                        f"{item.get('count', 0)} 次）"
                    )


        # =================================================
        # 清除学习记录
        # =================================================

        st.divider()


        if not (
            st.session_state
            .confirm_clear_records
        ):

            if st.button(
                "🗑️ 清除学习记录",
                key="clear_records_button",
                use_container_width=True
            ):

                st.session_state.confirm_clear_records = (
                    True
                )

                st.rerun()


        else:

            st.warning(
                "确定清除全部学习记录吗？"
                "A–E 自评和上传的学习资料不会删除。"
            )


            cc1, cc2 = (
                st.columns(2)
            )


            with cc1:

                if st.button(
                    "取消",
                    key="cancel_clear_button",
                    use_container_width=True
                ):

                    st.session_state.confirm_clear_records = (
                        False
                    )

                    st.rerun()


            with cc2:

                if st.button(
                    "确认清除",
                    key="confirm_clear_button",
                    type="primary",
                    use_container_width=True
                ):

                    clear_progress()

                    st.session_state.plan = None
                    st.session_state.lesson = None
                    st.session_state.evaluation = None

                    st.session_state.confirm_clear_records = False
                    st.session_state.show_all_records = False

                    st.rerun()


# =========================================================
# 保存自评
# =========================================================

save_self_assessment(
    knowledge_profile
)


# =========================================================
# 能力计算
# =========================================================

def calculate_self_scores(
        profile
):

    result = {}


    for category, subjects in (
        profile.items()
    ):

        values = [

            LEVEL_SCORE_MAP.get(
                level,
                20
            )

            for level
            in subjects.values()
        ]


        result[
            category
        ] = (
            sum(values)
            / len(values)

            if values

            else 20
        )


    return result


# =========================================================
# 获取真实测试分数
# =========================================================

def get_assessment_scores(
        progress
):

    result = {
        category: []
        for category
        in KNOWLEDGE_CATEGORIES
    }


    for topic, data in (
        progress.items()
    ):

        for record in (
            data.get(
                "history",
                []
            )
        ):

            category = (
                record.get(
                    "category"
                )
                or
                infer_category(
                    topic
                )
            )


            score = (
                record.get(
                    "score"
                )
            )


            if (
                category in result
                and
                isinstance(
                    score,
                    (int, float)
                )
            ):

                result[
                    category
                ].append(
                    score
                )


    return result


# =========================================================
# 动态能力值
# =========================================================

def calculate_dynamic_scores(
        self_scores,
        progress
):

    test_scores = (
        get_assessment_scores(
            progress
        )
    )


    result = {}


    for category in (
        KNOWLEDGE_CATEGORIES
    ):

        self_score = (
            self_scores.get(
                category,
                20
            )
        )


        scores = (
            test_scores.get(
                category,
                []
            )
        )


        if not scores:

            result[
                category
            ] = round(
                self_score,
                1
            )

            continue


        recent = (
            scores[-5:]
        )


        weights = list(
            range(
                1,
                len(recent) + 1
            )
        )


        weighted_test = (
            sum(
                score * weight

                for score, weight
                in zip(
                    recent,
                    weights
                )
            )
            /
            sum(weights)
        )


        self_weight = max(
            0.20,

            1
            /
            (
                1
                +
                0.7
                * len(scores)
            )
        )


        final = (
            self_score
            * self_weight
            +
            weighted_test
            * (
                1
                - self_weight
            )
        )


        if self_score >= 90:

            final = max(
                final,
                75
            )


        elif self_score >= 75:

            final = max(
                final,
                60
            )


        elif self_score >= 60:

            final = max(
                final,
                40
            )


        result[
            category
        ] = round(
            final,
            1
        )


    return result


# =========================================================
# 当前数据
# =========================================================

progress = (
    load_progress()
)


self_scores = (
    calculate_self_scores(
        knowledge_profile
    )
)


ability_scores = (
    calculate_dynamic_scores(
        self_scores,
        progress
    )
)


# =========================================================
# 当前能力值
# =========================================================

st.subheader(
    "🧭 当前能力值"
)


st.caption(
    "首次能力值主要来自已有知识自评；"
    "随着真实学习和测试增加，"
    "实际表现会逐渐影响能力值。"
)


if st.button(
    "📊 查看 / 收起能力雷达图"
):

    st.session_state.show_radar = (
        not
        st.session_state.show_radar
    )


if st.session_state.show_radar:

    labels = list(
        ability_scores.keys()
    )


    values = list(
        ability_scores.values()
    )


    angles = np.linspace(
        0,
        2 * np.pi,
        len(labels),
        endpoint=False
    ).tolist()


    closed_angles = (
        angles
        + angles[:1]
    )


    closed_values = (
        values
        + values[:1]
    )


    fig, ax = plt.subplots(
        figsize=(4.2, 4.2),
        subplot_kw={
            "polar": True
        }
    )


    ax.plot(
        closed_angles,
        closed_values,
        linewidth=1.8
    )


    ax.fill(
        closed_angles,
        closed_values,
        alpha=0.20
    )


    ax.set_xticks(
        angles
    )


    # Linux cloud images do not necessarily include Chinese fonts.
    # Use short ASCII category labels on the chart and a Chinese legend below it.
    radar_name_map = {
        "编程基础": "Coding",
        "数学基础": "Math",
        "机器学习": "ML",
        "深度学习": "DL",
        "NLP": "NLP",
        "AI / Agent开发": "AI Agent",
    }
    radar_labels = [
        radar_name_map.get(label, f"Area {i + 1}")
        for i, label in enumerate(labels)
    ]

    ax.set_xticklabels(
        radar_labels,
        fontsize=9
    )


    ax.set_ylim(
        0,
        100
    )


    ax.set_yticks(
        [
            20,
            40,
            60,
            75,
            90
        ]
    )


    ax.set_yticklabels(
        [
            "E",
            "D",
            "C",
            "B",
            "A"
        ]
    )


    ax.set_title(
        "Learning Ability",
        fontsize=12,
        pad=17
    )


    # Expand naturally to the available width on desktop and mobile.
    fig.tight_layout(pad=1.5)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.caption(
        "图例：Coding＝编程基础；Math＝数学基础；ML＝机器学习；"
        "DL＝深度学习；NLP＝自然语言处理；AI Agent＝AI / Agent开发。"
    )


# =========================================================
# 等级说明
# =========================================================

with st.expander(
    "查看 A–E 等级说明"
):

    st.markdown(
        """
### A · 精通
90–100

能够稳定理解、应用并处理综合问题。

### B · 熟悉
75–89

能够较稳定地理解和应用相关知识。

### C · 一般
60–74

能够理解基本内容并解决一般问题。

### D · 入门
40–59

已经接触相关概念，但独立应用仍不稳定。

### E · 未掌握
0–39

当前尚未建立稳定的知识基础。
"""
    )


# =========================================================
# Planner Profile
# =========================================================

knowledge_text = ""


for category, subjects in (
    knowledge_profile.items()
):

    knowledge_text += (
        f"\n【{category}】\n"
    )


    for subject, level in (
        subjects.items()
    ):

        knowledge_text += (
            f"{subject}："
            f"{level}\n"
        )


ability_text = ""


for category, score in (
    ability_scores.items()
):

    ability_text += (
        f"{category}："
        f"{score}分，"
        f"{score_to_grade(score)}\n"
    )


memory_summary = (
    get_memory_summary()
)


user_profile = f"""
专业背景：

{
    professional_background
    if professional_background.strip()
    else "未填写"
}


未来职业目标：

{career_goal}


==============================
已有知识基础
==============================

{knowledge_text}


==============================
当前能力值
==============================

{ability_text}


==============================
长期学习Memory
==============================

累计学习记录：

{memory_summary.get("total_learning_records", 0)}


累计学习天数：

{memory_summary.get("learning_days", 0)}


最近学习趋势：

{
    memory_summary
    .get(
        "learning_trend",
        {}
    )
    .get(
        "trend_text",
        "数据不足"
    )
}


反复薄弱点：

{
    memory_summary.get(
        "recurring_weak_points",
        []
    )
}
"""


# =========================================================
# 1. Planner
# =========================================================

st.divider()


st.header(
    "1️⃣ 学习诊断与职业方向规划"
)


if st.button(
    "🔍 分析我的知识缺口与职业方向",
    use_container_width=True
):

    with st.spinner(
        "Planner 正在结合 Global AI 课程要求、"
        "当前能力值和长期学习记录进行分析..."
    ):

        plan = (
            planner_agent(
                user_profile=user_profile,
                progress=load_progress(),
                career_goal=career_goal
            )
        )


    if "error" in plan:

        st.error(
            str(plan)
        )

    else:

        st.session_state.plan = (
            plan
        )

        st.session_state.lesson = None

        st.session_state.evaluation = None


# =========================================================
# Planner 输出
# =========================================================

if st.session_state.plan:

    plan = (
        st.session_state.plan
    )


    difficulty_map = {

        "beginner":
            "基础建立",

        "intermediate":
            "能力强化",

        "advanced":
            "综合应用"
    }


    c1, c2 = (
        st.columns(
            [
                2,
                1
            ]
        )
    )


    with c1:

        st.markdown(
            "### 📌 当前最需要补的知识"
        )

        st.markdown(
            f"### "
            f"{plan.get('topic', '')}"
        )


    with c2:

        st.markdown(
            "### 🎯 当前学习阶段"
        )

        st.markdown(
            "### "
            +
            difficulty_map.get(
                plan.get(
                    "difficulty",
                    "beginner"
                ),
                "基础建立"
            )
        )


    st.subheader(
        "💡 为什么先学这个"
    )


    st.write(
        plan.get(
            "reason",
            ""
        )
    )


    # =====================================================
    # 职业规划
    # =====================================================

    career_plan = (
        plan.get(
            "career_plan",
            {}
        )
    )


    st.subheader(
        "🧭 职业方向规划"
    )


    st.write(
        "当前匹配度："
        f"**"
        f"{career_plan.get('current_match', '一般')}"
        f"**"
    )


    recommended_careers = (
        career_plan.get(
            "recommended_careers",
            []
        )
    )


    for career in (
        recommended_careers
    ):

        st.write(
            f"- {career}"
        )


    st.write(
        career_plan.get(
            "reason",
            ""
        )
    )


# =========================================================
# 2. Tutor
# =========================================================

if st.session_state.plan:

    st.header(
        "2️⃣ 针对性学习测试"
    )


    if st.button(
        "📚 开始针对性学习",
        use_container_width=True
    ):

        plan = (
            st.session_state.plan
        )


        current_topic = (
            plan.get(
                "topic",
                ""
            )
        )


        current_attempt = (
            get_topic_attempt_count(
                current_topic
            )
            + 1
        )


        with st.spinner(
            "Tutor 正在检索课程资料和个人学习资料..."
        ):

            lesson = (
                tutor_agent(
                    topic=current_topic,

                    difficulty=plan.get(
                        "difficulty",
                        "beginner"
                    ),

                    weak_points=None,

                    attempt_count=current_attempt
                )
            )


        if "error" in lesson:

            st.error(
                str(lesson)
            )

        else:

            st.session_state.lesson = (
                lesson
            )

            st.session_state.evaluation = None


# =========================================================
# Tutor 输出
# =========================================================

if st.session_state.lesson:

    lesson = (
        st.session_state.lesson
    )


    st.subheader(
        f"📖 "
        f"{lesson.get('topic', '')}"
    )


    # =====================================================
    # Skill
    # =====================================================

    skills_used = (
        lesson.get(
            "skills_used",
            []
        )
    )


    if skills_used:

        with st.expander(
            "🧩 本轮使用的 Skill"
        ):

            for skill in skills_used:

                st.write(
                    f"**"
                    f"{skill.get('name', '')}"
                    f"**"
                )

                st.caption(
                    skill.get(
                        "skill",
                        ""
                    )
                )


    # =====================================================
    # Tutor内容
    # =====================================================

    st.markdown(
        "### 🎯 本轮学习目标"
    )


    st.write(
        lesson.get(
            "learning_goal",
            ""
        )
    )


    st.markdown(
        "### 📘 知识讲解"
    )


    st.write(
        lesson.get(
            "explanation",
            ""
        )
    )


    key_points = (
        lesson.get(
            "key_points",
            []
        )
    )


    if key_points:

        st.markdown(
            "### 📌 核心要点"
        )


        for point in key_points:

            st.write(
                f"- {point}"
            )


    if lesson.get(
        "common_mistake"
    ):

        st.markdown(
            "### ⚠️ 常见误区"
        )

        st.warning(
            lesson.get(
                "common_mistake"
            )
        )


    st.markdown(
        "### 🌰 示例"
    )


    st.write(
        lesson.get(
            "example",
            ""
        )
    )


    # =====================================================
    # 来源
    # =====================================================

    sources = (
        lesson.get(
            "sources",
            []
        )
    )


    if sources:

        with st.expander(
            "📚 本轮参考资料"
        ):

            for source in sources:

                st.write(
                    f"- {source}"
                )


    # =====================================================
    # 掌握度测验
    # =====================================================

    st.header(
        "📝 掌握度测验"
    )


    current_topic = (
        lesson.get(
            "topic",
            ""
        )
    )


    questions = (
        lesson.get(
            "questions",
            []
        )
    )


    answers = []


    for i, question in enumerate(
        questions,
        start=1
    ):

        st.markdown(
            f"### 第 {i} 题"
        )


        # =================================================
        # 选择题
        # =================================================

        if (
            question.get(
                "type"
            )
            == "multiple_choice"
        ):

            st.write(
                question.get(
                    "question",
                    ""
                )
            )


            options = (
                question.get(
                    "options",
                    {}
                )
            )


            option_labels = []

            option_map = {}


            for key in [
                "A",
                "B",
                "C",
                "D"
            ]:

                text = (
                    f"{key}. "
                    f"{options.get(key, '')}"
                )


                option_labels.append(
                    text
                )


                option_map[
                    text
                ] = key


            selected = (
                st.radio(
                    "请选择：",
                    option_labels,
                    index=None,
                    key=f"choice_{i}"
                )
            )


            answers.append(
                option_map[
                    selected
                ]
                if selected
                else ""
            )


        # =================================================
        # 简答题
        # =================================================

        elif (
            question.get(
                "type"
            )
            == "short_answer"
        ):

            st.write(
                question.get(
                    "question",
                    ""
                )
            )


            answer = (
                st.text_area(
                    "请用自己的话回答：",
                    height=140,
                    key=(
                        f"short_answer_"
                        f"{i}"
                    )
                )
            )


            answers.append(
                answer
            )


    # =====================================================
    # 提交
    # =====================================================

    if st.button(
        "✅ 提交并评估",
        use_container_width=True
    ):

        if any(
            not str(
                answer
            ).strip()

            for answer
            in answers
        ):

            st.warning(
                "请先完成全部题目。"
            )


        else:

            with st.spinner(
                "Evaluator 正在进行综合测评..."
            ):

                evaluation = (
                    evaluator_agent(
                        topic=current_topic,
                        questions=questions,
                        user_answers=answers
                    )
                )


            if "error" in evaluation:

                st.error(
                    str(evaluation)
                )


            else:

                current_attempt = (
                    get_topic_attempt_count(
                        current_topic
                    )
                    + 1
                )


                score = (
                    evaluation.get(
                        "score",
                        0
                    )
                )


                if (
                    score
                    < PASS_SCORE

                    and

                    current_attempt
                    >= MAX_ATTEMPTS_PER_TOPIC
                ):

                    evaluation[
                        "action"
                    ] = "replan"


                save_progress(
                    topic=current_topic,

                    evaluation=evaluation,

                    category=(
                        infer_category(
                            current_topic
                        )
                    )
                )


                st.session_state.evaluation = (
                    evaluation
                )


                st.session_state.confirm_skip_topic = (
                    False
                )


                st.rerun()


# =========================================================
# 3. 综合测评
# =========================================================

if (
    st.session_state.evaluation
    and
    st.session_state.lesson
):

    evaluation = (
        st.session_state.evaluation
    )


    lesson = (
        st.session_state.lesson
    )


    current_topic = (
        lesson.get(
            "topic",
            ""
        )
    )


    score = (
        evaluation.get(
            "score",
            0
        )
    )


    weak_points = (
        evaluation.get(
            "weak_points",
            []
        )
    )


    action = (
        evaluation.get(
            "action",
            ""
        )
    )


    attempt_count = (
        get_topic_attempt_count(
            current_topic
        )
    )


    st.header(
        "3️⃣ 综合测评"
    )


    result_col1, result_col2 = (
        st.columns(2)
    )


    with result_col1:

        st.metric(
            "综合得分",
            f"{score} / 100"
        )


    with result_col2:

        st.metric(
            "当前尝试次数",
            (
                f"{attempt_count} / "
                f"{MAX_ATTEMPTS_PER_TOPIC}"
            )
        )


    # =====================================================
    # 每题结果
    # =====================================================

    details = (
        evaluation.get(
            "details",
            {}
        )
    )


    questions = (
        lesson.get(
            "questions",
            []
        )
    )


    if len(questions) == 3:

        st.subheader(
            "📝 测验结果"
        )


        for i in [
            1,
            2
        ]:

            question = (
                questions[
                    i - 1
                ]
            )


            detail = (
                details.get(
                    f"question_{i}",
                    {}
                )
            )


            if (
                detail.get(
                    "score"
                )
                == 25
            ):

                st.success(
                    f"第 {i} 题：正确"
                )

            else:

                st.error(
                    f"第 {i} 题：错误"
                )


            with st.expander(
                f"👀 查看第 {i} 题答案"
            ):

                correct = (
                    question.get(
                        "correct_answer",
                        ""
                    )
                )


                st.write(
                    "你的答案："
                    f"{detail.get('user_answer', '')}"
                )


                st.success(
                    "正确答案："
                    f"{correct}. "
                    f"{question.get('options', {}).get(correct, '')}"
                )


        # =================================================
        # 简答题
        # =================================================

        q3 = (
            questions[2]
        )


        d3 = (
            details.get(
                "question_3",
                {}
            )
        )


        st.info(
            f"第 3 题："
            f"{d3.get('score', 0)} / 50"
        )


        st.write(
            d3.get(
                "feedback",
                ""
            )
        )


        with st.expander(
            "👀 查看第 3 题参考答案"
        ):

            for point in (
                q3.get(
                    "reference_points",
                    []
                )
            ):

                st.write(
                    f"- {point}"
                )


    # =====================================================
    # 薄弱点
    # =====================================================

    st.subheader(
        "🔍 当前薄弱点"
    )


    if weak_points:

        for point in weak_points:

            st.write(
                f"- {point}"
            )

    else:

        st.write(
            "暂无明显薄弱点。"
        )


    # =====================================================
    # Feedback
    # =====================================================

    st.subheader(
        "💬 综合反馈"
    )


    st.write(
        evaluation.get(
            "feedback",
            ""
        )
    )


    # =====================================================
    # 下一步
    # =====================================================

    st.subheader(
        "➡️ 下一步"
    )


    # =====================================================
    # 已掌握
    # =====================================================

    if action == "next_topic":

        st.success(
            "当前知识点已经达到掌握标准。"
        )


        if st.button(
            "🧭 规划下一个知识点",
            type="primary",
            use_container_width=True,
            key="next_topic_button"
        ):

            next_profile = (
                user_profile
                +
                f"""

==============================
最新学习结果
==============================

已掌握知识点：

{current_topic}


成绩：

{score}


请根据 Global AI 课程要求、
当前能力值和长期学习 Memory，
规划下一个适合的学习内容。

不要无理由立即重复当前知识点。
"""
            )


            with st.spinner(
                "Planner 正在规划下一学习内容..."
            ):

                new_plan = (
                    planner_agent(
                        user_profile=next_profile,
                        progress=load_progress(),
                        career_goal=career_goal
                    )
                )


            if "error" in new_plan:

                st.error(
                    str(new_plan)
                )

            else:

                st.session_state.plan = (
                    new_plan
                )

                st.session_state.lesson = None
                st.session_state.evaluation = None

                st.rerun()


    # =====================================================
    # 三次失败
    # =====================================================

    elif action == "replan":

        st.error(
            "当前知识点连续3次仍未达到80分。"
        )


        st.warning(
            "系统将停止继续原地重复，"
            "并重新规划学习路径。"
        )


        if st.button(
            "🧭 重新规划学习路径",
            type="primary",
            use_container_width=True,
            key="replan_button"
        ):

            replan_profile = (
                user_profile
                +
                f"""

==============================
当前学习瓶颈
==============================

知识点：

{current_topic}


尝试次数：

{attempt_count}


最新成绩：

{score}


当前薄弱点：

{weak_points}


重新规划时：

1. 不要原样继续重复当前知识点。
2. 优先考虑更基础的知识。
3. 可以拆成更小的子知识点。
4. 结合长期 Memory 中反复出现的薄弱点。
5. 保持与 Global AI 课程要求一致。
"""
            )


            with st.spinner(
                "Planner 正在重新规划..."
            ):

                new_plan = (
                    planner_agent(
                        user_profile=replan_profile,
                        progress=load_progress(),
                        career_goal=career_goal
                    )
                )


            if "error" in new_plan:

                st.error(
                    str(new_plan)
                )

            else:

                st.session_state.plan = (
                    new_plan
                )

                st.session_state.lesson = None
                st.session_state.evaluation = None

                st.rerun()


    # =====================================================
    # 未达标
    # =====================================================

    else:

        st.warning(
            "当前成绩尚未达到80分掌握标准。"
        )


        # =================================================
        # 根据本轮结果重新学习
        # =================================================

        if st.button(
            "🔄 根据本轮结果重新学习",
            type="primary",
            use_container_width=True,
            key="retry_topic_button"
        ):

            plan = (
                st.session_state.plan
            )


            next_attempt = (
                attempt_count
                + 1
            )


            with st.spinner(
                "Tutor 正在根据薄弱点选择 Skill，"
                "重新讲解并生成新题..."
            ):

                new_lesson = (
                    tutor_agent(
                        topic=current_topic,

                        difficulty=plan.get(
                            "difficulty",
                            "beginner"
                        ),

                        weak_points=weak_points,

                        attempt_count=next_attempt
                    )
                )


            if "error" in new_lesson:

                st.error(
                    str(new_lesson)
                )

            else:

                st.session_state.lesson = (
                    new_lesson
                )

                st.session_state.evaluation = None

                st.session_state.confirm_skip_topic = False

                st.rerun()


        st.caption(
            "重新学习时 Tutor 会根据 Skill 自动调整讲解方式，"
            "并生成一套新的掌握度测验。"
        )


        st.divider()


        # =================================================
        # 主动跳过
        # =================================================

        if not (
            st.session_state
            .confirm_skip_topic
        ):

            if st.button(
                "⏭️ 暂时跳过，进入下一学习内容",
                use_container_width=True,
                key="skip_topic_button"
            ):

                st.session_state.confirm_skip_topic = (
                    True
                )

                st.rerun()


        else:

            st.warning(
                f"当前成绩：{score} / 100\n\n"
                "当前知识点还没有达到掌握标准。\n\n"
                "如果选择继续：\n"
                "- 当前成绩会保留\n"
                "- 当前薄弱点会保留\n"
                "- 不会标记为已掌握\n"
                "- Planner 未来仍可以重新推荐该知识点"
            )


            cancel_col, skip_col = (
                st.columns(2)
            )


            with cancel_col:

                if st.button(
                    "取消",
                    key="cancel_skip_button",
                    use_container_width=True
                ):

                    st.session_state.confirm_skip_topic = (
                        False
                    )

                    st.rerun()


            with skip_col:

                if st.button(
                    "确认进入下一学习内容",
                    type="primary",
                    key="confirm_skip_button",
                    use_container_width=True
                ):

                    update_latest_record_action(
                        topic=current_topic,
                        new_action="user_skip",
                        original_action=action
                    )


                    skip_profile = (
                        user_profile
                        +
                        f"""

==============================
用户主动暂时跳过
==============================

当前知识点：

{current_topic}


成绩：

{score}


薄弱点：

{weak_points}


规则：

1. 当前知识点仍然视为未完全掌握。
2. 本轮不要立即再次返回完全相同的知识点。
3. 规划新的学习内容。
4. 当前薄弱点继续保留在 Memory。
5. 未来适当时可以再次回到当前知识点。
"""
                    )


                    with st.spinner(
                        "Planner 正在规划新的学习内容..."
                    ):

                        new_plan = (
                            planner_agent(
                                user_profile=skip_profile,
                                progress=load_progress(),
                                career_goal=career_goal
                            )
                        )


                    if "error" in new_plan:

                        st.error(
                            str(new_plan)
                        )

                    else:

                        st.session_state.plan = (
                            new_plan
                        )

                        st.session_state.lesson = None
                        st.session_state.evaluation = None

                        st.session_state.confirm_skip_topic = False

                        st.rerun()


    st.info(
        "本轮结果已经保存到长期学习 Memory。"
        "Planner 会继续结合 Global AI 课程要求、"
        "当前能力值、学习趋势和薄弱点调整学习路径。"
    )
