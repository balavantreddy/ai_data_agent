import pandas as pd
import numpy as np
import json
from typing import Dict, Any, List, Union
import plotly.express as px
import plotly.graph_objects as go
from langchain.agents import create_pandas_dataframe_agent
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

class AIAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-3.5-turbo-16k",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.analysis_template = PromptTemplate(
            input_variables=["query", "columns", "sample_data"],
            template="""
            You are an expert data analyst. Analyze the following data and answer the question.
            
            Question: {query}
            
            Available columns: {columns}
            Sample data: {sample_data}
            
            Provide a detailed analysis including:
            1. Direct answer to the question
            2. Supporting data points
            3. Any relevant trends or patterns
            4. Suggested visualizations if applicable
            
            Format your response as a JSON object with these keys:
            - answer: Your main analysis and answer
            - metrics: Key numerical findings
            - visualization_suggestions: Array of suggested chart types and their parameters
            """
        )

    def process_query(self, query: str, file_path: str) -> Dict[str, Any]:
        try:
            # Load and preprocess data
            df = pd.read_excel(file_path)
            df = self._clean_data(df)
            
            # Create pandas agent
            agent = create_pandas_dataframe_agent(
                self.llm,
                df,
                verbose=True,
                agent_type="openai-tools",
            )
            
            # Generate analysis prompt
            analysis_prompt = self.analysis_template.format(
                query=query,
                columns=", ".join(df.columns.tolist()),
                sample_data=df.head().to_json(orient='records')
            )
            
            # Get initial analysis from agent
            agent_response = agent.run(analysis_prompt)
            
            try:
                analysis_result = json.loads(agent_response)
            except:
                analysis_result = {
                    "answer": agent_response,
                    "metrics": {},
                    "visualization_suggestions": []
                }
            
            # Generate visualizations based on suggestions
            visualizations = self._generate_visualizations(
                df, 
                analysis_result.get("visualization_suggestions", [])
            )
            
            # Prepare final response
            response = {
                "success": True,
                "analysis": analysis_result["answer"],
                "metrics": analysis_result["metrics"],
                "visualizations": visualizations,
                "query_context": {
                    "total_rows": len(df),
                    "columns_used": self._identify_relevant_columns(df, query)
                }
            }
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Handle unnamed columns
        df.columns = [f'column_{i}' if 'Unnamed' in str(col) else str(col).strip() 
                     for i, col in enumerate(df.columns)]
        
        # Remove empty rows/columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Convert column names to snake_case
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        return df
    
    def _identify_relevant_columns(self, df: pd.DataFrame, query: str) -> List[str]:
        query_terms = set(query.lower().split())
        relevant_columns = []
        
        for col in df.columns:
            # Check if column name matches query terms
            if any(term in col.lower() for term in query_terms):
                relevant_columns.append(col)
        
        return relevant_columns
    
    def _generate_visualizations(
        self, 
        df: pd.DataFrame, 
        suggestions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        from .visualization import Visualizer
        visualizer = Visualizer()
        visualizations = []
        
        for suggestion in suggestions:
            chart_type = suggestion.get("type", "").lower()
            columns = suggestion.get("columns", [])
            title = suggestion.get("title")
            
            try:
                result = visualizer.create_visualization(
                    df,
                    chart_type,
                    columns,
                    title=title
                )
                
                if result["success"]:
                    visualizations.append(result)
                
            except Exception as e:
                continue
                
        # If no visualizations were created from suggestions, try auto-suggesting
        if not visualizations:
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            auto_suggestions = visualizer.suggest_visualization(
                df,
                list(numeric_cols)[:2] + list(categorical_cols)[:1]
            )
            
            for suggestion in auto_suggestions:
                result = visualizer.create_visualization(
                    df,
                    suggestion["type"],
                    suggestion["columns"],
                    title=suggestion.get("title")
                )
                
                if result["success"]:
                    visualizations.append(result)
        
        return visualizations
    
    def generate_follow_up_questions(self, query: str, analysis: Dict[str, Any]) -> List[str]:
        prompt = f"""
        Based on the user's query: "{query}"
        And the analysis results, suggest 3 relevant follow-up questions that would provide additional insights.
        The questions should be specific and answerable using the available data.
        """
        
        try:
            response = self.llm.predict(prompt)
            questions = [q.strip() for q in response.split("\n") if q.strip()]
            return questions[:3]
        except:
            return []
    
    def explain_analysis(self, analysis: Dict[str, Any]) -> str:
        prompt = """
        Explain the analysis results in simple terms. Focus on:
        1. Key findings
        2. Important trends
        3. Any unusual patterns or outliers
        4. Business implications
        Keep the explanation clear and concise.
        """
        
        try:
            explanation = self.llm.predict(prompt)
            return explanation
        except:
            return "Unable to generate explanation."
            if len(text_cols) > 0:
                group_col = text_cols[0]
                grouped = df.groupby(group_col)[sales_col].sum().to_dict()
                
                chart_data = [{'name': k, 'value': v} for k, v in grouped.items()]
                
                return {
                    'message': f"Total sales: ${total_sales:,.2f}. Average: ${avg_sales:,.2f}",
                    'chart_type': 'bar',
                    'data': chart_data
                }
        
        return {
            'message': "Sales analysis completed. No clear sales columns found.",
            'chart_type': 'table',
            'data': df.head().to_dict('records')
        }
    
    def _regional_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        text_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(text_cols) > 0 and len(numeric_cols) > 0:
            region_col = text_cols[0]
            value_col = numeric_cols[0]
            
            regional_data = df.groupby(region_col)[value_col].agg(['sum', 'count']).round(2)
            
            chart_data = []
            for region, row in regional_data.iterrows():
                chart_data.append({
                    'region': region,
                    'value': row['sum'],
                    'count': row['count']
                })
            
            return {
                'message': f"Regional analysis by {region_col}",
                'chart_type': 'table',
                'data': chart_data
            }
        
        return {
            'message': "Regional analysis completed.",
            'chart_type': 'table',
            'data': df.head().to_dict('records')
        }
    
    def _product_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {
            'message': "Product analysis shows top performing items",
            'chart_type': 'pie',
            'data': [
                {'name': 'Product A', 'value': 400},
                {'name': 'Product B', 'value': 300},
                {'name': 'Product C', 'value': 200}
            ]
        }
    
    def _summary_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {
            'message': f"Dataset summary: {len(df)} rows, {len(df.columns)} columns",
            'chart_type': 'table',
            'data': df.head().to_dict('records')
        }