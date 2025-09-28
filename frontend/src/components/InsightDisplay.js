import React from 'react';
import { File, FileText, AlertTriangle } from 'lucide-react';

const InsightDisplay = ({ insights, fileInfo }) => {
  const mainSheet = fileInfo.all_sheets_data[fileInfo.sheets[0]];
  
  return (
    <div className="insight-display">
      <div className="file-overview">
        <div className="file-header">
          <File size={24} />
          <h3>{fileInfo.filename}</h3>
        </div>
        
        <div className="file-stats">
          <div className="stat">
            <span>Sheets</span>
            <strong>{fileInfo.sheets.length}</strong>
          </div>
          <div className="stat">
            <span>Rows</span>
            <strong>{mainSheet.rows.toLocaleString()}</strong>
          </div>
          <div className="stat">
            <span>Columns</span>
            <strong>{mainSheet.columns}</strong>
          </div>
        </div>
      </div>

      <div className="data-quality">
        <h3>Data Quality</h3>
        <div className="quality-stats">
          <div className="quality-stat">
            <div className="stat-bar">
              <div 
                className="stat-fill" 
                style={{ width: `${mainSheet.data_quality.completeness}%` }}
              />
            </div>
            <span>Completeness</span>
            <strong>{mainSheet.data_quality.completeness}%</strong>
          </div>
          {mainSheet.data_quality.duplicate_rows > 0 && (
            <div className="quality-warning">
              <AlertTriangle size={16} />
              <span>{mainSheet.data_quality.duplicate_rows} duplicate rows found</span>
            </div>
          )}
        </div>

        {Object.entries(mainSheet.data_quality.type_consistency || {}).map(([col, status]) => (
          status === 'mixed' && (
            <div key={col} className="quality-warning">
              <AlertTriangle size={16} />
              <span>Mixed data types in column: {col}</span>
            </div>
          )
        ))}
      </div>

      {insights && (
        <div className="data-insights">
          <h3>Data Insights</h3>
          
          {insights.summary_stats && (
            <div className="insights-section">
              <h4>Summary Statistics</h4>
              <div className="summary-grid">
                {Object.entries(insights.summary_stats).map(([col, stats]) => (
                  <div key={col} className="stat-card">
                    <h5>{col}</h5>
                    <div className="stat-details">
                      <div>Mean: {Number(stats.mean).toFixed(2)}</div>
                      <div>Median: {Number(stats['50%']).toFixed(2)}</div>
                      <div>Std: {Number(stats.std).toFixed(2)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {insights.correlations && Object.keys(insights.correlations).length > 0 && (
            <div className="insights-section">
              <h4>Strong Correlations</h4>
              <ul>
                {Object.entries(insights.correlations).map(([col1, corr]) => (
                  Object.entries(corr).map(([col2, value]) => (
                    Math.abs(value) > 0.7 && col1 !== col2 && (
                      <li key={`${col1}-${col2}`}>
                        {col1} and {col2}: {value.toFixed(2)}
                      </li>
                    )
                  ))
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default InsightDisplay;