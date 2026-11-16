import os
import json
import logging
import re

from pypdf import PdfReader


# =========================================================
# 关闭 pypdf 大量警告
# =========================================================

logging.getLogger(
    "pypdf"
).setLevel(
    logging.ERROR
)


# =========================================================
# 目录
# =========================================================

COURSE_DATA_DIR = "course_data"

USER_MATERIAL_DIR = "user_materials"

CACHE_DIR = "rag_cache"

CACHE_FILE = os.path.join(
    CACHE_DIR,
    "course_pdf_cache.json"
)


# =========================================================
# 自动创建
# =========================================================

os.makedirs(
    COURSE_DATA_DIR,
    exist_ok=True
)

os.makedirs(
    USER_MATERIAL_DIR,
    exist_ok=True
)

os.makedirs(
    CACHE_DIR,
    exist_ok=True
)


# =========================================================
# 简单同义词
# =========================================================

TOPIC_SYNONYMS = {

    "逻辑回归": [
        "logistic regression",
        "sigmoid",
        "classification",
        "classifier",
        "linear classifier",
        "binary classification",
        "log odds"
    ],

    "朴素贝叶斯": [
        "naive bayes",
        "bayes",
        "conditional probability",
        "prior",
        "likelihood",
        "posterior"
    ],

    "交叉熵": [
        "cross entropy",
        "cross-entropy",
        "entropy",
        "loss",
        "negative log likelihood"
    ],

    "熵与交叉熵": [
        "entropy",
        "cross entropy",
        "cross-entropy",
        "information"
    ],

    "条件概率": [
        "conditional probability",
        "probability",
        "bayes"
    ],

    "贝叶斯公式": [
        "bayes theorem",
        "bayes rule",
        "posterior",
        "prior",
        "likelihood"
    ],

    "Precision / Recall / F1": [
        "precision",
        "recall",
        "f1",
        "f-score",
        "confusion matrix"
    ],

    "Perplexity": [
        "perplexity",
        "language model",
        "cross entropy"
    ],

    "N-gram": [
        "n-gram",
        "ngram",
        "language model"
    ],

    "Embedding": [
        "embedding",
        "word embedding",
        "vector representation"
    ],

    "Attention": [
        "attention",
        "self-attention",
        "query",
        "key",
        "value"
    ],

    "Transformer": [
        "transformer",
        "attention",
        "self-attention",
        "positional encoding"
    ],

    "RAG": [
        "retrieval augmented generation",
        "retrieval",
        "embedding",
        "vector database"
    ],

    "ReAct": [
        "react",
        "reasoning",
        "acting",
        "agent"
    ],

    "Function Calling": [
        "function calling",
        "function call",
        "tool call"
    ],

    "Tool Calling": [
        "tool calling",
        "tool call",
        "function calling"
    ],

    "Agent Loop": [
        "agent loop",
        "agent",
        "observe",
        "action",
        "reasoning"
    ],

    "Memory": [
        "memory",
        "long-term memory",
        "short-term memory"
    ]
}


# =========================================================
# 读取 JSON
# =========================================================

def _load_json(
        file_path,
        default
):

    if not os.path.exists(
        file_path
    ):
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


# =========================================================
# 保存 JSON
# =========================================================

def _save_json(
        file_path,
        data
):

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# 清理文本
# =========================================================

def _clean_text(text):

    if not text:
        return ""


    text = text.replace(
        "\x00",
        " "
    )


    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )


    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )


    return text.strip()


# =========================================================
# PDF信息
# =========================================================

def _get_file_signature(
        file_path
):

    try:

        stat = os.stat(
            file_path
        )


        return {
            "size":
                stat.st_size,

            "mtime_ns":
                stat.st_mtime_ns
        }


    except OSError:

        return {
            "size": 0,
            "mtime_ns": 0
        }


# =========================================================
# PDF解析
# =========================================================

def _extract_pdf_pages(
        file_path
):

    pages = []


    try:

        reader = PdfReader(
            file_path,
            strict=False
        )


        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            try:

                text = (
                    page.extract_text()
                    or ""
                )


                text = (
                    _clean_text(
                        text
                    )
                )


                if text:

                    pages.append(
                        {
                            "page":
                                page_number,

                            "text":
                                text
                        }
                    )


            except Exception as e:

                print(
                    f"读取页面失败："
                    f"{os.path.basename(file_path)} "
                    f"第{page_number}页："
                    f"{e}"
                )


    except Exception as e:

        print(
            f"PDF解析失败："
            f"{file_path}："
            f"{e}"
        )


    return pages


# =========================================================
# 查找全部PDF
# =========================================================

def _get_all_pdf_files():

    files = []


    # =====================================================
    # 官方课程资料
    # =====================================================

    if os.path.exists(
        COURSE_DATA_DIR
    ):

        for filename in os.listdir(
            COURSE_DATA_DIR
        ):

            if filename.lower().endswith(
                ".pdf"
            ):

                files.append(
                    {
                        "filename":
                            filename,

                        "path":
                            os.path.join(
                                COURSE_DATA_DIR,
                                filename
                            ),

                        "source_type":
                            "course"
                    }
                )


    # =====================================================
    # 用户资料
    # =====================================================

    if os.path.exists(
        USER_MATERIAL_DIR
    ):

        for filename in os.listdir(
            USER_MATERIAL_DIR
        ):

            if filename.lower().endswith(
                ".pdf"
            ):

                files.append(
                    {
                        "filename":
                            filename,

                        "path":
                            os.path.join(
                                USER_MATERIAL_DIR,
                                filename
                            ),

                        "source_type":
                            "user"
                    }
                )


    return files


# =========================================================
# Cache Key
#
# 避免 course_data 和 user_materials
# 有相同文件名
# =========================================================

def _make_cache_key(
        source_type,
        filename
):

    return (
        f"{source_type}::{filename}"
    )


# =========================================================
# 更新缓存
# =========================================================

def build_or_update_cache():

    cache = (
        _load_json(
            CACHE_FILE,
            {}
        )
    )


    current_files = (
        _get_all_pdf_files()
    )


    current_keys = set()


    # =====================================================
    # 新增/更新
    # =====================================================

    for file_info in current_files:

        filename = (
            file_info[
                "filename"
            ]
        )


        path = (
            file_info[
                "path"
            ]
        )


        source_type = (
            file_info[
                "source_type"
            ]
        )


        cache_key = (
            _make_cache_key(
                source_type,
                filename
            )
        )


        current_keys.add(
            cache_key
        )


        signature = (
            _get_file_signature(
                path
            )
        )


        old_data = (
            cache.get(
                cache_key
            )
        )


        # =================================================
        # 文件未改变
        # =================================================

        if old_data:

            old_signature = (
                old_data.get(
                    "signature",
                    {}
                )
            )


            if (
                old_signature.get(
                    "size"
                )
                ==
                signature.get(
                    "size"
                )

                and

                old_signature.get(
                    "mtime_ns"
                )
                ==
                signature.get(
                    "mtime_ns"
                )
            ):

                continue


        # =================================================
        # 文件新上传或被修改
        # =================================================

        print(
            f"正在解析PDF："
            f"{filename}"
        )


        pages = (
            _extract_pdf_pages(
                path
            )
        )


        cache[
            cache_key
        ] = {

            "filename":
                filename,

            "source_type":
                source_type,

            "signature":
                signature,

            "pages":
                pages
        }


    # =====================================================
    # 删除已经不存在的PDF
    # =====================================================

    cached_keys = list(
        cache.keys()
    )


    for cache_key in cached_keys:

        if cache_key not in current_keys:

            del cache[
                cache_key
            ]


    _save_json(
        CACHE_FILE,
        cache
    )


    return cache


# =========================================================
# 强制重建
# =========================================================

def rebuild_cache():

    if os.path.exists(
        CACHE_FILE
    ):

        try:

            os.remove(
                CACHE_FILE
            )

        except OSError:

            pass


    return build_or_update_cache()


# =========================================================
# 生成检索关键词
# =========================================================

def _build_keywords(
        topic
):

    topic = str(
        topic
    ).strip()


    keywords = [
        topic
    ]


    topic_lower = (
        topic.lower()
    )


    # =====================================================
    # 完整命中
    # =====================================================

    for key, synonyms in (
        TOPIC_SYNONYMS.items()
    ):

        if (
            key.lower()
            in topic_lower

            or

            topic_lower
            in key.lower()
        ):

            keywords.extend(
                synonyms
            )


    # =====================================================
    # 如果 topic 自身包含某个知识词
    # =====================================================

    for key, synonyms in (
        TOPIC_SYNONYMS.items()
    ):

        if key.lower() in topic_lower:

            keywords.append(
                key
            )

            keywords.extend(
                synonyms
            )


    # =====================================================
    # 去重
    # =====================================================

    unique_keywords = []


    for keyword in keywords:

        keyword = str(
            keyword
        ).strip()


        if (
            keyword

            and

            keyword.lower()
            not in [
                x.lower()
                for x
                in unique_keywords
            ]
        ):

            unique_keywords.append(
                keyword
            )


    return unique_keywords


# =========================================================
# 页面相关性评分
# =========================================================

def _score_text(
        text,
        keywords
):

    text_lower = (
        text.lower()
    )


    score = 0

    matched = []


    for keyword in keywords:

        keyword_lower = (
            keyword.lower()
        )


        count = (
            text_lower.count(
                keyword_lower
            )
        )


        if count > 0:

            matched.append(
                keyword
            )


            # 主关键词/短语命中
            score += (
                min(
                    count,
                    5
                )
                * 3
            )


    return (
        score,
        matched
    )


# =========================================================
# 取上下文
# =========================================================

def _extract_context(
        text,
        matched_keywords,
        context_lines=5
):

    if not text:

        return ""


    lines = (
        text.splitlines()
    )


    if not lines:

        return text[:3000]


    matched_indexes = []


    for index, line in enumerate(
        lines
    ):

        line_lower = (
            line.lower()
        )


        for keyword in matched_keywords:

            if (
                keyword.lower()
                in line_lower
            ):

                matched_indexes.append(
                    index
                )

                break


    # =====================================================
    # 没找到行
    # =====================================================

    if not matched_indexes:

        return text[:3000]


    # =====================================================
    # 取第一个主要匹配区域
    # =====================================================

    center = (
        matched_indexes[0]
    )


    start = max(
        0,
        center - context_lines
    )


    end = min(
        len(lines),
        center + context_lines + 1
    )


    context = "\n".join(
        lines[
            start:end
        ]
    )


    return (
        _clean_text(
            context
        )
    )


# =========================================================
# RAG检索
#
# interface保持不变：
#
# search_course_material(
#     topic,
#     max_results=3,
#     context_lines=5
# )
# =========================================================

def search_course_material(
        topic,
        max_results=3,
        context_lines=5
):

    # =====================================================
    # 自动更新缓存
    # =====================================================

    cache = (
        build_or_update_cache()
    )


    keywords = (
        _build_keywords(
            topic
        )
    )


    results = []


    # =====================================================
    # 所有PDF页面
    # =====================================================

    for cache_key, document in (
        cache.items()
    ):

        filename = (
            document.get(
                "filename",
                ""
            )
        )


        source_type = (
            document.get(
                "source_type",
                "course"
            )
        )


        pages = (
            document.get(
                "pages",
                []
            )
        )


        for page_data in pages:

            page_number = (
                page_data.get(
                    "page"
                )
            )


            text = (
                page_data.get(
                    "text",
                    ""
                )
            )


            score, matched_keywords = (
                _score_text(
                    text,
                    keywords
                )
            )


            if score <= 0:

                continue


            # =================================================
            # 官方课程资料优先
            # =================================================

            if source_type == "course":

                source_priority = 2

                # 小幅加权
                final_score = (
                    score + 3
                )

            else:

                source_priority = 1

                final_score = score


            context = (
                _extract_context(
                    text=text,

                    matched_keywords=matched_keywords,

                    context_lines=context_lines
                )
            )


            results.append(
                {
                    "filename":
                        filename,

                    "page":
                        page_number,

                    "content":
                        context,

                    "matched_keywords":
                        matched_keywords,

                    "score":
                        final_score,

                    "source_type":
                        source_type,

                    "source_priority":
                        source_priority
                }
            )


    # =====================================================
    # 排序
    #
    # 先看分数
    # 分数接近时官方课程资料优先
    # =====================================================

    results.sort(
        key=lambda item: (
            item.get(
                "score",
                0
            ),

            item.get(
                "source_priority",
                0
            )
        ),
        reverse=True
    )


    # =====================================================
    # 防止全部结果来自同一PDF
    # 稍微增加来源多样性
    # =====================================================

    selected = []

    used_pages = set()


    for result in results:

        unique_key = (
            result.get(
                "source_type"
            ),
            result.get(
                "filename"
            ),
            result.get(
                "page"
            )
        )


        if unique_key in used_pages:

            continue


        selected.append(
            result
        )


        used_pages.add(
            unique_key
        )


        if len(selected) >= max_results:

            break


    return selected


# =========================================================
# 查看当前知识库
# =========================================================

def get_knowledge_base_status():

    cache = (
        build_or_update_cache()
    )


    course_files = []

    user_files = []


    for document in (
        cache.values()
    ):

        filename = (
            document.get(
                "filename",
                ""
            )
        )


        source_type = (
            document.get(
                "source_type"
            )
        )


        if source_type == "course":

            if filename not in course_files:

                course_files.append(
                    filename
                )


        elif source_type == "user":

            if filename not in user_files:

                user_files.append(
                    filename
                )


    return {
        "course_files":
            sorted(
                course_files
            ),

        "user_files":
            sorted(
                user_files
            ),

        "course_count":
            len(
                course_files
            ),

        "user_count":
            len(
                user_files
            )
    }


# =========================================================
# 测试
# =========================================================

if __name__ == "__main__":

    print(
        "=== 知识库状态 ==="
    )


    status = (
        get_knowledge_base_status()
    )


    print(
        json.dumps(
            status,
            ensure_ascii=False,
            indent=2
        )
    )


    print(
        "\n=== 搜索逻辑回归 ==="
    )


    results = (
        search_course_material(
            topic="逻辑回归",
            max_results=5
        )
    )


    print(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2
        )
    )