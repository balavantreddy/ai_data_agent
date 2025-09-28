import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from config import MAX_ROWS_FOR_VISUALIZATION, DEFAULT_CHART_HEIGHT, DEFAULT_CHART_WIDTH

class Visualizer:
    def __init__(self):
        self.default_layout = {
            'height': DEFAULT_CHART_HEIGHT,
            'width': DEFAULT_CHART_WIDTH,
            'template': 'plotly_white',
            'margin': dict(l=50, r=50, t=50, b=50)
        }
    
    def create_visualization(
        self,
        df: pd.DataFrame,
        chart_type: str,
        columns: List[str],
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        try:
            # Sample data if too large
            if len(df) > MAX_ROWS_FOR_VISUALIZATION:
                df = df.sample(n=MAX_ROWS_FOR_VISUALIZATION, random_state=42)
            
            fig = None
            
            if chart_type == 'line':
                fig = self._create_line_chart(df, columns, **kwargs)
            elif chart_type == 'bar':
                fig = self._create_bar_chart(df, columns, **kwargs)
            elif chart_type == 'scatter':
                fig = self._create_scatter_plot(df, columns, **kwargs)
            elif chart_type == 'pie':
                fig = self._create_pie_chart(df, columns, **kwargs)
            elif chart_type == 'histogram':
                fig = self._create_histogram(df, columns[0], **kwargs)
            elif chart_type == 'box':
                fig = self._create_box_plot(df, columns, **kwargs)
            elif chart_type == 'heatmap':
                fig = self._create_heatmap(df, columns, **kwargs)
            
            if fig and title:
                fig.update_layout(title=title)
            
            if fig:
                return {
                    'success': True,
                    'plot_data': fig.to_json(),
                    'type': chart_type,
                    'columns_used': columns
                }
            
            return {
                'success': False,
                'error': 'Unsupported chart type'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_line_chart(
        self,
        df: pd.DataFrame,
        columns: List[str],
        **kwargs
    ) -> go.Figure:
        fig = px.line(
            df,
            x=columns[0],
            y=columns[1:],
            **{**self.default_layout, **kwargs}
        )
        return fig
    
    def _create_bar_chart(
        self,
        df: pd.DataFrame,
        columns: List[str],
        **kwargs
    ) -> go.Figure:
        orientation = kwargs.pop('orientation', 'v')
        
        if orientation == 'h':
            fig = px.bar(
                df,
                y=columns[0],
                x=columns[1:],
                orientation='h',
                **{**self.default_layout, **kwargs}
            )
        else:
            fig = px.bar(
                df,
                x=columns[0],
                y=columns[1:],
                **{**self.default_layout, **kwargs}
            )
        return fig
    
    def _create_scatter_plot(
        self,
        df: pd.DataFrame,
        columns: List[str],
        **kwargs
    ) -> go.Figure:
        color_column = kwargs.pop('color', None)
        size_column = kwargs.pop('size', None)
        
        fig = px.scatter(
            df,
            x=columns[0],
            y=columns[1],
            color=color_column,
            size=size_column,
            **{**self.default_layout, **kwargs}
        )
        return fig
    
    def _create_pie_chart(
        self,
        df: pd.DataFrame,
        columns: List[str],
        **kwargs
    ) -> go.Figure:
        fig = px.pie(
            df,
            values=columns[0],
            names=columns[1],
            **{**self.default_layout, **kwargs}
        )
        return fig
    
    def _create_histogram(
        self,
        df: pd.DataFrame,
        column: str,
        **kwargs
    ) -> go.Figure:
        bins = kwargs.pop('bins', 30)
        fig = px.histogram(
            df,
            x=column,
            nbins=bins,
            **{**self.default_layout, **kwargs}
        )
        return fig
    
    def _create_box_plot(
        self,
        df: pd.DataFrame,
        columns: List[str],
        **kwargs
    ) -> go.Figure:
        fig = px.box(
            df,
            x=columns[0] if len(columns) == 1 else columns[0],
            y=columns[1] if len(columns) > 1 else None,
            **{**self.default_layout, **kwargs}
        )
        return fig
    
    def _create_heatmap(
        self,
        df: pd.DataFrame,
        columns: List[str],
        **kwargs
    ) -> go.Figure:
        if len(columns) < 2:
            raise ValueError("Heatmap requires at least 2 columns")
        
        pivot_data = pd.pivot_table(
            df,
            values=columns[2] if len(columns) > 2 else 'count',
            index=columns[0],
            columns=columns[1],
            aggfunc='mean' if len(columns) > 2 else 'count'
        )
        
        fig = px.imshow(
            pivot_data,
            **{**self.default_layout, **kwargs}
        )
        return fig
    
    def suggest_visualization(
        self,
        df: pd.DataFrame,
        columns: List[str]
    ) -> List[Dict[str, Any]]:
        suggestions = []
        
        # Get column types
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        temporal_cols = df.select_dtypes(include=['datetime64']).columns
        
        selected_cols = set(columns)
        
        # Temporal analysis
        temporal_in_selection = any(col in temporal_cols for col in selected_cols)
        if temporal_in_selection:
            time_col = next(col for col in selected_cols if col in temporal_cols)
            numeric_in_selection = [col for col in selected_cols if col in numeric_cols]
            
            if numeric_in_selection:
                suggestions.append({
                    'type': 'line',
                    'columns': [time_col] + numeric_in_selection,
                    'title': f'Trend over time'
                })
        
        # Categorical analysis
        categorical_in_selection = any(col in categorical_cols for col in selected_cols)
        if categorical_in_selection and len(selected_cols & set(numeric_cols)) > 0:
            cat_col = next(col for col in selected_cols if col in categorical_cols)
            num_col = next(col for col in selected_cols if col in numeric_cols)
            
            suggestions.append({
                'type': 'bar',
                'columns': [cat_col, num_col],
                'title': f'{num_col} by {cat_col}'
            })
            
            suggestions.append({
                'type': 'box',
                'columns': [cat_col, num_col],
                'title': f'Distribution of {num_col} by {cat_col}'
            })
        
        # Numeric analysis
        numeric_in_selection = list(selected_cols & set(numeric_cols))
        if len(numeric_in_selection) >= 2:
            suggestions.append({
                'type': 'scatter',
                'columns': numeric_in_selection[:2],
                'title': f'Correlation between {numeric_in_selection[0]} and {numeric_in_selection[1]}'
            })
        
        if len(numeric_in_selection) == 1:
            suggestions.append({
                'type': 'histogram',
                'columns': numeric_in_selection,
                'title': f'Distribution of {numeric_in_selection[0]}'
            })
        
        return suggestions[:3]  # Return top 3 suggestions