import React, { useState } from 'react';
import FileUpload from './FileUpload';
import QueryInput from './QueryInput';
import VisualizationDisplay from './VisualizationDisplay';
import InsightDisplay from './InsightDisplay';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const DataAgent = () => {
  const [currentFile, setCurrentFile] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  const [warnings, setWarnings] = useState([]);

  const handleFileUpload = async (file) => {
    setLoading(true);
    setError(null);
    setWarnings([]);
    setCurrentFile(null);
    setInsights(null);
    setAnalysisResult(null);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (!response.data.success) {
        setError(response.data.error);
        if (response.data.sheet_errors) {
          setWarnings(response.data.sheet_errors.map(err => ({
            type: 'sheet_error',
            message: `Sheet "${err.sheet}": ${err.error}`,
            severity: 'error'
          })));
        }
        return;
      }
      
      // Collect all warnings from sheets
      const allWarnings = [];
      Object.entries(response.data.all_sheets_data).forEach(([sheetName, sheetData]) => {
        if (sheetData.warnings && sheetData.warnings.length > 0) {
          sheetData.warnings.forEach(warning => {
            allWarnings.push({
              ...warning,
              sheet: sheetName
            });
          });
        }
      });
      setWarnings(allWarnings);
      
      setCurrentFile({
        ...response.data,
        originalFile: file
      });
      
      if (response.data.insights) {
        setInsights(response.data.insights);
      }
      
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Error uploading file';
      const errorType = err.response?.data?.error_type;
      setError(errorType ? errorMessage : 'Error uploading file');
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = async (query) => {
    if (!currentFile) {
      setError('Please upload a file first');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/query`, {
        query,
        file_path: currentFile.file_path,
        dataset_id: currentFile.dataset_id
      });
      
      setAnalysisResult(response.data);
      
    } catch (err) {
      setError(err.response?.data?.error || 'Error processing query');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="data-agent">
      <header>
        <h1>AI Data Assistant</h1>
        <p>Upload your Excel file and ask questions about your data</p>
      </header>

      <FileUpload 
        onFileUpload={handleFileUpload}
        loading={loading}
        error={error}
      />

      {currentFile && (
        <div className="data-workspace">
          {warnings.length > 0 && (
            <div className="warnings-container">
              {warnings.map((warning, index) => (
                <div 
                  key={index} 
                  className={`warning-message ${warning.severity || 'warning'}`}
                >
                  <div className="warning-header">
                    {warning.sheet && (
                      <span className="warning-sheet">{warning.sheet}</span>
                    )}
                    <span className="warning-type">
                      {warning.type === 'sheet_error' ? 'Error' : 'Warning'}
                    </span>
                  </div>
                  <p>{warning.message}</p>
                </div>
              ))}
            </div>
          )}

          <QueryInput 
            onSubmit={handleQuery}
            disabled={loading}
          />
          
          {insights && (
            <InsightDisplay 
              insights={insights}
              fileInfo={currentFile}
            />
          )}

          {analysisResult && (
            <div className="analysis-results">
              <VisualizationDisplay 
                visualizations={analysisResult.visualizations}
                analysis={analysisResult.analysis}
                metrics={analysisResult.metrics}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DataAgent;