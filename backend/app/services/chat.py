import re
import json

import ollama

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis import Analysis
from app.models.dataset import Dataset


# ============================================================
# Ollama Client
# ============================================================

client = ollama.Client(
    host=settings.OLLAMA_BASE_URL
)


# ============================================================
# Dataset Context
# ============================================================

def get_dataset_context(
    db: Session,
    dataset_id: int,
    user_id: int,
):
    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.id == dataset_id,
            Dataset.owner_id == user_id,
        )
        .first()
    )

    if dataset is None:
        return None

    analysis = (
        db.query(Analysis)
        .filter(
            Analysis.dataset_id == dataset_id,
        )
        .first()
    )

    return {
        "dataset": dataset,
        "analysis": analysis,
    }


# ============================================================
# Helpers
# ============================================================

def normalize_question(question: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        question.lower().strip(),
    )


def get_total_missing_values(analysis) -> int:
    if not analysis or not analysis.summary:
        return 0

    summary = analysis.summary

    if isinstance(summary, dict):
        return int(
            summary.get("missing_cells", 0) or 0
        )

    return 0


def get_duplicate_count(analysis) -> int:
    if not analysis or not analysis.duplicates:
        return 0

    duplicates = analysis.duplicates

    if isinstance(duplicates, dict):
        return int(
            duplicates.get("count", 0) or 0
        )

    return 0


# ============================================================
# Extract Column Names
# ============================================================

def get_column_names(analysis) -> list[str]:
    """
    Safely extract column names from column_info.
    Supports several possible JSON structures.
    """

    if not analysis or not analysis.column_info:
        return []

    column_info = analysis.column_info

    # --------------------------------------------------------
    # List format
    #
    # [
    #   {"name": "age", ...},
    #   {"name": "salary", ...}
    # ]
    # --------------------------------------------------------

    if isinstance(column_info, list):

        result = []

        for item in column_info:

            if isinstance(item, dict):

                name = (
                    item.get("name")
                    or item.get("column")
                    or item.get("column_name")
                )

                if name:
                    result.append(str(name))

        return result

    # --------------------------------------------------------
    # Dictionary format
    #
    # {
    #   "age": {...},
    #   "salary": {...}
    # }
    # --------------------------------------------------------

    if isinstance(column_info, dict):
        return [
            str(key)
            for key in column_info.keys()
        ]

    return []


# ============================================================
# Find Column In Question
# ============================================================

def find_column_in_question(
    question: str,
    analysis,
) -> str | None:

    q = normalize_question(question)

    columns = get_column_names(analysis)

    # Longest first prevents partial matches.
    columns = sorted(
        columns,
        key=len,
        reverse=True,
    )

    for column in columns:

        if column.lower() in q:
            return column

    return None


# ============================================================
# Correlation Context
# ============================================================

def get_correlation_context(
    question: str,
    analysis,
) -> dict | None:

    if not analysis or not analysis.correlations:
        return None

    q = normalize_question(question)

    correlation_keywords = [
        "correlation",
        "correlations",
        "relationship",
        "relationships",
        "related",
        "relation",
        "associated",
        "association",
    ]

    if not any(
        keyword in q
        for keyword in correlation_keywords
    ):
        return None

    correlations = analysis.correlations

    # --------------------------------------------------------
    # Make sure correlations is a dictionary
    # --------------------------------------------------------

    if not isinstance(correlations, dict):
        return {
            "type": "all",
            "values": correlations,
        }

    # --------------------------------------------------------
    # Find mentioned columns
    # --------------------------------------------------------

    mentioned_columns = []

    for column in correlations.keys():

        if str(column).lower() in q:
            mentioned_columns.append(
                str(column)
            )

    # --------------------------------------------------------
    # Specific pair
    # --------------------------------------------------------

    if len(mentioned_columns) >= 2:

        first = mentioned_columns[0]
        second = mentioned_columns[1]

        first_values = correlations.get(
            first,
            {},
        )

        if isinstance(first_values, dict):

            value = first_values.get(
                second
            )

            if value is not None:

                return {
                    "type": "pair",
                    "first": first,
                    "second": second,
                    "value": value,
                }

        # Try reverse direction
        second_values = correlations.get(
            second,
            {},
        )

        if isinstance(second_values, dict):

            value = second_values.get(
                first
            )

            if value is not None:

                return {
                    "type": "pair",
                    "first": first,
                    "second": second,
                    "value": value,
                }

    # --------------------------------------------------------
    # Specific column
    # --------------------------------------------------------

    if len(mentioned_columns) == 1:

        column = mentioned_columns[0]

        values = correlations.get(
            column,
            {},
        )

        if isinstance(values, dict):

            relevant = {
                str(key): value
                for key, value in values.items()
                if str(key) != column
                and value is not None
            }

            return {
                "type": "column",
                "column": column,
                "values": relevant,
            }

    # --------------------------------------------------------
    # General correlation question
    # --------------------------------------------------------

    return {
        "type": "all",
        "values": correlations,
    }


# ============================================================
# Outlier Context
# ============================================================

def get_outlier_context(
    question: str,
    analysis,
) -> dict | None:

    if not analysis or not analysis.outliers:
        return None

    q = normalize_question(question)

    outlier_keywords = [
        "outlier",
        "outliers",
        "unusual value",
        "unusual values",
        "anomaly",
        "anomalies",
    ]

    if not any(
        keyword in q
        for keyword in outlier_keywords
    ):
        return None

    outliers = analysis.outliers

    # --------------------------------------------------------
    # Specific column
    # --------------------------------------------------------

    column = find_column_in_question(
        question,
        analysis,
    )

    if (
        column
        and isinstance(outliers, dict)
        and column in outliers
    ):

        return {
            "type": "column",
            "column": column,
            "count": outliers[column],
        }

    # --------------------------------------------------------
    # All outliers
    # --------------------------------------------------------

    return {
        "type": "all",
        "values": outliers,
    }


# ============================================================
# Column Statistics
# ============================================================

def get_column_statistics_context(
    question: str,
    analysis,
) -> dict | None:

    if not analysis or not analysis.statistics:
        return None

    column = find_column_in_question(
        question,
        analysis,
    )

    if not column:
        return None

    q = normalize_question(question)

    statistic_keywords = [
        "mean",
        "average",
        "median",
        "minimum",
        "maximum",
        "max",
        "min",
        "standard deviation",
        "std",
        "statistics",
        "statistic",
        "distribution",
    ]

    if not any(
        keyword in q
        for keyword in statistic_keywords
    ):
        return None

    statistics = analysis.statistics

    if not isinstance(statistics, dict):
        return None

    column_statistics = statistics.get(
        column
    )

    if column_statistics is None:
        return None

    return {
        "column": column,
        "statistics": column_statistics,
    }


# ============================================================
# Fast Deterministic Answers
# ============================================================

def generate_fast_answer(
    question: str,
    dataset,
    analysis,
) -> str | None:

    q = normalize_question(question)

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    if (
        "missing" in q
        or "null" in q
        or "empty value" in q
        or "empty values" in q
    ):

        total_missing = get_total_missing_values(
            analysis
        )

        return (
            f"The dataset contains "
            f"{total_missing} missing values."
        )

    # --------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------

    if (
        "duplicate" in q
        or "duplicated" in q
        or "repeated rows" in q
    ):

        duplicate_count = get_duplicate_count(
            analysis
        )

        if duplicate_count == 0:
            return (
                "The dataset does not contain "
                "any duplicate rows."
            )

        return (
            f"The dataset contains "
            f"{duplicate_count} duplicate rows."
        )

    # --------------------------------------------------------
    # Rows
    # --------------------------------------------------------

    if (
        ("how many" in q or "number of" in q)
        and "row" in q
    ):

        return (
            f"The dataset contains "
            f"{dataset.rows} rows."
        )

    # --------------------------------------------------------
    # Columns
    # --------------------------------------------------------

    if (
        ("how many" in q or "number of" in q)
        and (
            "column" in q
            or "feature" in q
        )
    ):

        return (
            f"The dataset contains "
            f"{dataset.columns} columns."
        )

    # --------------------------------------------------------
    # Dataset name
    # --------------------------------------------------------

    if (
        "dataset name" in q
        or "file name" in q
        or "filename" in q
    ):

        return (
            f"The dataset filename is "
            f"{dataset.original_filename}."
        )

    # --------------------------------------------------------
    # Quality
    # --------------------------------------------------------

    if (
        "quality score" in q
        or "data quality" in q
        or q == "quality"
    ):

        return (
            f"The dataset has a data quality "
            f"score of {analysis.quality_score}/100."
        )

    # --------------------------------------------------------
    # Memory
    # --------------------------------------------------------

    if (
        "memory" in q
        and (
            "usage" in q
            or "size" in q
        )
    ):

        memory_kb = 0

        if isinstance(
            analysis.summary,
            dict,
        ):

            memory_kb = (
                analysis.summary.get(
                    "memory_usage",
                    0,
                )
                / 1024
            )

        return (
            f"The dataset uses approximately "
            f"{memory_kb:.2f} KB of memory."
        )

    return None


# ============================================================
# Build Focused Prompt
# ============================================================

def build_focused_prompt(
    question: str,
    dataset,
    analysis,
) -> str:

    # ========================================================
    # Correlation
    # ========================================================

    correlation_context = get_correlation_context(
        question,
        analysis,
    )

    if correlation_context:

        print(
            "CHAT: Using focused correlation context."
        )

        return f"""
You are InsightForge AI, an AI data analyst.

The user is asking about correlations.

Use ONLY the correlation data provided below.

Do not calculate or invent any values.

Correlation data:
{json.dumps(
    correlation_context,
    indent=2,
    default=str,
)}

Dataset:
{dataset.original_filename}

User question:
{question}

Explain the correlation in simple language.

If the correlation value is positive:
explain that the variables tend to increase together.

If the correlation value is negative:
explain that one tends to increase when the other decreases.

If the value is close to zero:
explain that there is little linear relationship.

Do not claim causation.

Keep the answer concise.
"""


    # ========================================================
    # Outliers
    # ========================================================

    outlier_context = get_outlier_context(
        question,
        analysis,
    )

    if outlier_context:

        print(
            "CHAT: Using focused outlier context."
        )

        return f"""
You are InsightForge AI, an AI data analyst.

The user is asking about outliers.

Use ONLY the outlier information provided below.

Do not invent values.

Outlier data:
{json.dumps(
    outlier_context,
    indent=2,
    default=str,
)}

Dataset:
{dataset.original_filename}

User question:
{question}

Explain which columns contain outliers
and how many outliers were detected.

If the provided data only contains counts,
do not invent the actual row values.

Keep the answer concise and useful.
"""


    # ========================================================
    # Column statistics
    # ========================================================

    statistics_context = (
        get_column_statistics_context(
            question,
            analysis,
        )
    )

    if statistics_context:

        print(
            "CHAT: Using focused column statistics."
        )

        return f"""
You are InsightForge AI, an AI data analyst.

Answer the user's question using ONLY
the statistics provided below.

Do not invent statistics.

Statistics:
{json.dumps(
    statistics_context,
    indent=2,
    default=str,
)}

Dataset:
{dataset.original_filename}

User question:
{question}

Explain the result in simple language.

Keep the answer concise.
"""


    # ========================================================
    # General dataset question
    # ========================================================

    print(
        "CHAT: Using general dataset context."
    )

    return f"""
You are InsightForge AI, an AI data analyst.

Answer the user's question using ONLY
the dataset analysis provided below.

Do not invent statistics or facts.

If the information needed to answer the question
is not available, clearly say so.

Explain technical concepts in simple language.

Keep the answer concise and useful.

DATASET
-------
Filename: {dataset.original_filename}
Rows: {dataset.rows}
Columns: {dataset.columns}

SUMMARY
-------
{json.dumps(
    analysis.summary,
    indent=2,
    default=str,
)}

COLUMN INFORMATION
------------------
{json.dumps(
    analysis.column_info,
    indent=2,
    default=str,
)}

STATISTICS
----------
{json.dumps(
    analysis.statistics,
    indent=2,
    default=str,
)}

MISSING VALUES
--------------
{json.dumps(
    analysis.missing_values,
    indent=2,
    default=str,
)}

DUPLICATES
----------
{json.dumps(
    analysis.duplicates,
    indent=2,
    default=str,
)}

CORRELATIONS
------------
{json.dumps(
    analysis.correlations,
    indent=2,
    default=str,
)}

OUTLIERS
--------
{json.dumps(
    analysis.outliers,
    indent=2,
    default=str,
)}

QUALITY SCORE
-------------
{analysis.quality_score}/100

ANALYSIS SUMMARY
----------------
{analysis.summary_text}

USER QUESTION
-------------
{question}
"""


# ============================================================
# Generate Chat Answer
# ============================================================

def generate_chat_answer(
    question: str,
    context: dict,
) -> str:

    dataset = context["dataset"]
    analysis = context["analysis"]

    if analysis is None:
        return (
            "I found the dataset, but its analysis "
            "is not available yet."
        )

    # ========================================================
    # Fast answer
    # ========================================================

    fast_answer = generate_fast_answer(
        question=question,
        dataset=dataset,
        analysis=analysis,
    )

    if fast_answer is not None:

        print(
            "CHAT: Answered directly from analysis."
        )

        return fast_answer

    # ========================================================
    # Focused prompt
    # ========================================================

    prompt = build_focused_prompt(
        question=question,
        dataset=dataset,
        analysis=analysis,
    )

    # ========================================================
    # Ollama
    # ========================================================

    try:

        print(
            "CHAT: Sending question to Ollama..."
        )

        response = client.chat(
            model=settings.OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        answer = response["message"]["content"]

        print(
            "CHAT: Ollama response received."
        )

        return answer.strip()

    except Exception as error:

        print(
            "Ollama error:",
            error,
        )

        return (
            "I'm unable to connect to the local AI "
            "model right now. Please make sure "
            "Ollama is running."
        )