from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import csv
from io import StringIO
from openai import OpenAI
from sqlalchemy import text
from flask_cors import CORS

app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
CORS(app)  # Enable CORS for all routes

# Configure OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# PostgreSQL URI
POSTGRES_URI = os.getenv('POSTGRES_URI')

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRES_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Stock Price Model
class StockPrice(db.Model):
    __tablename__ = 'stock_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    stock = db.Column(db.String(50), nullable=False)
    open = db.Column(db.Numeric(10, 2))
    high = db.Column(db.Numeric(10, 2))
    low = db.Column(db.Numeric(10, 2))
    close = db.Column(db.Numeric(10, 2))
    volume = db.Column(db.BigInteger)
    change_pct = db.Column(db.Numeric(5, 2))

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'stock': self.stock,
            'open': float(self.open) if self.open else None,
            'high': float(self.high) if self.high else None,
            'low': float(self.low) if self.low else None,
            'close': float(self.close) if self.close else None,
            'volume': self.volume,
            'change_pct': float(self.change_pct) if self.change_pct else None
        }

# Create all database tables
with app.app_context():
    db.create_all()

EXPECTED_COLUMNS = [
    'Date', 'Stock', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change Pct'
]

@app.route('/api/stocks/upload_csv', methods=['POST'])
def upload_csv():
    print("Uploading CSV...")
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'File is not a CSV'}), 400

        stream = StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        
        # Validate columns
        if reader.fieldnames != EXPECTED_COLUMNS:
            return jsonify({'error': f'CSV columns do not match expected schema. Expected: {EXPECTED_COLUMNS}, Found: {reader.fieldnames}'}), 400

        records = []
        for row in reader:
            try:
                record = StockPrice(
                    date=datetime.strptime(row['Date'], '%Y-%m-%d').date(),
                    stock=row['Stock'],
                    open=row['Open'] if row['Open'] else None,
                    high=row['High'] if row['High'] else None,
                    low=row['Low'] if row['Low'] else None,
                    close=row['Close'] if row['Close'] else None,
                    volume=int(row['Volume']) if row['Volume'] else None,
                    change_pct=row['Change Pct'] if row['Change Pct'] else None
                )
                records.append(record)
            except Exception as e:
                return jsonify({'error': f'Error processing row: {row}, error: {str(e)}'}), 400

        try:
            # Insert in chunks to handle large datasets
            chunk_size = 1000
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i + chunk_size]
                db.session.bulk_save_objects(chunk)
                db.session.commit()
            return jsonify({'message': f'Successfully uploaded {len(records)} records.'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add new endpoint for natural language queries
@app.route('/api/query', methods=['POST'])
def query_stocks():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400

        user_query = data['query']
        
        # Use OpenAI to understand the query and generate SQL
        sql_prompt = f"""
        Given the following PostgreSQL database schema:
        Table: stock_prices
        Columns: id (SERIAL), date (DATE), stock (VARCHAR), open (NUMERIC), high (NUMERIC), low (NUMERIC), close (NUMERIC), volume (BIGINT), change_pct (NUMERIC)
        
        Convert this natural language query into PostgreSQL SQL: {user_query}
        
        Important PostgreSQL rules:
        1. When using aggregate functions (MAX, MIN, AVG, SUM, COUNT), any non-aggregated column in SELECT must be in GROUP BY
        2. Use PostgreSQL syntax only (e.g., use CURRENT_DATE instead of date('now'))
        3. For date operations, use PostgreSQL date functions (e.g., CURRENT_DATE - INTERVAL '1 month')
        4. Return ONLY the raw SQL query without any markdown formatting or backticks
        5. Do not include any explanations or comments
        6. Always include GROUP BY when using aggregate functions with non-aggregated columns
        
        Example correct queries:
        - "What was the highest price for each stock?" should be:
          SELECT stock, MAX(high) AS highest_price FROM stock_prices GROUP BY stock;
        - "What is the average volume per stock?" should be:
          SELECT stock, AVG(volume) AS avg_volume FROM stock_prices GROUP BY stock;
        - "Show me the latest price for each stock" should be:
          SELECT stock, close FROM stock_prices WHERE date = (SELECT MAX(date) FROM stock_prices);
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a PostgreSQL expert that converts natural language queries into PostgreSQL SQL. Always follow PostgreSQL's GROUP BY rules and return only the raw SQL query without any formatting or explanation."},
                {"role": "user", "content": sql_prompt}
            ],
            temperature=0.1
        )
        
        sql_query = response.choices[0].message.content.strip()
        # Remove any markdown formatting if present
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        # Execute the SQL query
        try:
            result = db.session.execute(text(sql_query))
            rows = result.fetchall()
            
            # Convert results to list of dictionaries
            columns = result.keys()
            results = [dict(zip(columns, row)) for row in rows]
            
            # Generate natural language response
            nl_prompt = f"""
            Given the following query: "{user_query}"
            And the following results: {results}
            
            Provide a natural language summary of these results. Focus on the key insights and trends.
            Keep the response concise but informative. Include specific numbers and dates where relevant.
            """
            
            nl_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial analyst that explains stock data in clear, natural language."},
                    {"role": "user", "content": nl_prompt}
                ],
                temperature=0.7
            )
            
            natural_language_summary = nl_response.choices[0].message.content.strip()
            
            return jsonify({
                'query': user_query,
                'sql': sql_query,
                'results': results,
                'summary': natural_language_summary
            })
            
        except Exception as e:
            return jsonify({'error': f'Error executing query: {str(e)}'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)), debug=os.getenv('FLASK_ENV') != 'production')
