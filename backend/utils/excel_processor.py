import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import re

class ExcelProcessor:
    def __init__(self):
        self.type_patterns = {
            'date': [
                r'\d{4}-\d{2}-\d{2}',
                r'\d{2}/\d{2}/\d{4}',
                r'\d{2}-\d{2}-\d{4}'
            ],
            'amount': [
                r'^\$?\d+\.?\d*$',
                r'^\d+\.?\d*\s?USD$'
            ],
            'percentage': [
                r'^\d+\.?\d*\s?%$',
                r'^\d+\.?\d*$'
            ]
        }

    def process_file(self, filepath: str) -> Dict[str, Any]:
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                return {
                    'success': False, 
                    'error': 'File not found',
                    'error_type': 'file_not_found'
                }
            
            # Check file size
            file_size = os.path.getsize(filepath) / (1024 * 1024)  # Convert to MB
            if file_size > 16:
                return {
                    'success': False,
                    'error': 'File size exceeds 16MB limit',
                    'error_type': 'file_too_large'
                }
            
            try:
                # Try to open the Excel file
                excel_file = pd.ExcelFile(filepath)
                
            except xlrd.biffh.XLRDError as e:
                if "Password protected" in str(e):
                    return {
                        'success': False,
                        'error': 'Password protected Excel files are not supported',
                        'error_type': 'password_protected'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Invalid or corrupt Excel file',
                        'error_type': 'invalid_file'
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'error': 'Error opening Excel file: ' + str(e),
                    'error_type': 'open_error'
                }
            
            # Get sheets
            sheets = excel_file.sheet_names
            if not sheets:
                return {
                    'success': False,
                    'error': 'Excel file contains no sheets',
                    'error_type': 'no_sheets'
                }
            
            all_sheets_data = {}
            sheet_errors = []
            
            for sheet in sheets:
                try:
                    df = pd.read_excel(filepath, sheet_name=sheet)
                    
                    # Check if sheet is empty
                    if df.empty:
                        sheet_errors.append({
                            'sheet': sheet,
                            'error': 'Empty sheet',
                            'error_type': 'empty_sheet'
                        })
                        continue
                        
                    # Check minimum size
                    if len(df) < 2 or len(df.columns) < 2:
                        sheet_errors.append({
                            'sheet': sheet,
                            'error': 'Sheet must contain at least 2 rows and 2 columns',
                            'error_type': 'insufficient_data'
                        })
                        continue
                    
                    cleaned_df = self._clean_data(df)
                    data_quality = self._assess_quality(cleaned_df)
                    
                    # Check data quality thresholds
                    if data_quality['completeness'] < 50:
                        sheet_errors.append({
                            'sheet': sheet,
                            'error': 'Sheet contains too much missing data (>50%)',
                            'error_type': 'low_quality_data'
                        })
                        continue
                    
                    sheet_info = {
                        'rows': len(cleaned_df),
                        'columns': len(cleaned_df.columns),
                        'preview': cleaned_df.head().to_dict('records'),
                        'column_names': cleaned_df.columns.tolist(),
                        'column_types': self._infer_column_types(cleaned_df),
                        'data_quality': data_quality,
                        'suggested_names': self._suggest_column_names(cleaned_df),
                        'warnings': []
                    }
                    
                    # Add warnings for data quality issues
                    if data_quality['duplicate_rows'] > 0:
                        sheet_info['warnings'].append({
                            'type': 'duplicate_rows',
                            'message': f"Found {data_quality['duplicate_rows']} duplicate rows",
                            'severity': 'warning'
                        })
                    
                    mixed_type_cols = [
                        col for col, status in data_quality['type_consistency'].items()
                        if status == 'mixed'
                    ]
                    if mixed_type_cols:
                        sheet_info['warnings'].append({
                            'type': 'mixed_types',
                            'message': f"Mixed data types found in columns: {', '.join(mixed_type_cols)}",
                            'severity': 'warning'
                        })
                    
                    # Check for potentially problematic column names
                    if any(' ' in col for col in cleaned_df.columns):
                        sheet_info['warnings'].append({
                            'type': 'column_names',
                            'message': "Some column names contain spaces",
                            'severity': 'info'
                        })
                    
                    all_sheets_data[sheet] = sheet_info
                    
                except Exception as e:
                    sheet_errors.append({
                        'sheet': sheet,
                        'error': str(e),
                        'error_type': 'sheet_processing_error'
                    })
            
            # Check if any sheets were processed successfully
            if not all_sheets_data:
                return {
                    'success': False,
                    'error': 'No valid sheets found in file',
                    'error_type': 'no_valid_sheets',
                    'sheet_errors': sheet_errors
                }
            
            # Process main sheet for general insights
            try:
                main_df = pd.read_excel(filepath, sheet_name=0)
                cleaned_main_df = self._clean_data(main_df)
                insights = self._analyze_data(cleaned_main_df)
            except Exception as e:
                insights = None
            
            return {
                'success': True,
                'sheets': sheets,
                'all_sheets_data': all_sheets_data,
                'insights': insights,
                'sheet_errors': sheet_errors if sheet_errors else None,
                'file_path': filepath
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'general_error'
            }
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Handle unnamed columns
        df.columns = [f'column_{i}' if 'Unnamed' in str(col) else str(col).strip() 
                     for i, col in enumerate(df.columns)]
        
        # Remove empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean column names
        df.columns = [self._clean_column_name(col) for col in df.columns]
        
        # Handle inconsistent data types
        df = self._standardize_data_types(df)
        
        return df
    
    def _clean_column_name(self, name: str) -> str:
        # Remove special characters and spaces
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
        # Remove multiple underscores
        clean_name = re.sub(r'_+', '_', clean_name)
        # Remove leading/trailing underscores
        clean_name = clean_name.strip('_').lower()
        return clean_name if clean_name else 'unnamed_column'
    
    def _standardize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            # Sample non-null values
            sample = df[col].dropna().head(100)
            
            if len(sample) == 0:
                continue
                
            # Check for dates
            if all(self._is_date(str(x)) for x in sample):
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Check for numeric values
            elif all(self._is_numeric(str(x)) for x in sample):
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            # Check for percentages
            elif all(self._is_percentage(str(x)) for x in sample):
                df[col] = df[col].apply(lambda x: 
                    pd.to_numeric(str(x).rstrip('%'), errors='coerce') / 100)
            
            # Check for currency
            elif all(self._is_currency(str(x)) for x in sample):
                df[col] = df[col].apply(lambda x: 
                    pd.to_numeric(re.sub(r'[^\d.-]', '', str(x)), errors='coerce'))
        
        return df
    
    def _is_date(self, value: str) -> bool:
        for pattern in self.type_patterns['date']:
            if re.match(pattern, value):
                return True
        try:
            pd.to_datetime(value)
            return True
        except:
            return False
    
    def _is_numeric(self, value: str) -> bool:
        try:
            float(re.sub(r'[^\d.-]', '', value))
            return True
        except:
            return False
    
    def _is_percentage(self, value: str) -> bool:
        for pattern in self.type_patterns['percentage']:
            if re.match(pattern, value):
                return True
        return False
    
    def _is_currency(self, value: str) -> bool:
        for pattern in self.type_patterns['amount']:
            if re.match(pattern, value):
                return True
        return False
    
    def _infer_column_types(self, df: pd.DataFrame) -> Dict[str, str]:
        column_types = {}
        for col in df.columns:
            if df[col].dtype == 'datetime64[ns]':
                column_types[col] = 'date'
            elif df[col].dtype in ['int64', 'float64']:
                if all(0 <= x <= 1 for x in df[col].dropna()):
                    column_types[col] = 'percentage'
                else:
                    column_types[col] = 'numeric'
            else:
                column_types[col] = 'text'
        return column_types
    
    def _suggest_column_names(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        suggestions = {}
        common_patterns = {
            'date': ['date', 'time', 'year', 'month', 'day'],
            'amount': ['price', 'cost', 'amount', 'revenue', 'sales'],
            'quantity': ['quantity', 'units', 'count', 'number'],
            'location': ['country', 'region', 'city', 'state', 'location'],
            'product': ['product', 'item', 'sku', 'category'],
            'customer': ['customer', 'client', 'account', 'user']
        }
        
        for col in df.columns:
            if 'column_' in col or 'unnamed' in col:
                sample_values = df[col].dropna().head(10)
                suggested_names = []
                
                # Check data type patterns
                for category, patterns in common_patterns.items():
                    if any(pattern in col.lower() for pattern in patterns):
                        suggested_names.extend(patterns)
                
                # Add data type specific suggestions
                if df[col].dtype == 'datetime64[ns]':
                    suggested_names.extend(common_patterns['date'])
                elif df[col].dtype in ['int64', 'float64']:
                    if all(0 <= x <= 1 for x in df[col].dropna()):
                        suggested_names.append('percentage')
                    else:
                        suggested_names.extend(common_patterns['amount'])
                        suggested_names.extend(common_patterns['quantity'])
                
                suggestions[col] = list(set(suggested_names))
        
        return suggestions
    
    def _assess_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        duplicate_rows = df.duplicated().sum()
        
        # Check for inconsistent data types
        type_consistency = {}
        for col in df.columns:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                main_type = type(non_null.iloc[0])
                consistent = all(isinstance(x, main_type) for x in non_null)
                type_consistency[col] = 'consistent' if consistent else 'mixed'
        
        return {
            'completeness': int((1 - missing_cells/total_cells) * 100),
            'duplicate_rows': int(duplicate_rows),
            'row_count': len(df),
            'type_consistency': type_consistency,
            'missing_values_by_column': df.isnull().sum().to_dict()
        }
            'consistency': 85,  # Mock
            'accuracy': 90      # Mock
        }
    
    def _analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        insights = {
            'summary_stats': {},
            'correlations': {},
            'unique_counts': {},
            'data_distribution': {}
        }
        
        # Summary statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            insights['summary_stats'] = df[numeric_cols].describe().to_dict()
            
            # Correlations between numeric columns
            if len(numeric_cols) > 1:
                insights['correlations'] = df[numeric_cols].corr().to_dict()
        
        # Unique value counts for categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            unique_counts = df[col].value_counts().head(10).to_dict()
            insights['unique_counts'][col] = unique_counts
        
        # Data distribution for numeric columns
        for col in numeric_cols:
            insights['data_distribution'][col] = {
                'histogram_data': np.histogram(df[col].dropna(), bins=10),
                'skewness': float(df[col].skew()),
                'kurtosis': float(df[col].kurtosis())
            }
        
        return insights
        insights = []
        
        # Numeric columns analysis
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            insights.append(f"Found {len(numeric_cols)} numeric columns")
        
        # Categorical analysis
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            insights.append(f"Found {len(categorical_cols)} text columns")
        
        insights.append(f"Dataset contains {len(df)} records")
        
        return insights