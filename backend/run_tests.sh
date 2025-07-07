#!/bin/bash

# Script to run tests with proper output
echo "Starting test execution..."

# Activate virtual environment if not already active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create test database
echo "Creating test database..."
python -c "
import asyncio
import asyncpg

async def create_test_db():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='kuroibara',
            password='password',
            database='postgres'
        )
        await conn.execute('CREATE DATABASE test_kuroibara;')
        print('Test database created successfully!')
        await conn.close()
    except Exception as e:
        if 'already exists' in str(e).lower():
            print('Test database already exists!')
        else:
            print(f'Error: {e}')

asyncio.run(create_test_db())
"

# Run the tests
echo "Running tests..."
python -m pytest tests/test_api.py::test_api_docs -v

echo "Test execution completed!"
