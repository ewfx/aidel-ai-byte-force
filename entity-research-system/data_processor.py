import pandas as pd
import json
import csv
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def process_file(file_path):
    """
    Process uploaded file and convert it to a standardized format
    Supports CSV, Excel, JSON formats
    
    Args:
        file_path (str): Path to the uploaded file
        
    Returns:
        list: List of transaction dictionaries
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.csv':
            return process_csv(file_path)
        elif file_ext in ['.xls', '.xlsx']:
            return process_excel(file_path)
        elif file_ext == '.json':
            return process_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        raise

def process_csv(file_path):
    """Process CSV file into transactions"""
    try:
        df = pd.read_csv(file_path)
        return standardize_dataframe(df)
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        # Try alternative CSV parsing with different encoding or delimiter
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                dialect = csv.Sniffer().sniff(f.read(1024))
                f.seek(0)
                df = pd.read_csv(file_path, sep=dialect.delimiter)
                return standardize_dataframe(df)
        except Exception as nested_e:
            logger.error(f"Second attempt at CSV processing failed: {str(nested_e)}")
            raise

def process_excel(file_path):
    """Process Excel file into transactions"""
    try:
        df = pd.read_excel(file_path)
        return standardize_dataframe(df)
    except Exception as e:
        logger.error(f"Error processing Excel: {str(e)}")
        
        # Try reading with sheet specification
        try:
            xl = pd.ExcelFile(file_path)
            # Take the first sheet
            sheet_name = xl.sheet_names[0]
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            return standardize_dataframe(df)
        except Exception as nested_e:
            logger.error(f"Second attempt at Excel processing failed: {str(nested_e)}")
            raise

def process_json(file_path):
    """Process JSON file into transactions"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Handle different JSON structures
        if isinstance(data, list):
            return standardize_json_list(data)
        elif isinstance(data, dict):
            if 'transactions' in data and isinstance(data['transactions'], list):
                return standardize_json_list(data['transactions'])
            else:
                # Single transaction
                return [standardize_transaction(data)]
        else:
            raise ValueError("Unsupported JSON structure")
    except Exception as e:
        logger.error(f"Error processing JSON: {str(e)}")
        raise

def standardize_dataframe(df):
    """Convert DataFrame to standard transaction format"""
    # Make column names lowercase
    df.columns = [col.lower() for col in df.columns]
    
    # Map common column names to standard format
    column_mapping = {
        'source': 'sender',
        'from': 'sender',
        'sender_name': 'sender',
        'destination': 'receiver',
        'to': 'receiver', 
        'receiver_name': 'receiver',
        'value': 'amount',
        'sum': 'amount',
        'date': 'timestamp',
        'time': 'timestamp',
        'transaction date': 'timestamp',
        'tx_id': 'transaction_id',
        'id': 'transaction_id',
        'reference': 'transaction_id'
    }
    
    # Rename columns if they exist
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col not in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    # Convert to list of dictionaries
    transactions = df.to_dict('records')
    
    # Standardize each transaction
    return [standardize_transaction(tx) for tx in transactions]

def standardize_json_list(data):
    """Standardize a list of transaction dictionaries"""
    return [standardize_transaction(tx) for tx in data]

def standardize_transaction(tx):
    """Standardize a single transaction dictionary"""
    # Create a new transaction with standard fields
    std_tx = {
        'transaction_id': str(tx.get('transaction_id', tx.get('id', ''))),
        'sender': str(tx.get('sender', tx.get('from', ''))),
        'receiver': str(tx.get('receiver', tx.get('to', ''))), 
        'amount': float(tx.get('amount', tx.get('value', 0.0))),
        'currency': str(tx.get('currency', 'USD')),
        'raw_data': tx
    }
    
    # Handle timestamp
    timestamp = tx.get('timestamp', tx.get('date', tx.get('time', None)))
    if timestamp:
        if isinstance(timestamp, str):
            try:
                # Try common datetime formats
                for date_format in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        std_tx['timestamp'] = datetime.strptime(timestamp, date_format)
                        break
                    except ValueError:
                        continue
                
                # If none of the formats worked, use current time
                if 'timestamp' not in std_tx:
                    std_tx['timestamp'] = datetime.now()
            except:
                std_tx['timestamp'] = datetime.now()
        else:
            std_tx['timestamp'] = timestamp
    else:
        std_tx['timestamp'] = datetime.now()
    
    return std_tx

def extract_entities(transactions):
    """
    Extract unique entities from transaction data
    
    Args:
        transactions (list): List of transaction dictionaries
        
    Returns:
        list: List of entity dictionaries with name and type
    """
    entities = {}
    
    # Extract senders and receivers
    for tx in transactions:
        sender = tx.get('sender', '').strip()
        receiver = tx.get('receiver', '').strip()
        
        if sender and sender not in entities:
            entities[sender] = {
                'name': sender,
                'type': guess_entity_type(sender),
                'description': '',
                'transactions': []
            }
        
        if receiver and receiver not in entities:
            entities[receiver] = {
                'name': receiver,
                'type': guess_entity_type(receiver),
                'description': '',
                'transactions': []
            }
        
        # Add transaction to entity's transaction list
        if sender in entities:
            entities[sender]['transactions'].append(tx)
        if receiver in entities:
            entities[receiver]['transactions'].append(tx)
    
    # Return list of entity dictionaries
    return list(entities.values())

def guess_entity_type(name):
    """
    Make a basic guess at entity type based on name
    
    Args:
        name (str): Entity name
        
    Returns:
        str: Guessed entity type
    """
    name_lower = name.lower()
    
    # Check for company indicators
    if any(indicator in name_lower for indicator in ['ltd', 'llc', 'inc', 'corporation', 'corp', 'company', 'co.', 'holdings']):
        return 'corporation'
    
    # Check for non-profit indicators
    elif any(indicator in name_lower for indicator in ['foundation', 'trust', 'ngo', 'charity', 'association', 'non-profit']):
        return 'non-profit'
    
    # Check for financial intermediary indicators
    elif any(indicator in name_lower for indicator in ['bank', 'financial', 'capital', 'invest', 'securities', 'credit', 'fund']):
        return 'financial_intermediary'
    
    # Shell company indicators (offshore locations, generic names)
    elif any(indicator in name_lower for indicator in ['holdings', 'international', 'overseas', 'offshore', 'global', 'universal']):
        return 'shell_company'
    
    # Default
    return 'unknown'
