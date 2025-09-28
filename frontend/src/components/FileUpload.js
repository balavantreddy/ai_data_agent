import React, { useRef, useState } from 'react';
import { Upload, AlertTriangle, X } from 'lucide-react';

const ERROR_MESSAGES = {
  file_too_large: 'File size exceeds 16MB limit. Please upload a smaller file.',
  password_protected: 'Password protected Excel files are not supported. Please remove the password protection.',
  invalid_file: 'Invalid or corrupt Excel file. Please check the file and try again.',
  no_sheets: 'Excel file contains no sheets. Please add data to the file.',
  no_valid_sheets: 'No valid sheets found in the file. Please ensure sheets contain valid data.',
  empty_sheet: 'One or more sheets are empty. Please add data to the sheets.',
  insufficient_data: 'Sheets must contain at least 2 rows and 2 columns of data.',
  low_quality_data: 'One or more sheets contain too much missing data (>50%).',
  general_error: 'An error occurred while processing the file.',
  type_error: 'Please upload an Excel file (.xlsx or .xls)'
};

const FileUpload = ({ onFileUpload, loading, error }) => {
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setValidationError(null);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      handleFileValidation(file);
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileValidation(file);
    }
  };

  const handleFileValidation = (file) => {
    // Reset previous errors
    setValidationError(null);

    // Check file type
    const validTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'application/vnd.ms-excel.sheet.macroenabled.12'
    ];
    
    if (!validTypes.includes(file.type)) {
      setValidationError('type_error');
      return;
    }

    // Check file size (16MB limit)
    const maxSize = 16 * 1024 * 1024; // 16MB in bytes
    if (file.size > maxSize) {
      setValidationError('file_too_large');
      return;
    }

    // If all validations pass, process the file
    onFileUpload(file);
  };

  return (
    <div className="file-upload">
      <div 
        className={`upload-area ${dragActive ? 'drag-active' : ''} ${(error || validationError) ? 'has-error' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.xlsm"
          onChange={handleFileInput}
          style={{ display: 'none' }}
        />
        
        {loading ? (
          <div className="upload-status loading">
            <div className="spinner"></div>
            <p>Processing your file...</p>
          </div>
        ) : (
          <div className="upload-status">
            <Upload size={48} className={error || validationError ? 'error-icon' : ''} />
            <p className="upload-text">
              Drag and drop or click to upload Excel files
            </p>
            <p className="upload-hint">
              Supported formats: .xlsx, .xls (up to 16MB)
            </p>
          </div>
        )}

        {(error || validationError) && (
          <div className="error-message">
            <AlertTriangle size={20} />
            <span>{ERROR_MESSAGES[validationError] || error}</span>
            <button 
              className="clear-error"
              onClick={(e) => {
                e.stopPropagation();
                setValidationError(null);
              }}
            >
              <X size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;