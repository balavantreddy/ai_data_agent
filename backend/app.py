from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import pandas as pd
from utils.excel_processor import ExcelProcessor
from utils.ai_agent import AIAgent
from utils.database import DatabaseManager, init_db
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

processor = ExcelProcessor()
ai_agent = AIAgent()
db_manager = DatabaseManager()

# Initialize database
init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only Excel files (.xlsx, .xls) are allowed'}), 400
    
    try:
        # Save file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        # Process file
        result = processor.process_file(filepath)
        
        if result['success']:
            # Store dataset information in database
            dataset_info = {
                'filename': file.filename,
                'file_path': filepath,
                'row_count': result['all_sheets_data'][result['sheets'][0]]['rows'],
                'column_count': result['all_sheets_data'][result['sheets'][0]]['columns'],
                'data_quality': result['all_sheets_data'][result['sheets'][0]]['data_quality'],
                'column_info': {
                    'names': result['all_sheets_data'][result['sheets'][0]]['column_names'],
                    'types': result['all_sheets_data'][result['sheets'][0]]['column_types']
                }
            }
            dataset = db_manager.create_dataset(dataset_info)
            
            result['dataset_id'] = dataset.id
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/query', methods=['POST'])
def process_query():
    data = request.get_json()
    query = data.get('query')
    file_path = data.get('file_path')
    dataset_id = data.get('dataset_id')
    
    if not query or not file_path or not dataset_id:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    start_time = time.time()
    try:
        # Process query
        response = ai_agent.process_query(query, file_path)
        execution_time = time.time() - start_time
        
        # Log query
        db_manager.log_query(
            dataset_id=dataset_id,
            query_text=query,
            execution_time=execution_time,
            success=response['success'],
            result=response if response['success'] else None,
            error_message=response.get('error') if not response['success'] else None
        )
        
        # Get similar queries for context
        similar_queries = db_manager.get_similar_queries(query)
        if similar_queries:
            response['similar_queries'] = similar_queries
        
        return jsonify(response)
        
    except Exception as e:
        execution_time = time.time() - start_time
        db_manager.log_query(
            dataset_id=dataset_id,
            query_text=query,
            execution_time=execution_time,
            success=False,
            error_message=str(e)
        )
        return jsonify({'error': str(e)}), 500

@app.route('/dataset/<int:dataset_id>/history', methods=['GET'])
def get_dataset_history(dataset_id):
    try:
        history = db_manager.get_dataset_history(dataset_id)
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dataset/<int:dataset_id>/insights', methods=['GET'])
def get_dataset_insights(dataset_id):
    try:
        insights = db_manager.get_dataset_insights(dataset_id)
        if insights:
            return jsonify({'success': True, 'insights': insights})
        return jsonify({'error': 'Dataset not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)