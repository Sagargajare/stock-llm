import pandas as pd
from sqlalchemy import create_engine, text
from schema import schema
import os

# PostgreSQL URI
POSTGRES_URI = os.getenv('POSTGRES_URI')

def create_database():
    # Create SQLAlchemy engine with connection pooling
    engine = create_engine(POSTGRES_URI, pool_pre_ping=True)
    
    try:
        with engine.connect() as conn:
            # Drop and create table
            print("Dropping existing table if exists...")
            conn.execute(text("DROP TABLE IF EXISTS stock_prices"))
            
            print("Creating table...")
            conn.execute(text(schema))
            conn.commit()

            # Read the CSV file
            print("Reading CSV file...")
            df = pd.read_csv('stocks_df.csv')

            # Rename columns to match schema
            column_mapping = {
                'Date': 'date',
                'Stock': 'stock',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Change Pct': 'change_pct',
            }
            df = df.rename(columns=column_mapping)

            required_columns = ['date', 'stock', 'open', 'high', 'low', 'close', 'volume', 'change_pct']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in CSV: {missing_columns}")

            # Convert date column to date object
            df['date'] = pd.to_datetime(df['date']).dt.date

            # Insert data in chunks to handle large datasets
            print("Inserting data into PostgreSQL...")
            chunk_size = 1000  # Adjust based on your data size
            total_rows = len(df)
            
            for i in range(0, total_rows, chunk_size):
                chunk = df.iloc[i:i + chunk_size]
                try:
                    chunk.to_sql('stock_prices', engine, if_exists='append', index=False, method='multi')
                    print(f"Inserted rows {i+1} to {min(i+chunk_size, total_rows)} of {total_rows}")
                except Exception as e:
                    print(f"Error inserting chunk starting at row {i+1}: {str(e)}")
                    raise

            # Create index for performance
            print("Creating indexes...")
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_stock_date ON stock_prices(stock, date)'))
            conn.commit()

            print("PostgreSQL database creation completed successfully!")

    except Exception as e:
        print(f"Error during database creation: {str(e)}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    create_database() 