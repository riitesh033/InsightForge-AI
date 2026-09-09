"""
Professional Data Analysis Service

Generates business-quality analysis reports with:
- Executive summary
- Data quality assessment
- Descriptive statistics
- Distribution analysis
- Correlation analysis
- Outlier detection
- Key insights
- Actionable recommendations
- Business opportunity analysis
"""

from typing import Any, Optional
from datetime import datetime
import numpy as np
import pandas as pd
from scipy import stats


def to_json_safe(obj: Any) -> Any:
    """Recursively convert pandas/numpy/Python objects into JSON-safe values."""
    
    if isinstance(obj, dict):
        return {
            str(to_json_safe(key)): to_json_safe(value)
            for key, value in obj.items()
        }
    
    if isinstance(obj, list):
        return [to_json_safe(value) for value in obj]
    
    if isinstance(obj, tuple):
        return [to_json_safe(value) for value in obj]
    
    if isinstance(obj, set):
        return [to_json_safe(value) for value in obj]
    
    if obj is pd.NA:
        return None
    
    if isinstance(obj, (pd.Timestamp, pd.DatetimeTZDtype)):
        try:
            return pd.Timestamp(obj).isoformat()
        except Exception:
            return str(obj)
    
    if isinstance(obj, pd.Timedelta):
        return str(obj)
    
    if isinstance(obj, np.datetime64):
        try:
            return pd.Timestamp(obj).isoformat()
        except Exception:
            return str(obj)
    
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    
    if isinstance(obj, np.integer):
        return int(obj)
    
    if isinstance(obj, np.floating):
        value = float(obj)
        if not np.isfinite(value):
            return None
        return value
    
    if isinstance(obj, np.bool_):
        return bool(obj)
    
    if isinstance(obj, np.ndarray):
        return [to_json_safe(value) for value in obj.tolist()]
    
    if isinstance(obj, float):
        if not np.isfinite(obj):
            return None
        return obj
    
    try:
        missing = pd.isna(obj)
        if isinstance(missing, (bool, np.bool_)) and missing:
            return None
    except (TypeError, ValueError):
        pass
    
    return obj


def detect_column_types(df: pd.DataFrame) -> dict[str, list[str]]:
    """Detect column types beyond pandas dtypes."""
    
    numerical = []
    categorical = []
    datetime_cols = []
    boolean_cols = []
    identifier = []
    
    for col in df.columns:
        col_str = str(col).lower()
        series = df[col]
        
        # Check for datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(str(col))
            continue
        
        # Check for boolean
        if pd.api.types.is_bool_dtype(series):
            boolean_cols.append(str(col))
            continue
        
        # Check for identifier patterns
        if (col_str == 'id' or col_str.endswith('_id') or 
            col_str.endswith('id') and col_str != 'paid'):
            if series.nunique() == len(series.dropna()):
                identifier.append(str(col))
                continue
        
        # Check for numerical
        if pd.api.types.is_numeric_dtype(series):
            numerical.append(str(col))
            continue
        
        # Check if categorical (low cardinality or object/string)
        unique_ratio = series.nunique() / len(series) if len(series) > 0 else 0
        if (pd.api.types.is_object_dtype(series) or 
            pd.api.types.is_string_dtype(series) or
            (unique_ratio < 0.1 and series.nunique() < 50)):
            categorical.append(str(col))
            continue
        
        # Default to categorical for remaining
        categorical.append(str(col))
    
    return {
        'numerical': numerical,
        'categorical': categorical,
        'datetime': datetime_cols,
        'boolean': boolean_cols,
        'identifier': identifier
    }


def calculate_descriptive_statistics(df: pd.DataFrame, column_types: dict) -> dict:
    """Calculate comprehensive descriptive statistics."""
    
    statistics = {}
    
    # Numerical columns
    for col in column_types.get('numerical', []):
        series = df[col].dropna()
        
        if len(series) == 0:
            continue
        
        stats_dict = {
            'count': int(len(series)),
            'mean': float(series.mean()) if len(series) > 0 else None,
            'median': float(series.median()) if len(series) > 0 else None,
            'mode': float(series.mode().iloc[0]) if len(series.mode()) > 0 else None,
            'min': float(series.min()) if len(series) > 0 else None,
            'max': float(series.max()) if len(series) > 0 else None,
            'range': float(series.max() - series.min()) if len(series) > 0 else None,
            'std': float(series.std()) if len(series) > 1 else None,
            'variance': float(series.var()) if len(series) > 1 else None,
            'q1': float(series.quantile(0.25)) if len(series) > 0 else None,
            'q3': float(series.quantile(0.75)) if len(series) > 0 else None,
            'iqr': float(series.quantile(0.75) - series.quantile(0.25)) if len(series) > 0 else None,
            'skewness': float(stats.skew(series)) if len(series) > 2 else None,
            'kurtosis': float(stats.kurtosis(series)) if len(series) > 3 else None,
            'percentile_5': float(series.quantile(0.05)) if len(series) > 0 else None,
            'percentile_95': float(series.quantile(0.95)) if len(series) > 0 else None,
            'coefficient_of_variation': float(series.std() / series.mean()) if len(series) > 1 and series.mean() != 0 else None,
        }
        
        # Clean up None values
        stats_dict = {k: v for k, v in stats_dict.items() if v is not None and not (isinstance(v, float) and not np.isfinite(v))}
        
        statistics[col] = stats_dict
    
    # Categorical columns
    for col in column_types.get('categorical', []):
        series = df[col].dropna()
        
        if len(series) == 0:
            continue
        
        value_counts = series.value_counts()
        top_value = value_counts.index[0] if len(value_counts) > 0 else None
        top_count = int(value_counts.iloc[0]) if len(value_counts) > 0 else 0
        
        stats_dict = {
            'count': int(len(series)),
            'unique': int(series.nunique()),
            'top_value': str(top_value) if top_value is not None else None,
            'top_frequency': top_count,
            'top_percentage': round((top_count / len(series)) * 100, 2) if len(series) > 0 else 0,
        }
        
        # Add distribution for top 5 categories
        distribution = {}
        for val, count in value_counts.head(5).items():
            distribution[str(val)] = {
                'count': int(count),
                'percentage': round((count / len(series)) * 100, 2)
            }
        
        stats_dict['distribution'] = distribution
        statistics[col] = stats_dict
    
    # Datetime columns
    for col in column_types.get('datetime', []):
        series = df[col].dropna()
        
        if len(series) == 0:
            continue
        
        stats_dict = {
            'count': int(len(series)),
            'min_date': series.min().isoformat() if len(series) > 0 else None,
            'max_date': series.max().isoformat() if len(series) > 0 else None,
            'time_span_days': int((series.max() - series.min()).days) if len(series) > 1 else 0,
        }
        
        statistics[col] = stats_dict
    
    return statistics


def analyze_data_quality(df: pd.DataFrame, column_types: dict) -> dict:
    """Comprehensive data quality assessment."""
    
    total_rows = len(df)
    issues = []
    
    # Missing values analysis
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        if missing_count > 0:
            missing_percent = round((missing_count / total_rows) * 100, 2)
            
            severity = 'low'
            if missing_percent > 30:
                severity = 'high'
            elif missing_percent > 10:
                severity = 'medium'
            
            col_type = 'unknown'
            for type_name, cols in column_types.items():
                if col in cols:
                    col_type = type_name
                    break
            
            recommendation = f"Consider {'imputing using median/mode' if col_type == 'numerical' else 'using most frequent value or creating an Unknown category'} if missingness is random."
            if missing_percent > 50:
                recommendation = "Consider removing this column due to excessive missing values."
            
            issues.append({
                'type': 'missing_values',
                'column': str(col),
                'count': missing_count,
                'percentage': missing_percent,
                'severity': severity,
                'recommendation': recommendation
            })
    
    # Duplicate analysis
    duplicate_count = int(df.duplicated().sum())
    if duplicate_count > 0:
        duplicate_percent = round((duplicate_count / total_rows) * 100, 2)
        
        severity = 'low'
        if duplicate_percent > 20:
            severity = 'high'
        elif duplicate_percent > 5:
            severity = 'medium'
        
        issues.append({
            'type': 'duplicates',
            'column': 'all',
            'count': duplicate_count,
            'percentage': duplicate_percent,
            'severity': severity,
            'recommendation': 'Investigate whether duplicates are valid or errors. Consider removing exact duplicates.'
        })
    
    # Constant columns
    for col in df.columns:
        if df[col].nunique() == 1 and df[col].notna().any():
            issues.append({
                'type': 'constant_column',
                'column': str(col),
                'count': 1,
                'percentage': 100.0,
                'severity': 'low',
                'recommendation': 'This column has no variance and may not be useful for analysis.'
            })
    
    # High cardinality categorical columns
    for col in column_types.get('categorical', []):
        unique_count = df[col].nunique()
        unique_ratio = unique_count / total_rows if total_rows > 0 else 0
        
        if unique_count > 100 and unique_ratio > 0.5:
            issues.append({
                'type': 'high_cardinality',
                'column': str(col),
                'count': unique_count,
                'percentage': round(unique_ratio * 100, 2),
                'severity': 'medium',
                'recommendation': 'High cardinality may cause issues in modeling. Consider grouping rare categories.'
            })
    
    # Outlier detection for numerical columns
    for col in column_types.get('numerical', []):
        series = df[col].dropna()
        
        if len(series) < 4:
            continue
        
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = ((series < lower_bound) | (series > upper_bound)).sum()
        
        if outliers > 0:
            outlier_percent = round((outliers / len(series)) * 100, 2)
            
            severity = 'low'
            if outlier_percent > 10:
                severity = 'high'
            elif outlier_percent > 5:
                severity = 'medium'
            
            issues.append({
                'type': 'outliers',
                'column': str(col),
                'count': int(outliers),
                'percentage': outlier_percent,
                'severity': severity,
                'recommendation': 'Investigate outliers. They may be errors or valid extreme values. Consider winsorizing or transformation if they skew analysis.'
            })
    
    # Calculate overall quality score
    score = 100
    
    for issue in issues:
        if issue['severity'] == 'high':
            score -= 15
        elif issue['severity'] == 'medium':
            score -= 8
        else:
            score -= 3
    
    score = max(score, 0)
    
    return {
        'quality_score': score,
        'total_issues': len(issues),
        'issues': issues,
        'summary': {
            'excellent': score >= 90,
            'good': 75 <= score < 90,
            'fair': 50 <= score < 75,
            'poor': score < 50
        }
    }


def analyze_distributions(df: pd.DataFrame, column_types: dict) -> dict:
    """Analyze distribution characteristics for numerical columns."""
    
    distributions = {}
    
    for col in column_types.get('numerical', []):
        series = df[col].dropna()
        
        if len(series) < 4:
            continue
        
        # Calculate statistics
        mean = series.mean()
        median = series.median()
        std = series.std()
        skewness = stats.skewness(series)
        kurtosis = stats.kurtosis(series)
        
        # Determine distribution shape
        shape = 'unknown'
        if abs(skewness) < 0.5:
            shape = 'approximately_symmetric'
        elif skewness > 0:
            shape = 'right_skewed'
        else:
            shape = 'left_skewed'
        
        # Determine variance level
        cv = std / mean if mean != 0 else 0
        variance_level = 'moderate'
        if abs(cv) > 1:
            variance_level = 'high'
        elif abs(cv) < 0.3:
            variance_level = 'low'
        
        # Check for concentration
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        range_val = series.max() - series.min()
        
        concentration = 'normal'
        if range_val > 0 and iqr / range_val < 0.2:
            concentration = 'highly_concentrated'
        elif range_val > 0 and iqr / range_val > 0.6:
            concentration = 'widely_spread'
        
        distributions[col] = {
            'shape': shape,
            'skewness': round(skewness, 3),
            'kurtosis': round(kurtosis, 3),
            'variance_level': variance_level,
            'coefficient_of_variation': round(cv, 3),
            'concentration': concentration,
            'has_outliers': bool(any((series < (q1 - 1.5 * iqr)) | (series > (q3 + 1.5 * iqr)))),
        }
    
    return distributions


def analyze_correlations(df: pd.DataFrame, column_types: dict) -> dict:
    """Analyze correlations between numerical variables."""
    
    numerical_df = df[column_types.get('numerical', [])]
    
    if len(numerical_df.columns) < 2 or len(numerical_df) < 3:
        return {'matrix': {}, 'pairs': [], 'interpretation': []}
    
    # Calculate correlation matrix
    corr_matrix = numerical_df.corr(numeric_only=True).round(3)
    
    # Extract significant pairs
    pairs = []
    interpretation = []
    
    columns = list(corr_matrix.columns)
    
    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):
            col1 = columns[i]
            col2 = columns[j]
            corr_value = float(corr_matrix.loc[col1, col2])
            
            if not np.isnan(corr_value):
                strength = 'weak'
                direction = 'positive' if corr_value >= 0 else 'negative'
                
                if abs(corr_value) >= 0.7:
                    strength = 'strong'
                elif abs(corr_value) >= 0.4:
                    strength = 'moderate'
                
                pairs.append({
                    'first': col1,
                    'second': col2,
                    'value': corr_value,
                    'strength': strength,
                    'direction': direction
                })
                
                if abs(corr_value) >= 0.6:
                    interpretation.append({
                        'columns': [col1, col2],
                        'correlation': corr_value,
                        'interpretation': (
                            f"{col1} and {col2} show a {strength} {direction} correlation "
                            f"(r = {corr_value:.3f}). This indicates they tend to move together, "
                            f"but correlation does not imply causation."
                        )
                    })
    
    # Sort by absolute correlation
    pairs.sort(key=lambda x: abs(x['value']), reverse=True)
    
    return {
        'matrix': corr_matrix.to_dict(),
        'pairs': pairs,
        'interpretation': interpretation
    }


def generate_key_insights(
    df: pd.DataFrame,
    column_types: dict,
    statistics: dict,
    quality: dict,
    correlations: dict,
    distributions: dict
) -> list[dict]:
    """Generate meaningful insights from the analysis."""
    
    insights = []
    total_rows = len(df)
    
    # Insight 1: Data quality issues
    if quality['total_issues'] > 0:
        high_severity_issues = [i for i in quality['issues'] if i['severity'] == 'high']
        
        if high_severity_issues:
            insights.append({
                'category': 'data_quality',
                'finding': f"Critical data quality issues detected in {len(high_severity_issues)} area(s).",
                'evidence': f"Quality score: {quality['quality_score']}/100. Issues include: {', '.join(set(i['type'] for i in high_severity_issues))}.",
                'impact': 'Poor data quality can lead to inaccurate analysis and misleading conclusions.',
                'recommendation': 'Address high-severity issues before proceeding with advanced analysis or decision-making.'
            })
    
    # Insight 2: Missing values pattern
    missing_issues = [i for i in quality['issues'] if i['type'] == 'missing_values' and i['percentage'] > 5]
    
    if missing_issues:
        worst_missing = max(missing_issues, key=lambda x: x['percentage'])
        insights.append({
            'category': 'data_quality',
            'finding': f"Column '{worst_missing['column']}' has significant missing values ({worst_missing['percentage']}%).",
            'evidence': f"{worst_missing['count']} out of {total_rows} records are missing in this column.",
            'impact': 'Missing data can bias analysis results and reduce statistical power.',
            'recommendation': f"Consider imputation strategies or investigate why data is missing in '{worst_missing['column']}'."
        })
    
    # Insight 3: Strong correlations
    strong_correlations = [p for p in correlations.get('pairs', []) if abs(p['value']) >= 0.7]
    
    if strong_correlations:
        strongest = strong_correlations[0]
        insights.append({
            'category': 'relationships',
            'finding': f"Strong relationship detected between '{strongest['first']}' and '{strongest['second']}'.",
            'evidence': f"Correlation coefficient: {strongest['value']:.3f}",
            'impact': 'These variables move together strongly, which may indicate redundancy or important business relationships.',
            'recommendation': 'Investigate whether one variable causes the other, or if both are influenced by a third factor.'
        })
    
    # Insight 4: Outlier concerns
    outlier_issues = [i for i in quality['issues'] if i['type'] == 'outliers' and i['percentage'] > 5]
    
    if outlier_issues:
        worst_outlier = max(outlier_issues, key=lambda x: x['percentage'])
        insights.append({
            'category': 'anomalies',
            'finding': f"Significant outliers detected in '{worst_outlier['column']}'.",
            'evidence': f"{worst_outlier['count']} values ({worst_outlier['percentage']}%) fall outside normal ranges.",
            'impact': 'Outliers can disproportionately influence statistical measures and model training.',
            'recommendation': 'Verify if outliers are data entry errors or legitimate extreme values. Consider separate analysis.'
        })
    
    # Insight 5: Distribution characteristics
    skewed_cols = [(col, dist) for col, dist in distributions.items() 
                   if dist.get('shape') in ['right_skewed', 'left_skewed']]
    
    if skewed_cols:
        most_skewed = max(skewed_cols, key=lambda x: abs(x[1].get('skewness', 0)))
        insights.append({
            'category': 'distribution',
            'finding': f"Column '{most_skewed[0]}' shows {most_skewed[1]['shape'].replace('_', ' ')}.",
            'evidence': f"Skewness coefficient: {most_skewed[1].get('skewness', 0):.3f}",
            'impact': 'Skewed distributions may require transformation for certain statistical analyses.',
            'recommendation': 'Consider log or square root transformation if normality is required for analysis.'
        })
    
    # Insight 6: Business opportunities (if applicable)
    revenue_col = None
    cost_col = None
    quantity_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if any(term in col_lower for term in ['revenue', 'sales', 'amount', 'price']):
            revenue_col = col
        if any(term in col_lower for term in ['cost', 'expense']):
            cost_col = col
        if any(term in col_lower for term in ['quantity', 'units', 'count']):
            quantity_col = col
    
    if revenue_col and revenue_col in statistics:
        rev_stats = statistics[revenue_col]
        insights.append({
            'category': 'business',
            'finding': f"Revenue analysis shows significant variation.",
            'evidence': f"Mean: {rev_stats.get('mean', 0):,.2f}, Std Dev: {rev_stats.get('std', 0):,.2f}, Range: {rev_stats.get('min', 0):,.2f} to {rev_stats.get('max', 0):,.2f}",
            'impact': 'High variance suggests opportunities for optimization and segmentation.',
            'recommendation': 'Segment analysis by product/customer/category to identify high-performing segments.'
        })
    
    if revenue_col and cost_col and revenue_col in df.columns and cost_col in df.columns:
        profit_col = df[revenue_col] - df[cost_col]
        profit_margin = (profit_col / df[revenue_col]).mean() * 100 if df[revenue_col].mean() != 0 else 0
        
        insights.append({
            'category': 'business',
            'finding': f"Average profit margin is approximately {profit_margin:.1f}%.",
            'evidence': f"Calculated from revenue and cost columns. Margin varies across records.",
            'impact': 'Understanding margin drivers can help optimize profitability.',
            'recommendation': 'Analyze which products/customers have highest margins and focus resources there.'
        })
    
    # Insight 7: Dataset size considerations
    if total_rows < 100:
        insights.append({
            'category': 'methodology',
            'finding': 'Dataset is relatively small.',
            'evidence': f'Only {total_rows} records available for analysis.',
            'impact': 'Small sample sizes limit statistical power and generalizability.',
            'recommendation': 'Collect more data if possible. Be cautious about drawing strong conclusions.'
        })
    elif total_rows > 100000:
        insights.append({
            'category': 'methodology',
            'finding': 'Large dataset provides robust statistical foundation.',
            'evidence': f'{total_rows:,} records available for analysis.',
            'impact': 'Large samples enable reliable statistical inference and machine learning.',
            'recommendation': 'Consider sampling for exploratory analysis to improve speed.'
        })
    
    # Limit insights to most important ones
    return insights[:8]


def generate_recommendations(
    df: pd.DataFrame,
    column_types: dict,
    quality: dict,
    insights: list[dict]
) -> dict:
    """Generate prioritized actionable recommendations."""
    
    high_priority = []
    medium_priority = []
    low_priority = []
    
    # High priority: Critical data quality issues
    critical_issues = [i for i in quality['issues'] if i['severity'] == 'high']
    
    for issue in critical_issues:
        if issue['type'] == 'missing_values':
            high_priority.append({
                'action': f"Fix missing values in '{issue['column']}'",
                'reason': f"{issue['percentage']}% of values are missing",
                'evidence': f"{issue['count']} records affected",
                'benefit': 'Improved data completeness and analysis accuracy',
                'risk': 'Imputation may introduce bias if missingness is not random'
            })
        elif issue['type'] == 'outliers':
            high_priority.append({
                'action': f"Investigate outliers in '{issue['column']}'",
                'reason': f"{issue['count']} extreme values detected",
                'evidence': f"{issue['percentage']}% of data points are outliers",
                'benefit': 'More accurate statistical measures and models',
                'risk': 'Removing valid outliers may lose important information'
            })
    
    # Medium priority: Moderate issues and opportunities
    medium_issues = [i for i in quality['issues'] if i['severity'] == 'medium']
    
    for issue in medium_issues:
        if issue['type'] == 'duplicates':
            medium_priority.append({
                'action': 'Review and remove duplicate records',
                'reason': f"{issue['count']} duplicate rows found",
                'evidence': f"{issue['percentage']}% of dataset contains duplicates",
                'benefit': 'Cleaner dataset, more accurate aggregations',
                'risk': 'Some duplicates may be legitimate (e.g., repeated transactions)'
            })
        elif issue['type'] == 'high_cardinality':
            medium_priority.append({
                'action': f"Group rare categories in '{issue['column']}'",
                'reason': 'Too many unique values for effective analysis',
                'evidence': f"{issue['count']} unique values",
                'benefit': 'Simplified analysis and better model performance',
                'risk': 'May lose granularity in some segments'
            })
    
    # Low priority: Optimization suggestions
    constant_cols = [i for i in quality['issues'] if i['type'] == 'constant_column']
    
    if constant_cols:
        low_priority.append({
            'action': f"Consider removing constant columns: {', '.join(i['column'] for i in constant_cols)}",
            'reason': 'These columns have no variance',
            'evidence': 'Constant columns provide no analytical value',
            'benefit': 'Reduced memory usage and faster processing',
            'risk': 'None - constant columns cannot contribute to analysis'
        })
    
    # Add general recommendations based on dataset characteristics
    if len(column_types.get('datetime', [])) > 0:
        medium_priority.append({
            'action': 'Perform time-series analysis',
            'reason': 'Dataset contains temporal information',
            'evidence': f"Date columns detected: {', '.join(column_types['datetime'])}",
            'benefit': 'Identify trends, seasonality, and temporal patterns',
            'risk': 'Requires sufficient time span for meaningful analysis'
        })
    
    if len(column_types.get('categorical', [])) > 2:
        medium_priority.append({
            'action': 'Perform segmentation analysis',
            'reason': 'Multiple categorical variables available',
            'evidence': f"Categorical columns: {', '.join(column_types['categorical'][:5])}",
            'benefit': 'Discover distinct groups and tailor strategies',
            'risk': 'Over-segmentation may reduce actionability'
        })
    
    # If no high priority items, add a default
    if not high_priority:
        high_priority.append({
            'action': 'Proceed with standard analysis workflow',
            'reason': 'No critical data quality issues detected',
            'evidence': f"Quality score: {quality['quality_score']}/100",
            'benefit': 'Efficient use of analysis resources',
            'risk': 'Continue monitoring for emerging issues'
        })
    
    return {
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'low_priority': low_priority
    }


def analyze_business_opportunities(df: pd.DataFrame, column_types: dict) -> dict:
    """Analyze potential business opportunities if relevant columns exist."""
    
    opportunities = []
    required_columns = {
        'revenue': ['revenue', 'sales', 'amount', 'price', 'total'],
        'cost': ['cost', 'expense', 'cogs'],
        'profit': ['profit', 'margin', 'earnings'],
        'product': ['product', 'item', 'sku', 'category'],
        'customer': ['customer', 'client', 'user', 'buyer'],
        'date': ['date', 'time', 'timestamp', 'order_date'],
        'quantity': ['quantity', 'units', 'qty', 'count']
    }
    
    # Map actual columns to business concepts
    column_mapping = {}
    
    for concept, terms in required_columns.items():
        for col in df.columns:
            col_lower = str(col).lower()
            if any(term in col_lower for term in terms):
                column_mapping[concept] = col
                break
    
    # Can we calculate profit?
    can_calculate_profit = False
    
    if 'revenue' in column_mapping and 'cost' in column_mapping:
        can_calculate_profit = True
        revenue_col = column_mapping['revenue']
        cost_col = column_mapping['cost']
        
        profit = df[revenue_col] - df[cost_col]
        profit_margin = (profit / df[revenue_col]).replace([np.inf, -np.inf], np.nan)
        
        opportunities.append({
            'type': 'profit_analysis',
            'finding': 'Profit can be calculated from available data',
            'metrics': {
                'average_profit': float(profit.mean()) if not profit.isna().all() else None,
                'average_margin_percent': float(profit_margin.mean() * 100) if not profit_margin.isna().all() else None,
                'total_profit': float(profit.sum()) if not profit.isna().all() else None
            },
            'recommendation': 'Analyze profit by product/customer segment to identify optimization opportunities'
        })
    
    # Product analysis
    if 'product' in column_mapping and 'revenue' in column_mapping:
        product_col = column_mapping['product']
        revenue_col = column_mapping['revenue']
        
        product_revenue = df.groupby(product_col)[revenue_col].agg(['sum', 'mean', 'count']).reset_index()
        product_revenue.columns = ['product', 'total_revenue', 'avg_revenue', 'transaction_count']
        product_revenue = product_revenue.sort_values('total_revenue', ascending=False)
        
        if len(product_revenue) > 0:
            top_product = product_revenue.iloc[0]
            opportunities.append({
                'type': 'product_performance',
                'finding': f"Top product by revenue identified",
                'metrics': {
                    'top_product': str(top_product['product']),
                    'top_product_revenue': float(top_product['total_revenue']),
                    'concentration': float(product_revenue.head(5)['total_revenue'].sum() / product_revenue['total_revenue'].sum() * 100) if product_revenue['total_revenue'].sum() > 0 else None
                },
                'recommendation': 'Focus on understanding what makes top products successful'
            })
    
    # Customer analysis
    if 'customer' in column_mapping and 'revenue' in column_mapping:
        customer_col = column_mapping['customer']
        revenue_col = column_mapping['revenue']
        
        customer_revenue = df.groupby(customer_col)[revenue_col].sum().reset_index()
        customer_revenue.columns = ['customer', 'total_revenue']
        customer_revenue = customer_revenue.sort_values('total_revenue', ascending=False)
        
        if len(customer_revenue) > 0:
            top_20_pct = customer_revenue.head(int(len(customer_revenue) * 0.2))
            concentration = top_20_pct['total_revenue'].sum() / customer_revenue['total_revenue'].sum() * 100 if customer_revenue['total_revenue'].sum() > 0 else 0
            
            opportunities.append({
                'type': 'customer_concentration',
                'finding': 'Customer revenue concentration analysis',
                'metrics': {
                    'top_20_percent_customers_revenue_share': float(concentration),
                    'total_customers': len(customer_revenue)
                },
                'recommendation': 'If concentration > 80%, consider diversification strategy to reduce dependency risk'
            })
    
    # Time-based analysis
    if 'date' in column_mapping and 'revenue' in column_mapping:
        date_col = column_mapping['date']
        revenue_col = column_mapping['revenue']
        
        try:
            df[date_col] = pd.to_datetime(df[date_col])
            monthly_revenue = df.set_index(date_col)[revenue_col].resample('M').sum()
            
            if len(monthly_revenue) > 1:
                trend = monthly_revenue.diff().mean()
                opportunities.append({
                    'type': 'temporal_trend',
                    'finding': 'Temporal revenue trend analysis',
                    'metrics': {
                        'average_monthly_change': float(trend) if not np.isnan(trend) else None,
                        'trend_direction': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable'
                    },
                    'recommendation': 'Investigate factors driving the trend and consider seasonal adjustments'
                })
        except Exception:
            pass
    
    # If no opportunities found, explain what's needed
    if not opportunities:
        missing = set(required_columns.keys()) - set(column_mapping.keys())
        opportunities.append({
            'type': 'data_requirements',
            'finding': 'Limited business analysis possible with current columns',
            'missing_columns': list(missing),
            'recommendation': f"Add columns related to: {', '.join(missing)} for comprehensive business analysis"
        })
    
    return {
        'available_metrics': list(column_mapping.keys()),
        'can_calculate_profit': can_calculate_profit,
        'opportunities': opportunities
    }


def generate_professional_analysis(df: pd.DataFrame) -> dict:
    """Main function to generate comprehensive professional analysis."""
    
    print("\n========================================")
    print("GENERATING PROFESSIONAL ANALYSIS")
    print("========================================\n")
    
    # Step 1: Detect column types
    print("Step 1: Detecting column types...")
    column_types = detect_column_types(df)
    print(f"  Numerical: {len(column_types['numerical'])}")
    print(f"  Categorical: {len(column_types['categorical'])}")
    print(f"  Datetime: {len(column_types['datetime'])}")
    print(f"  Boolean: {len(column_types['boolean'])}")
    print(f"  Identifier: {len(column_types['identifier'])}\n")
    
    # Step 2: Calculate descriptive statistics
    print("Step 2: Calculating descriptive statistics...")
    statistics = calculate_descriptive_statistics(df, column_types)
    print(f"  Statistics calculated for {len(statistics)} columns\n")
    
    # Step 3: Analyze data quality
    print("Step 3: Analyzing data quality...")
    quality = analyze_data_quality(df, column_types)
    print(f"  Quality score: {quality['quality_score']}/100")
    print(f"  Total issues: {quality['total_issues']}\n")
    
    # Step 4: Analyze distributions
    print("Step 4: Analyzing distributions...")
    distributions = analyze_distributions(df, column_types)
    print(f"  Distribution analysis for {len(distributions)} columns\n")
    
    # Step 5: Analyze correlations
    print("Step 5: Analyzing correlations...")
    correlations = analyze_correlations(df, column_types)
    print(f"  Found {len(correlations.get('pairs', []))} correlation pairs\n")
    
    # Step 6: Generate key insights
    print("Step 6: Generating key insights...")
    insights = generate_key_insights(df, column_types, statistics, quality, correlations, distributions)
    print(f"  Generated {len(insights)} insights\n")
    
    # Step 7: Generate recommendations
    print("Step 7: Generating recommendations...")
    recommendations = generate_recommendations(df, column_types, quality, insights)
    print(f"  High priority: {len(recommendations['high_priority'])}")
    print(f"  Medium priority: {len(recommendations['medium_priority'])}")
    print(f"  Low priority: {len(recommendations['low_priority'])}\n")
    
    # Step 8: Analyze business opportunities
    print("Step 8: Analyzing business opportunities...")
    business_opportunities = analyze_business_opportunities(df, column_types)
    print(f"  Available metrics: {business_opportunities['available_metrics']}")
    print(f"  Can calculate profit: {business_opportunities['can_calculate_profit']}\n")
    
    # Compile executive summary
    print("Step 9: Compiling executive summary...")
    
    summary_parts = []
    summary_parts.append(f"The dataset contains {len(df):,} records across {len(df.columns)} variables.")
    
    if quality['quality_score'] >= 90:
        summary_parts.append("The overall data quality is excellent.")
    elif quality['quality_score'] >= 75:
        summary_parts.append("The overall data quality is good.")
    elif quality['quality_score'] >= 50:
        summary_parts.append("The overall data quality is fair, with some issues requiring attention.")
    else:
        summary_parts.append("The overall data quality is poor and requires immediate attention.")
    
    # Add key finding
    if insights:
        top_insight = insights[0]
        summary_parts.append(f"Key finding: {top_insight['finding']}")
    
    # Add top recommendation
    if recommendations['high_priority']:
        top_rec = recommendations['high_priority'][0]
        summary_parts.append(f"Primary recommendation: {top_rec['action']}")
    
    executive_summary = " ".join(summary_parts)
    
    print("Analysis generation complete!")
    print("========================================\n")
    
    return to_json_safe({
        'executive_summary': executive_summary,
        'dataset_overview': {
            'rows': len(df),
            'columns': len(df.columns),
            'memory_bytes': int(df.memory_usage(deep=True).sum()),
            'column_types': column_types,
        },
        'statistics': statistics,
        'data_quality': quality,
        'distributions': distributions,
        'correlations': correlations,
        'key_insights': insights,
        'recommendations': recommendations,
        'business_opportunities': business_opportunities,
        'generated_at': datetime.now().isoformat(),
        'methodology': {
            'outlier_detection': 'IQR method (Q1 - 1.5*IQR, Q3 + 1.5*IQR)',
            'correlation_method': "Pearson's correlation coefficient",
            'quality_scoring': 'Weighted penalty system based on issue severity',
            'limitations': [
                'Correlation does not imply causation',
                'Statistical tests assume independent observations',
                'Business interpretations depend on domain context',
                'Small sample sizes may limit reliability'
            ]
        }
    })
