import os
import csv
import json
import logging
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename
import io

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# List of allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls', 'txt'}

def allowed_file(filename):
    """
    Check if a file has an allowed extension
    
    Args:
        filename (str): The filename to check
        
    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_transaction_data(file_obj):
    """
    Process transaction data from various file formats
    
    Args:
        file_obj: File object containing transaction data
        
    Returns:
        dict: Dictionary containing processed data and metadata
    """
    filename = secure_filename(file_obj.filename)
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    try:
        # Process different file formats
        if file_ext == 'csv':
            data = process_csv(file_obj)
        elif file_ext == 'json':
            data = process_json(file_obj)
        elif file_ext in ['xlsx', 'xls']:
            data = process_excel(file_obj)
        elif file_ext == 'txt':
            data = process_txt(file_obj)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Standardize and validate the processed data
        processed_data = standardize_transaction_data(data)
        
        # Generate metadata about the processed data
        metadata = {
            'record_count': len(processed_data),
            'source_file': filename,
            'processed_at': datetime.utcnow().isoformat(),
            'format': file_ext
        }
        
        return {
            'processed_data': processed_data,
            'metadata': metadata
        }
    
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
        raise ValueError(f"Error processing file: {str(e)}")

def process_csv(file_obj):
    """
    Process CSV file containing transaction data
    
    Args:
        file_obj: CSV file object
        
    Returns:
        list: List of dictionaries containing transaction data
    """
    # Read CSV data
    content = file_obj.read().decode('utf-8')
    file_obj.seek(0)  # Reset file pointer
    
    # Try to detect the delimiter
    dialect = csv.Sniffer().sniff(content[:1024])
    delimiter = dialect.delimiter
    
    # Convert CSV to list of dictionaries
    data = []
    csv_reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    
    for row in csv_reader:
        # Clean up row data (strip whitespace from keys and values)
        cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()}
        data.append(cleaned_row)
    
    return data

def process_json(file_obj):
    """
    Process JSON file containing transaction data
    
    Args:
        file_obj: JSON file object
        
    Returns:
        list: List of dictionaries containing transaction data
    """
    content = file_obj.read().decode('utf-8')
    data = json.loads(content)
    
    # Ensure the data is a list of dictionaries
    if isinstance(data, dict):
        # If the data is a dictionary with a list of records
        for key in data:
            if isinstance(data[key], list):
                return data[key]
        # If the data is a single record, wrap it in a list
        return [data]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Invalid JSON data format. Expected list or dictionary.")

def process_excel(file_obj):
    """
    Process Excel file containing transaction data
    
    Args:
        file_obj: Excel file object
        
    Returns:
        list: List of dictionaries containing transaction data
    """
    # Read Excel data
    df = pd.read_excel(file_obj)
    
    # Convert DataFrame to list of dictionaries
    data = df.to_dict(orient='records')
    
    return data

def process_txt(file_obj):
    """
    Process TXT file containing transaction data
    Attempts to detect format (CSV, JSON, or delimited)
    
    Args:
        file_obj: TXT file object
        
    Returns:
        list: List of dictionaries containing transaction data
    """
    content = file_obj.read().decode('utf-8')
    
    # Try to detect if it's JSON
    try:
        data = json.loads(content)
        # Ensure the data is a list of dictionaries
        if isinstance(data, dict):
            # If the data is a dictionary with a list of records
            for key in data:
                if isinstance(data[key], list):
                    return data[key]
            # If the data is a single record, wrap it in a list
            return [data]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("Invalid JSON data format. Expected list or dictionary.")
    except json.JSONDecodeError:
        # Not valid JSON, try CSV
        try:
            # Try to detect the delimiter
            dialect = csv.Sniffer().sniff(content[:1024])
            delimiter = dialect.delimiter
            
            # Convert CSV to list of dictionaries
            data = []
            csv_reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            
            for row in csv_reader:
                # Clean up row data (strip whitespace from keys and values)
                cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()}
                data.append(cleaned_row)
            
            return data
        except:
            # Not valid CSV, try fixed width or other format
            raise ValueError("Unsupported text file format. Please use CSV or JSON.")

def standardize_transaction_data(data):
    """
    Standardize transaction data into a common format
    
    Args:
        data (list): List of dictionaries containing transaction data
        
    Returns:
        list: List of standardized transaction dictionaries
    """
    standardized_data = []
    
    # Define field mappings (common variations of field names)
    field_mappings = {
        'transaction_id': ['transaction_id', 'id', 'txid', 'tx_id', 'transaction_reference', 'reference'],
        'sender': ['sender', 'from', 'source', 'sender_name', 'from_account', 'originator', 'payer'],
        'receiver': ['receiver', 'to', 'destination', 'recipient', 'recipient_name', 'to_account', 'beneficiary', 'payee'],
        'amount': ['amount', 'sum', 'total', 'value', 'transaction_amount'],
        'currency': ['currency', 'curr', 'currency_code'],
        'timestamp': ['timestamp', 'date', 'time', 'datetime', 'transaction_date', 'created_at', 'date_time'],
        'type': ['type', 'transaction_type', 'payment_type', 'tx_type']
    }
    
    for record in data:
        standardized_record = {}
        
        # Standardize field names
        for standard_field, variations in field_mappings.items():
            # Look for variations in the record
            for variation in variations:
                if variation in record:
                    # Found a matching field, standardize it
                    value = record[variation]
                    
                    # Handle special fields
                    if standard_field == 'timestamp':
                        # Try to parse the timestamp
                        try:
                            if isinstance(value, str):
                                # Try common date formats
                                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                                    try:
                                        value = datetime.strptime(value, fmt)
                                        break
                                    except ValueError:
                                        continue
                                
                                # If all format attempts failed, keep the original string
                                if isinstance(value, str):
                                    pass
                        except Exception as e:
                            logger.warning(f"Failed to parse timestamp '{value}': {str(e)}")
                    
                    elif standard_field == 'amount':
                        # Try to convert to float
                        try:
                            if isinstance(value, str):
                                # Remove currency symbols and commas
                                value = value.replace(',', '')
                                value = ''.join(c for c in value if c.isdigit() or c in ['.', '-'])
                            value = float(value)
                        except Exception as e:
                            logger.warning(f"Failed to parse amount '{value}': {str(e)}")
                    
                    standardized_record[standard_field] = value
                    break
        
        # Ensure required fields have at least placeholder values
        if 'transaction_id' not in standardized_record:
            standardized_record['transaction_id'] = f"TX-{len(standardized_data):06d}"
        
        if 'timestamp' not in standardized_record:
            standardized_record['timestamp'] = datetime.utcnow()
        
        if 'amount' not in standardized_record:
            standardized_record['amount'] = 0.0
        
        if 'currency' not in standardized_record:
            standardized_record['currency'] = 'USD'
        
        if 'type' not in standardized_record:
            standardized_record['type'] = 'unknown'
        
        # Include source field to track data origin
        standardized_record['source'] = 'file_import'
        
        # Copy any additional fields that weren't mapped
        for field, value in record.items():
            if field not in [var for variations in field_mappings.values() for var in variations]:
                # This is an unmapped field, include it with its original name
                standardized_record[field] = value
        
        standardized_data.append(standardized_record)
    
    return standardized_data
