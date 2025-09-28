import React, { useState } from 'react';
import { Search } from 'lucide-react';

const QueryInput = ({ onSubmit, disabled }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query.trim());
    }
  };

  return (
    <div className="query-input">
      <form onSubmit={handleSubmit}>
        <div className="input-container">
          <Search size={20} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask questions about your data..."
            disabled={disabled}
          />
        </div>
        <button 
          type="submit" 
          disabled={disabled || !query.trim()}
        >
          {disabled ? 'Processing...' : 'Analyze'}
        </button>
      </form>
      <div className="query-suggestions">
        <p>Try asking:</p>
        <ul>
          <li>What's the total sales by region?</li>
          <li>Show me the top 5 products</li>
          <li>Create a trend analysis of monthly revenue</li>
        </ul>
      </div>
    </div>
  );
};

export default QueryInput;