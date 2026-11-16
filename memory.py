import json
import os
from datetime import datetime
from collections import Counter


# =========================================================
# 文件路径
# =========================================================

PROGRESS_FILE = "progress.json"
PROFILE_FILE = "student_profile.json"


# =========================================================
# 通用 JSON
# =========================================================

def _load_json(file_path, default):

    if not os.path.exists(file_path):
        return default

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except (
        json.JSONDecodeError,
        OSError
    ):

        return default


def _save_json(file_path, data):

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


# =========================================================
# 读取学习历史
# =========================================================

def load_progress():

    return _load_json(
        PROGRESS_FILE,
        {}
    )


# =========================================================
# 获取某知识点尝试次数
# =========================================================

def get_topic_attempt_count(topic):

    progress = load_progress()

    history = (
        progress
        .get(topic, {})
        .get(
            "history",
            []
        )
    )

    return len(history)


# =========================================================
# 获取某知识点最新记录
# =========================================================

def get_latest_topic_record(topic):

    progress = load_progress()

    history = (
        progress
        .get(topic, {})
        .get(
            "history",
            []
        )
    )

    if not history:
        return None

    return history[-1]


# =========================================================
# 保存学习结果
# =========================================================

def save_progress(
        topic,
        evaluation,
        category=None
):

    progress = load_progress()


    if topic not in progress:

        progress[topic] = {
            "history": []
        }


    if "history" not in progress[topic]:

        progress[
            topic
        ][
            "history"
        ] = []


    # =====================================================
    # 当前尝试次数
    # =====================================================

    attempt_number = (
        len(
            progress[
                topic
            ][
                "history"
            ]
        )
        + 1
    )


    now = datetime.now()


    record = {

        # 完整日期时间
        "datetime":
            now.strftime(
                "%Y-%m-%d %H:%M"
            ),

        # 日期
        "date":
            now.strftime(
                "%Y-%m-%d"
            ),

        # 时间
        "time":
            now.strftime(
                "%H:%M:%S"
            ),

        # 第几次尝试
        "attempt":
            attempt_number,

        # 所属类别
        "category":
            category,

        # 成绩
        "score":
            evaluation.get(
                "score",
                0
            ),

        # 薄弱点
        "weak_points":
            evaluation.get(
                "weak_points",
                []
            ),

        # 评价
        "feedback":
            evaluation.get(
                "feedback",
                ""
            ),

        # 下一步
        "action":
            evaluation.get(
                "action",
                ""
            ),

        # 如果用户主动跳过
        # 保存原来的系统建议
        "original_action":
            evaluation.get(
                "original_action"
            )
    }


    progress[
        topic
    ][
        "history"
    ].append(
        record
    )


    _save_json(
        PROGRESS_FILE,
        progress
    )


# =========================================================
# 修改某知识点最新记录 action
#
# 用于：
# 用户主动选择跳过
# =========================================================

def update_latest_record_action(
        topic,
        new_action,
        original_action=None
):

    progress = load_progress()


    if topic not in progress:
        return False


    history = (
        progress[
            topic
        ].get(
            "history",
            []
        )
    )


    if not history:
        return False


    latest = history[-1]


    if original_action is None:

        original_action = (
            latest.get(
                "action"
            )
        )


    latest[
        "original_action"
    ] = original_action


    latest[
        "action"
    ] = new_action


    _save_json(
        PROGRESS_FILE,
        progress
    )


    return True


# =========================================================
# 获取全部学习记录
#
# 把：
#
# topic
#   → history
#
# 展平成：
#
# [
#   record,
#   record,
#   ...
# ]
# =========================================================

def get_learning_records():

    progress = load_progress()

    records = []


    for topic, topic_data in (
        progress.items()
    ):

        history = (
            topic_data.get(
                "history",
                []
            )
        )


        for index, record in enumerate(
            history,
            start=1
        ):

            # =================================================
            # 兼容旧记录
            # =================================================

            record_datetime = (
                record.get(
                    "datetime"
                )
            )


            date = (
                record.get(
                    "date",
                    ""
                )
            )


            time = (
                record.get(
                    "time",
                    ""
                )
            )


            if not record_datetime:

                if date and time:

                    record_datetime = (
                        f"{date} "
                        f"{time[:5]}"
                    )

                elif date:

                    record_datetime = date

                else:

                    record_datetime = (
                        "未知时间"
                    )


            # =================================================
            # 如果旧记录没有 date
            # 从 datetime 提取
            # =================================================

            if not date:

                if (
                    record_datetime
                    and
                    record_datetime
                    != "未知时间"
                ):

                    date = (
                        record_datetime[:10]
                    )

                else:

                    date = "未知日期"


            records.append(
                {
                    "topic":
                        topic,

                    "datetime":
                        record_datetime,

                    "date":
                        date,

                    "time":
                        time,

                    "attempt":
                        record.get(
                            "attempt",
                            index
                        ),

                    "category":
                        record.get(
                            "category"
                        ),

                    "score":
                        record.get(
                            "score",
                            0
                        ),

                    "weak_points":
                        record.get(
                            "weak_points",
                            []
                        ),

                    "feedback":
                        record.get(
                            "feedback",
                            ""
                        ),

                    "action":
                        record.get(
                            "action",
                            ""
                        ),

                    "original_action":
                        record.get(
                            "original_action"
                        )
                }
            )


    # =====================================================
    # 最新记录放前面
    # =====================================================

    records.sort(
        key=lambda x: (
            x.get(
                "datetime",
                ""
            )
        ),
        reverse=True
    )


    return records


# =========================================================
# 最近 N 条
# =========================================================

def get_recent_learning_records(
        limit=5
):

    return (
        get_learning_records()
        [:limit]
    )


# =========================================================
# 按日期分组
#
# 返回：
#
# {
#   "2026-10-28": [...],
#   "2026-10-27": [...]
# }
# =========================================================

def get_learning_records_by_date():

    records = (
        get_learning_records()
    )


    daily_records = {}


    for record in records:

        date = (
            record.get(
                "date"
            )
        )


        if not date:

            record_datetime = (
                record.get(
                    "datetime",
                    ""
                )
            )


            if (
                record_datetime
                and
                record_datetime
                != "未知时间"
            ):

                date = (
                    record_datetime[:10]
                )

            else:

                date = "未知日期"


        if date not in daily_records:

            daily_records[
                date
            ] = []


        daily_records[
            date
        ].append(
            record
        )


    # =====================================================
    # 日期从新到旧
    # =====================================================

    daily_records = dict(
        sorted(
            daily_records.items(),
            key=lambda item: (
                item[0]
            ),
            reverse=True
        )
    )


    return daily_records


# =========================================================
# 每日学习总结
# =========================================================

def get_daily_summary(date):

    daily_records = (
        get_learning_records_by_date()
    )


    records = (
        daily_records.get(
            date,
            []
        )
    )


    if not records:

        return {
            "date": date,
            "study_count": 0,
            "average_score": 0,
            "topics": [],
            "mastered_topics": [],
            "unfinished_topics": [],
            "weak_points": []
        }


    scores = []

    topics = []

    mastered_topics = []

    unfinished_topics = []

    all_weak_points = []


    for record in records:

        topic = (
            record.get(
                "topic",
                ""
            )
        )


        score = (
            record.get(
                "score",
                0
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


        if isinstance(
            score,
            (int, float)
        ):

            scores.append(
                score
            )


        if (
            topic
            and
            topic not in topics
        ):

            topics.append(
                topic
            )


        if (
            score >= 80
            or
            action == "next_topic"
        ):

            if (
                topic
                and
                topic not in mastered_topics
            ):

                mastered_topics.append(
                    topic
                )

        else:

            if (
                topic
                and
                topic not in unfinished_topics
            ):

                unfinished_topics.append(
                    topic
                )


        for point in weak_points:

            if point:

                all_weak_points.append(
                    str(point)
                )


    average_score = (

        sum(scores)
        / len(scores)

        if scores

        else 0
    )


    # =====================================================
    # 薄弱点出现次数排序
    # =====================================================

    weakness_counter = Counter(
        all_weak_points
    )


    weakness_rank = [
        {
            "weak_point": point,
            "count": count
        }

        for point, count
        in weakness_counter.most_common()
    ]


    return {

        "date":
            date,

        "study_count":
            len(records),

        "average_score":
            round(
                average_score,
                1
            ),

        "topics":
            topics,

        "mastered_topics":
            mastered_topics,

        "unfinished_topics":
            unfinished_topics,

        "weak_points":
            weakness_rank
    }


# =========================================================
# 获取全部反复薄弱点
# =========================================================

def get_recurring_weak_points(
        limit=10
):

    records = (
        get_learning_records()
    )


    all_weak_points = []


    for record in records:

        weak_points = (
            record.get(
                "weak_points",
                []
            )
        )


        for point in weak_points:

            if point:

                all_weak_points.append(
                    str(point)
                )


    counter = Counter(
        all_weak_points
    )


    return [
        {
            "weak_point": point,
            "count": count
        }

        for point, count
        in counter.most_common(
            limit
        )
    ]


# =========================================================
# 学习趋势
#
# 使用最近 N 次成绩判断
# =========================================================

def get_learning_trend(
        limit=6
):

    records = (
        get_learning_records()
    )


    # =====================================================
    # get_learning_records 是新 → 旧
    # 趋势计算需要旧 → 新
    # =====================================================

    recent_records = (
        records[:limit]
    )


    recent_records = list(
        reversed(
            recent_records
        )
    )


    scores = []


    for record in recent_records:

        score = (
            record.get(
                "score"
            )
        )


        if isinstance(
            score,
            (int, float)
        ):

            scores.append(
                score
            )


    if len(scores) < 2:

        return {
            "trend": "insufficient_data",
            "trend_text": "数据不足",
            "scores": scores
        }


    # =====================================================
    # 前半部分 vs 后半部分
    # =====================================================

    middle = (
        len(scores)
        // 2
    )


    if middle == 0:

        return {
            "trend": "insufficient_data",
            "trend_text": "数据不足",
            "scores": scores
        }


    first_half = (
        scores[:middle]
    )


    second_half = (
        scores[middle:]
    )


    first_average = (
        sum(first_half)
        / len(first_half)
    )


    second_average = (
        sum(second_half)
        / len(second_half)
    )


    difference = (
        second_average
        - first_average
    )


    # =====================================================
    # 趋势判断
    # =====================================================

    if difference >= 5:

        trend = "improving"

        trend_text = "正在进步"

    elif difference <= -5:

        trend = "declining"

        trend_text = "近期下降"

    else:

        trend = "stable"

        trend_text = "基本稳定"


    return {

        "trend":
            trend,

        "trend_text":
            trend_text,

        "scores":
            scores,

        "first_average":
            round(
                first_average,
                1
            ),

        "second_average":
            round(
                second_average,
                1
            ),

        "difference":
            round(
                difference,
                1
            )
    }


# =========================================================
# 给 Planner 使用的 Memory 摘要
# =========================================================

def get_memory_summary():

    records = (
        get_learning_records()
    )


    daily_records = (
        get_learning_records_by_date()
    )


    weak_points = (
        get_recurring_weak_points(
            limit=5
        )
    )


    trend = (
        get_learning_trend()
    )


    return {

        "total_learning_records":
            len(records),

        "learning_days":
            len(daily_records),

        "recent_records":
            records[:5],

        "recurring_weak_points":
            weak_points,

        "learning_trend":
            trend
    }


# =========================================================
# 学生自评
# =========================================================

def load_self_assessment():

    return _load_json(
        PROFILE_FILE,
        {}
    )


def save_self_assessment(
        profile
):

    _save_json(
        PROFILE_FILE,
        profile
    )


# =========================================================
# 清空学习历史
# =========================================================

def clear_progress():

    _save_json(
        PROGRESS_FILE,
        {}
    )


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    print(
        "\n=== 按日期学习记录 ==="
    )

    print(
        json.dumps(
            get_learning_records_by_date(),
            ensure_ascii=False,
            indent=2
        )
    )


    print(
        "\n=== 学习趋势 ==="
    )

    print(
        json.dumps(
            get_learning_trend(),
            ensure_ascii=False,
            indent=2
        )
    )


    print(
        "\n=== Memory摘要 ==="
    )

    print(
        json.dumps(
            get_memory_summary(),
            ensure_ascii=False,
            indent=2
        )
    )