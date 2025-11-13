"""
Utilitários para visualizações padronizadas
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, List, Tuple


# Configuração de estilo padrão
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10


def save_figure(fig, filename: str, output_dir: str = "../reports/figures", dpi: int = 300) -> None:
    """
    Salva uma figura no diretório de relatórios
    
    Args:
        fig: Figura matplotlib
        filename: Nome do arquivo
        output_dir: Diretório de saída
        dpi: Resolução da imagem
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path / filename, dpi=dpi, bbox_inches='tight')
    plt.close(fig)


def plot_distribution(
    data: pd.Series,
    title: str = "Distribuição",
    xlabel: Optional[str] = None,
    bins: int = 30,
    save: bool = False,
    filename: Optional[str] = None
) -> plt.Figure:
    """
    Cria histograma com curva de densidade
    
    Args:
        data: Dados a visualizar
        title: Título do gráfico
        xlabel: Rótulo do eixo X
        bins: Número de bins do histograma
        save: Se True, salva a figura
        filename: Nome do arquivo (se save=True)
        
    Returns:
        Figura matplotlib
    """
    fig, ax = plt.subplots()
    
    ax.hist(data, bins=bins, alpha=0.7, density=True, edgecolor='black')
    
    # Curva de densidade
    data_clean = data.dropna()
    density = stats.gaussian_kde(data_clean)
    xs = np.linspace(data_clean.min(), data_clean.max(), 200)
    ax.plot(xs, density(xs), 'r-', linewidth=2)
    
    ax.set_title(title)
    ax.set_xlabel(xlabel or data.name)
    ax.set_ylabel('Densidade')
    
    if save and filename:
        save_figure(fig, filename)
    
    return fig


def plot_boxplot(
    df: pd.DataFrame,
    column: str,
    by: Optional[str] = None,
    title: str = "Boxplot",
    save: bool = False,
    filename: Optional[str] = None
) -> plt.Figure:
    """
    Cria boxplot para análise de distribuição e outliers
    
    Args:
        df: DataFrame de entrada
        column: Coluna a visualizar
        by: Coluna para agrupar (opcional)
        title: Título do gráfico
        save: Se True, salva a figura
        filename: Nome do arquivo (se save=True)
        
    Returns:
        Figura matplotlib
    """
    fig, ax = plt.subplots()
    
    if by:
        df.boxplot(column=column, by=by, ax=ax)
        plt.suptitle('')
    else:
        df.boxplot(column=column, ax=ax)
    
    ax.set_title(title)
    
    if save and filename:
        save_figure(fig, filename)
    
    return fig


def plot_correlation_heatmap(
    df: pd.DataFrame,
    title: str = "Matriz de Correlação",
    cmap: str = 'coolwarm',
    save: bool = False,
    filename: Optional[str] = None
) -> plt.Figure:
    """
    Cria heatmap de correlação
    
    Args:
        df: DataFrame de entrada
        title: Título do gráfico
        cmap: Esquema de cores
        save: Se True, salva a figura
        filename: Nome do arquivo (se save=True)
        
    Returns:
        Figura matplotlib
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    
    corr_matrix = df.corr(numeric_only=True)
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap=cmap, 
                center=0, square=True, linewidths=1, ax=ax)
    
    ax.set_title(title)
    
    if save and filename:
        save_figure(fig, filename)
    
    return fig


def plot_scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
    title: str = "Gráfico de Dispersão",
    save: bool = False,
    filename: Optional[str] = None
) -> plt.Figure:
    """
    Cria gráfico de dispersão
    
    Args:
        df: DataFrame de entrada
        x: Coluna para eixo X
        y: Coluna para eixo Y
        hue: Coluna para colorir pontos (opcional)
        title: Título do gráfico
        save: Se True, salva a figura
        filename: Nome do arquivo (se save=True)
        
    Returns:
        Figura matplotlib
    """
    fig, ax = plt.subplots()
    
    if hue:
        sns.scatterplot(data=df, x=x, y=y, hue=hue, ax=ax)
    else:
        sns.scatterplot(data=df, x=x, y=y, ax=ax)
    
    ax.set_title(title)
    
    if save and filename:
        save_figure(fig, filename)
    
    return fig


def plot_time_series(
    df: pd.DataFrame,
    date_column: str,
    value_columns: List[str],
    title: str = "Série Temporal",
    save: bool = False,
    filename: Optional[str] = None
) -> plt.Figure:
    """
    Cria gráfico de série temporal
    
    Args:
        df: DataFrame de entrada
        date_column: Coluna com datas
        value_columns: Lista de colunas a plotar
        title: Título do gráfico
        save: Se True, salva a figura
        filename: Nome do arquivo (se save=True)
        
    Returns:
        Figura matplotlib
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for col in value_columns:
        ax.plot(df[date_column], df[col], label=col, marker='o')
    
    ax.set_title(title)
    ax.set_xlabel('Data')
    ax.set_ylabel('Valor')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    
    if save and filename:
        save_figure(fig, filename)
    
    return fig


def plot_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "Gráfico de Barras",
    horizontal: bool = False,
    save: bool = False,
    filename: Optional[str] = None
) -> plt.Figure:
    """
    Cria gráfico de barras
    
    Args:
        df: DataFrame de entrada
        x: Coluna para categorias
        y: Coluna para valores
        title: Título do gráfico
        horizontal: Se True, cria barras horizontais
        save: Se True, salva a figura
        filename: Nome do arquivo (se save=True)
        
    Returns:
        Figura matplotlib
    """
    fig, ax = plt.subplots()
    
    if horizontal:
        ax.barh(df[x], df[y])
        ax.set_xlabel(y)
        ax.set_ylabel(x)
    else:
        ax.bar(df[x], df[y])
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        plt.xticks(rotation=45)
    
    ax.set_title(title)
    
    if save and filename:
        save_figure(fig, filename)
    
    return fig

