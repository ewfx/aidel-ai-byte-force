import logging
import re
import json
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def identify_entities(transactions):
    """
    Identify potential entities from transaction data
    
    Args:
        transactions (list): List of standardized transaction dictionaries
        
    Returns:
        list: List of identified entity dictionaries
    """
    entities = {}
    
    try:
        # Extract entities from sender and receiver fields
        for tx in transactions:
            sender = tx.get('sender', '').strip()
            receiver = tx.get('receiver', '').strip()
            
            if sender and len(sender) > 1:
                entity_type = guess_entity_type(sender, tx)
                if entity_type:
                    entity_key = f"{sender.lower()}|{entity_type}"
                    if entity_key not in entities:
                        entities[entity_key] = {
                            'name': sender,
                            'type': entity_type,
                            'transactions_as_sender': [],
                            'transactions_as_receiver': [],
                            'identifiers': set()
                        }
                    entities[entity_key]['transactions_as_sender'].append(tx)
                    
                    # Look for identifiers in the transaction
                    identifiers = extract_identifiers(tx)
                    for id_type, id_value in identifiers:
                        entities[entity_key]['identifiers'].add((id_type, id_value))
            
            if receiver and len(receiver) > 1:
                entity_type = guess_entity_type(receiver, tx)
                if entity_type:
                    entity_key = f"{receiver.lower()}|{entity_type}"
                    if entity_key not in entities:
                        entities[entity_key] = {
                            'name': receiver,
                            'type': entity_type,
                            'transactions_as_sender': [],
                            'transactions_as_receiver': [],
                            'identifiers': set()
                        }
                    entities[entity_key]['transactions_as_receiver'].append(tx)
                    
                    # Look for identifiers in the transaction
                    identifiers = extract_identifiers(tx)
                    for id_type, id_value in identifiers:
                        entities[entity_key]['identifiers'].add((id_type, id_value))
        
        # Convert entities to list format and finalize
        entity_list = []
        for entity_key, entity_data in entities.items():
            # Calculate transaction statistics
            tx_count_as_sender = len(entity_data['transactions_as_sender'])
            tx_count_as_receiver = len(entity_data['transactions_as_receiver'])
            total_volume_as_sender = sum(float(tx.get('amount', 0)) for tx in entity_data['transactions_as_sender'])
            total_volume_as_receiver = sum(float(tx.get('amount', 0)) for tx in entity_data['transactions_as_receiver'])
            
            # Determine primary identifier if available
            primary_identifier = ""
            if entity_data['identifiers']:
                # Sort identifiers by priority (tax ID > registration number > etc.)
                sorted_identifiers = sorted(entity_data['identifiers'], key=lambda x: identifier_priority(x[0]))
                if sorted_identifiers:
                    primary_identifier = sorted_identifiers[0][1]
            
            entity_list.append({
                'name': entity_data['name'],
                'type': entity_data['type'],
                'identifier': primary_identifier,
                'transactions': {
                    'as_sender': tx_count_as_sender,
                    'as_receiver': tx_count_as_receiver,
                    'total': tx_count_as_sender + tx_count_as_receiver
                },
                'volume': {
                    'as_sender': total_volume_as_sender,
                    'as_receiver': total_volume_as_receiver,
                    'net': total_volume_as_receiver - total_volume_as_sender
                }
            })
        
        # Sort entities by total transaction count (most active first)
        entity_list.sort(key=lambda x: x['transactions']['total'], reverse=True)
        
        return entity_list
    
    except Exception as e:
        logger.error(f"Error identifying entities: {str(e)}")
        # Return any entities identified before the error
        return [{'name': k.split('|')[0], 'type': k.split('|')[1]} for k in entities.keys()]

def guess_entity_type(name, transaction=None):
    """
    Guess the entity type based on the name and transaction data
    
    Args:
        name (str): Entity name
        transaction (dict): Transaction data for context
        
    Returns:
        str: Guessed entity type or None if unable to determine
    """
    # Skip empty or very short names
    if not name or len(name) <= 1:
        return None
    
    # Look for company-related keywords
    company_indicators = ['inc', 'llc', 'ltd', 'corp', 'corporation', 'co', 'company', 
                         'gmbh', 'ag', 'plc', 'lp', 'partners', 'limited', 'holdings',
                         'group', 'enterprises', 'investments', 'industries', 'solutions',
                         'bank', 'capital', 'services', 'technologies', 'systems']
    
    # Look for non-profit indicators
    nonprofit_indicators = ['foundation', 'association', 'ngo', 'charity', 'trust',
                           'institute', 'society', 'nonprofit', 'non-profit']
    
    # Look for financial intermediary indicators
    financial_indicators = ['bank', 'credit union', 'broker', 'exchange', 'fund',
                           'capital', 'asset', 'securities', 'investment', 'financial',
                           'wealth', 'treasury', 'trust', 'finance', 'monetary',
                           'payment', 'transfer', 'transaction', 'remittance']
    
    # Check for legal form in the name
    name_lower = name.lower()
    words = name_lower.split()
    
    # Check for company indicators
    for indicator in company_indicators:
        if re.search(r'\b' + re.escape(indicator) + r'\b', name_lower) or name_lower.endswith(f" {indicator}"):
            return 'corporation'
    
    # Check for non-profit indicators
    for indicator in nonprofit_indicators:
        if re.search(r'\b' + re.escape(indicator) + r'\b', name_lower) or name_lower.endswith(f" {indicator}"):
            return 'non-profit'
    
    # Check for financial intermediary indicators
    for indicator in financial_indicators:
        if re.search(r'\b' + re.escape(indicator) + r'\b', name_lower) or name_lower.endswith(f" {indicator}"):
            return 'financial_intermediary'
    
    # Check transaction patterns for shell company indicators
    if transaction:
        # Shell companies often have generic names and complex transaction patterns
        # This is a basic heuristic and should be enhanced with more sophisticated logic
        if ('shell' in name_lower or 'holdings' in name_lower or 'international' in name_lower) and \
           (transaction.get('amount', 0) > 50000 or 'offshore' in name_lower):
            return 'shell'
    
    # Default to corporation for anything that looks like a company name
    # This is a simplified approach; a more sophisticated entity classifier would be better
    if any(char.isdigit() for char in name) or len(words) >= 2:
        # Names with numbers or multiple words are likely organizations
        return 'corporation'
    
    # Can't determine entity type
    return None

def extract_identifiers(transaction):
    """
    Extract potential entity identifiers from transaction data
    
    Args:
        transaction (dict): Transaction data
        
    Returns:
        list: List of tuples (identifier_type, identifier_value)
    """
    identifiers = []
    
    # Check all fields in the transaction for potential identifiers
    for field, value in transaction.items():
        if isinstance(value, str):
            # Check for common identifier patterns
            
            # Tax ID (EIN, VAT, etc.)
            tax_id_patterns = [
                # US EIN pattern (XX-XXXXXXX)
                r'\b(\d{2}-\d{7})\b',
                # VAT pattern (2-letter country code + numbers)
                r'\b([A-Z]{2}\d{8,12})\b'
            ]
            
            for pattern in tax_id_patterns:
                matches = re.findall(pattern, value)
                for match in matches:
                    identifiers.append(('tax_id', match))
            
            # Registration number
            reg_patterns = [
                # Generic registration number pattern
                r'\bReg\.?\s*No\.?[:# ]?([A-Z0-9]{5,15})\b',
                r'\bRegistration\s*[:# ]?([A-Z0-9]{5,15})\b'
            ]
            
            for pattern in reg_patterns:
                matches = re.findall(pattern, value)
                for match in matches:
                    identifiers.append(('registration', match))
    
    # Check for additional identifiers in additional fields
    for field in ['reference', 'description', 'memo', 'notes']:
        if field in transaction and isinstance(transaction[field], str):
            value = transaction[field]
            
            # Look for SWIFT/BIC codes (financial institutions)
            swift_matches = re.findall(r'\b([A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?)\b', value)
            for match in swift_matches:
                identifiers.append(('swift_bic', match[0]))
            
            # Look for IBAN (financial institutions/accounts)
            iban_matches = re.findall(r'\b([A-Z]{2}\d{2}[A-Z0-9]{4}[A-Z0-9]{8,})\b', value)
            for match in iban_matches:
                identifiers.append(('iban', match))
    
    return identifiers

def identifier_priority(id_type):
    """
    Determine priority of identifier types (lower number = higher priority)
    
    Args:
        id_type (str): Type of identifier
        
    Returns:
        int: Priority value
    """
    priorities = {
        'tax_id': 1,
        'registration': 2,
        'swift_bic': 3,
        'iban': 4
    }
    
    return priorities.get(id_type, 999)  # Default to low priority if unknown
