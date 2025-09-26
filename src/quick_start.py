#!/usr/bin/env python3

import os
import sys
import subprocess

def check_python_version():
    if sys.version_info < (3, 8):
        print("Python 3.8 or higher is required.")
        return False
    print(f'Python version {sys.version_info.major}.{sys.version_info.minor} detected.')
    return True

def install_dependencies():
    print("Installing dependencies from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("All dependencies are installed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def check_env_file():
    if not os.path.exists('.env'):
        print(".env file is missing. Please create one based on .env.example.")
        return False
    print(".env file found.")
    return True

def create_directories():
    dirs = ['data', 'logs']
    for dir in dirs:
        os.makedirs(dir, exist_ok=True)
        print(f"Directory '{dir}' is ready.")

def check_dataset():
    data_path = 'data/cocktails.csv'
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}")
        print("Please download from: https://www.kaggle.com/datasets/aadyasingh55/cocktails/data")
        return False
    print("Dataset found.")
    return True

def main():
    print("Starting quick setup...")
    print('=' * 40)

    if not check_python_version():
        return
    create_directories()
    if not check_env_file():
        return
    if not install_dependencies():
        return
    
    dataset_exists = check_dataset()

    print('Setup complete.\n')
    print('Next steps:')
    print('1. Configure your database settings in the .env file.')
    if dataset_exists:
        print('2. Run: python src/database_setup.py')
        print('3. Run: python src/data_preprocessing.py')
    else:
        print('2. Download the dataset and place it in the data/ directory.')
        print('3. Then run: python src/database_setup.py')
        print('4. Then run: python src/data_preprocessing.py')
    print('4. Run: streamlit run src/app.py')

    print("\nVerifying installations...")
    try:
        import streamlit
        print("✅ Streamlit installed")
    except ImportError:
        print("❌ Streamlit not installed")
    
    try:
        import psycopg2
        print("✅ psycopg2 installed")
    except ImportError:
        print("❌ psycopg2 not installed")
    
    try:
        import sentence_transformers
        print("✅ sentence-transformers installed")
    except ImportError:
        print("❌ sentence-transformers not installed")

if __name__ == "__main__":
    main()