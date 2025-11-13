"""
Utilitários para análises estatísticas
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Tuple, Optional, Dict, Any


def descriptive_stats(df: pd.DataFrame, column: Optional[str] = None) -> pd.DataFrame:
    """
    Calcula estatísticas descritivas
    
    Args:
        df: DataFrame de entrada
        column: Coluna específica (None para todas)
        
    Returns:
        DataFrame com estatísticas descritivas
    """
    if column:
        return df[column].describe()
    return df.describe()


def correlation_analysis(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """
    Calcula matriz de correlação
    
    Args:
        df: DataFrame de entrada
        method: Método de correlação ('pearson', 'spearman', 'kendall')
        
    Returns:
        Matriz de correlação
    """
    return df.corr(method=method, numeric_only=True)


def hypothesis_test_ttest(
    sample1: pd.Series,
    sample2: pd.Series,
    alternative: str = 'two-sided'
) -> Dict[str, float]:
    """
    Realiza teste t de Student para duas amostras independentes
    
    Args:
        sample1: Primeira amostra
        sample2: Segunda amostra
        alternative: Hipótese alternativa ('two-sided', 'less', 'greater')
        
    Returns:
        Dicionário com estatística t e p-valor
    """
    statistic, pvalue = stats.ttest_ind(sample1, sample2, alternative=alternative)
    return {
        'statistic': statistic,
        'pvalue': pvalue,
        'significant_5pct': pvalue < 0.05
    }


def hypothesis_test_chi2(observed: pd.DataFrame) -> Dict[str, float]:
    """
    Realiza teste qui-quadrado de independência
    
    Args:
        observed: Tabela de contingência observada
        
    Returns:
        Dicionário com estatística qui-quadrado, p-valor e graus de liberdade
    """
    chi2, pvalue, dof, expected = stats.chi2_contingency(observed)
    return {
        'chi2': chi2,
        'pvalue': pvalue,
        'dof': dof,
        'significant_5pct': pvalue < 0.05
    }


def normality_test(data: pd.Series) -> Dict[str, Any]:
    """
    Testa normalidade dos dados usando Shapiro-Wilk
    
    Args:
        data: Série de dados a testar
        
    Returns:
        Dicionário com estatística e p-valor
    """
    statistic, pvalue = stats.shapiro(data)
    return {
        'statistic': statistic,
        'pvalue': pvalue,
        'is_normal_5pct': pvalue > 0.05
    }


def confidence_interval(
    data: pd.Series,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calcula intervalo de confiança para a média
    
    Args:
        data: Série de dados
        confidence: Nível de confiança (padrão 95%)
        
    Returns:
        Tupla com (limite_inferior, limite_superior)
    """
    mean = data.mean()
    std_err = stats.sem(data)
    margin = std_err * stats.t.ppf((1 + confidence) / 2, len(data) - 1)
    return (mean - margin, mean + margin)


def anova_test(*groups) -> Dict[str, float]:
    """
    Realiza ANOVA (análise de variância) para múltiplos grupos
    
    Args:
        *groups: Grupos de dados a comparar
        
    Returns:
        Dicionário com estatística F e p-valor
    """
    statistic, pvalue = stats.f_oneway(*groups)
    return {
        'f_statistic': statistic,
        'pvalue': pvalue,
        'significant_5pct': pvalue < 0.05
    }


def regression_summary(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Calcula estatísticas básicas de regressão linear
    
    Args:
        X: Variáveis independentes
        y: Variável dependente
        
    Returns:
        Dicionário com estatísticas da regressão
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score, mean_squared_error
    
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    
    return {
        'r2_score': r2_score(y, y_pred),
        'rmse': np.sqrt(mean_squared_error(y, y_pred)),
        'coefficients': dict(zip(X.columns, model.coef_)),
        'intercept': model.intercept_
    }

