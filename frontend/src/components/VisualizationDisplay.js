import React from 'react';
import Plot from 'react-plotly.js';

const VisualizationDisplay = ({ visualizations, analysis, metrics }) => {
  return (
    <div className="visualization-display">
      {analysis && (
        <div className="analysis-text">
          <h3>Analysis</h3>
          <p>{analysis}</p>
        </div>
      )}

      {Object.keys(metrics || {}).length > 0 && (
        <div className="metrics">
          <h3>Key Metrics</h3>
          <div className="metrics-grid">
            {Object.entries(metrics).map(([key, value]) => (
              <div key={key} className="metric-card">
                <h4>{key}</h4>
                <p>{typeof value === 'number' ? value.toLocaleString() : value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {visualizations && visualizations.length > 0 && (
        <div className="visualizations">
          <h3>Visualizations</h3>
          <div className="charts-grid">
            {visualizations.map((viz, index) => (
              <div key={index} className="chart-container">
                {viz.success && (
                  <Plot
                    data={JSON.parse(viz.plot_data)}
                    layout={{
                      title: viz.title,
                      height: 400,
                      width: 600,
                      margin: { t: 50, r: 50, b: 50, l: 50 }
                    }}
                    config={{ responsive: true }}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default VisualizationDisplay;