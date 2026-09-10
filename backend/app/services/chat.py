import re
import json
from typing import Any

from sqlalchemy.orm import Session

from app.services.ai_provider import generate_ai_response
from app.models.analysis import Analysis
from app.models.dataset import Dataset


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
        .order_by(Analysis.id.desc())
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


def safe_number(value: Any) -> float | None:
    """
    Safely convert a value to a number.
    Returns None when conversion is not possible.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_number(value: Any) -> str:
    """
    Format numeric values cleanly.
    """

    number = safe_number(value)

    if number is None:
        return str(value)

    if number.is_integer():
        return str(int(number))

    return f"{number:.4f}".rstrip("0").rstrip(".")


def get_total_missing_values(analysis) -> int:
    if not analysis or not analysis.summary:
        return 0

    summary = analysis.summary

    if isinstance(summary, dict):
        value = (
            summary.get("missing_cells")
            or summary.get("missing_values")
            or summary.get("missing")
            or 0
        )

        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    return 0


def get_duplicate_count(analysis) -> int:
    if not analysis or not analysis.duplicates:
        return 0

    duplicates = analysis.duplicates

    if isinstance(duplicates, dict):
        value = (
            duplicates.get("count")
            or duplicates.get("duplicate_count")
            or 0
        )

        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    return 0


# ============================================================
# Extract Column Names
# ============================================================

def get_column_names(analysis) -> list[str]:
    """
    Safely extract column names from column_info.

    Supports:

    [
        {"name": "age"},
        {"name": "salary"}
    ]

    and:

    {
        "age": {...},
        "salary": {...}
    }
    """

    if not analysis or not analysis.column_info:
        return []

    column_info = analysis.column_info

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


def find_columns_in_question(
    question: str,
    analysis,
) -> list[str]:

    q = normalize_question(question)

    columns = get_column_names(analysis)

    columns = sorted(
        columns,
        key=len,
        reverse=True,
    )

    found = []

    for column in columns:

        if column.lower() in q:
            found.append(column)

    return found


# ============================================================
# Correlation Helpers
# ============================================================

def get_correlation_pairs(
    correlations: Any,
) -> list[dict]:

    """
    Convert a correlation matrix into unique pairs.

    Example:

    {
        "age": {
            "age": 1.0,
            "salary": 0.838
        },
        "salary": {
            "age": 0.838,
            "salary": 1.0
        }
    }

    becomes:

    [
        {
            "first": "age",
            "second": "salary",
            "value": 0.838
        }
    ]
    """

    if not isinstance(correlations, dict):
        return []

    pairs = []
    seen = set()

    for first, values in correlations.items():

        if not isinstance(values, dict):
            continue

        for second, value in values.items():

            if str(first) == str(second):
                continue

            numeric_value = safe_number(value)

            if numeric_value is None:
                continue

            pair_key = frozenset(
                [str(first), str(second)]
            )

            if pair_key in seen:
                continue

            seen.add(pair_key)

            pairs.append(
                {
                    "first": str(first),
                    "second": str(second),
                    "value": numeric_value,
                }
            )

    return pairs


def get_strongest_correlation(
    analysis,
) -> dict | None:

    if not analysis or not analysis.correlations:
        return None

    pairs = get_correlation_pairs(
        analysis.correlations
    )

    if not pairs:
        return None

    return max(
        pairs,
        key=lambda pair: abs(pair["value"]),
    )


def get_weakest_correlation(
    analysis,
) -> dict | None:

    if not analysis or not analysis.correlations:
        return None

    pairs = get_correlation_pairs(
        analysis.correlations
    )

    if not pairs:
        return None

    return min(
        pairs,
        key=lambda pair: abs(pair["value"]),
    )


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

    if not isinstance(correlations, dict):

        return {
            "type": "all",
            "values": correlations,
        }

    mentioned_columns = find_columns_in_question(
        question,
        analysis,
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
# Outlier Helpers
# ============================================================

def get_outlier_counts(
    analysis,
) -> dict[str, int]:

    if not analysis or not analysis.outliers:
        return {}

    outliers = analysis.outliers

    if not isinstance(outliers, dict):
        return {}

    result = {}

    for column, count in outliers.items():

        try:
            result[str(column)] = int(count or 0)
        except (TypeError, ValueError):
            continue

    return result


def get_total_outliers(
    analysis,
) -> int:

    counts = get_outlier_counts(
        analysis
    )

    return sum(counts.values())


def get_strongest_outlier_column(
    analysis,
) -> tuple[str, int] | None:

    counts = get_outlier_counts(
        analysis
    )

    if not counts:
        return None

    return max(
        counts.items(),
        key=lambda item: item[1],
    )


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

    # ========================================================
    # Missing values
    # ========================================================

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

    # ========================================================
    # Duplicate rows
    # ========================================================

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

    # ========================================================
    # Strongest correlation
    # ========================================================

    strongest_correlation_phrases = [
        "strongest correlation",
        "highest correlation",
        "most correlated",
        "strongest relationship",
        "highest relationship",
        "most related",
        "strongest relation",
        "highest relation",
    ]

    if any(
        phrase in q
        for phrase in strongest_correlation_phrases
    ):

        strongest = get_strongest_correlation(
            analysis
        )

        if strongest is None:
            return (
                "No correlation data is available "
                "for this dataset."
            )

        first = strongest["first"]
        second = strongest["second"]
        value = strongest["value"]

        direction = (
            "positive"
            if value > 0
            else "negative"
            if value < 0
            else "near-zero"
        )

        return (
            f"The strongest correlation is between "
            f"{first} and {second}, with a correlation "
            f"coefficient of {format_number(value)}. "
            f"This is a {direction} correlation."
        )

    # ========================================================
    # Weakest correlation
    # ========================================================

    weakest_correlation_phrases = [
        "weakest correlation",
        "lowest correlation",
        "least correlated",
        "weakest relationship",
        "least related",
    ]

    if any(
        phrase in q
        for phrase in weakest_correlation_phrases
    ):

        weakest = get_weakest_correlation(
            analysis
        )

        if weakest is None:
            return (
                "No correlation data is available "
                "for this dataset."
            )

        first = weakest["first"]
        second = weakest["second"]
        value = weakest["value"]

        return (
            f"The weakest correlation is between "
            f"{first} and {second}, with a correlation "
            f"coefficient of {format_number(value)}."
        )

    # ========================================================
    # Total outliers
    # ========================================================

    total_outlier_phrases = [
        "total outliers",
        "how many outliers",
        "number of outliers",
        "how many anomalies",
        "total anomalies",
        "number of anomalies",
    ]

    if any(
        phrase in q
        for phrase in total_outlier_phrases
    ):

        total_outliers = get_total_outliers(
            analysis
        )

        return (
            f"The dataset contains "
            f"{total_outliers} outliers in total."
        )

    # ========================================================
    # Column with most outliers
    # ========================================================

    most_outlier_phrases = [
        "most outliers",
        "highest number of outliers",
        "maximum outliers",
        "most anomalies",
    ]

    if any(
        phrase in q
        for phrase in most_outlier_phrases
    ):

        strongest_outlier = (
            get_strongest_outlier_column(
                analysis
            )
        )

        if strongest_outlier is None:
            return (
                "No outlier data is available "
                "for this dataset."
            )

        column, count = strongest_outlier

        return (
            f"The column with the most outliers is "
            f"{column}, with {count} outliers."
        )

    # ========================================================
    # Rows
    # ========================================================

    if (
        ("how many" in q or "number of" in q)
        and "row" in q
    ):

        return (
            f"The dataset contains "
            f"{dataset.rows} rows."
        )

    # ========================================================
    # Columns
    # ========================================================

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

    # ========================================================
    # Dataset name
    # ========================================================

    if (
        "dataset name" in q
        or "file name" in q
        or "filename" in q
    ):

        return (
            f"The dataset filename is "
            f"{dataset.original_filename}."
        )

    # ========================================================
    # Quality
    # ========================================================

    if (
        "quality score" in q
        or "data quality" in q
        or q == "quality"
    ):

        return (
            f"The dataset has a data quality "
            f"score of {analysis.quality_score}/100."
        )

    # ========================================================
    # Memory
    # ========================================================

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

            memory_value = analysis.summary.get(
                "memory_usage",
                0,
            )

            numeric_memory = safe_number(
                memory_value
            )

            if numeric_memory is not None:
                memory_kb = numeric_memory / 1024

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

Do not calculate, modify, or invent any values.

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

A correlation close to +1 means a strong positive
linear relationship.

A correlation close to -1 means a strong negative
linear relationship.

A correlation close to 0 means little linear
relationship.

Do not claim that correlation means causation.

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

Do not invent values or row numbers.

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

IMPORTANT RULES:

1. Use only verified information from the
   dataset analysis.

2. Never invent statistics, values, trends,
   correlations, percentages, or facts.

3. Never claim to have inspected raw data
   that is not included in the context.

4. If the required information is unavailable,
   clearly say that it is not available.

5. Correlation does not imply causation.

6. Use the actual dataset column names.

7. Give dataset-specific recommendations
   when the available evidence supports them.

8. Explain technical concepts in simple language.

9. Do not give generic advice when
   dataset-specific evidence is available.

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

ANSWER STYLE
------------
For analytical questions, structure the answer as:

Finding:
Evidence:
Interpretation:
Recommendation:

Keep the answer concise unless the user
asks for a detailed explanation.
"""


# ============================================================
# Generate Chat Answer
# ============================================================

async def generate_chat_answer(
    question: str,
    context: dict,
) -> str:

    dataset = context["dataset"]
    analysis = context["analysis"]

    # ========================================================
    # Check analysis
    # ========================================================

    if analysis is None:

        return (
            "I found the dataset, but its analysis "
            "is not available yet."
        )

    # ========================================================
    # Fast deterministic answer
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
    # Build focused/general prompt
    # ========================================================

    prompt = build_focused_prompt(
        question=question,
        dataset=dataset,
        analysis=analysis,
    )

    # ========================================================
    # AI Provider Router
    # ========================================================

    try:

        print(
            "CHAT: Sending question to AI provider..."
        )

        answer = await generate_ai_response(
            prompt
        )

        print(
            "CHAT: AI response received."
        )

        return answer.strip()

    except Exception as error:

        print(
            "AI provider error:",
            error,
        )

        return (
            "I couldn't generate an AI answer right now. "
            "Your dataset analysis is available, but "
            "the AI provider is temporarily unavailable."
        )
