import os
import re
import json
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define validation levels
VALIDATION_LEVELS = {
    'BASIC': 1,    # Basic format and syntactic validation
    'EXTENDED': 2, # More extensive validation including cross-referencing
    'FULL': 3      # Comprehensive validation with external API checks
}

def validate_entity(entity_data):
    """
    Validate entity data through multiple checks
    
    Args:
        entity_data (dict): Entity information to validate
        
    Returns:
        dict: Validation results with status and validation details
    """
    validation_level = VALIDATION_LEVELS['FULL']  # Default to full validation
    validation_results = {
        'is_valid': False,
        'validation_level': validation_level,
        'checks': [],
        'external_validation': {},
        'confidence_score': 0.0,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        # Step 1: Basic validation
        basic_validation = validate_basic_entity_info(entity_data)
        validation_results['checks'].append(basic_validation)
        
        # Step 2: Extended validation if basic passed
        if basic_validation['passed']:
            extended_validation = validate_entity_extended(entity_data)
            validation_results['checks'].append(extended_validation)
            
            # Step 3: External validation if extended passed
            if extended_validation['passed'] and validation_level >= VALIDATION_LEVELS['FULL']:
                external_validation = validate_entity_external(entity_data)
                validation_results['external_validation'] = external_validation
                validation_results['checks'].append({
                    'check_type': 'external_api',
                    'passed': external_validation.get('validation_passed', False),
                    'details': external_validation
                })
        
        # Calculate overall validation status
        passed_checks = sum(1 for check in validation_results['checks'] if check['passed'])
        total_checks = len(validation_results['checks'])
        
        validation_results['is_valid'] = (passed_checks > 0 and 
                                         passed_checks >= total_checks * 0.7)  # At least 70% of checks passed
        
        # Calculate confidence score (0.0 to 1.0)
        if total_checks > 0:
            validation_results['confidence_score'] = round(passed_checks / total_checks, 2)
        
        return validation_results
    
    except Exception as e:
        logger.error(f"Error validating entity: {str(e)}")
        validation_results['checks'].append({
            'check_type': 'error',
            'passed': False,
            'details': f"Validation error: {str(e)}"
        })
        return validation_results

def validate_basic_entity_info(entity_data):
    """
    Perform basic validation on entity information
    
    Args:
        entity_data (dict): Entity information
        
    Returns:
        dict: Validation results
    """
    validation_result = {
        'check_type': 'basic',
        'passed': False,
        'details': {}
    }
    
    # Check entity name
    name = entity_data.get('name', '')
    validation_result['details']['name_check'] = {
        'passed': bool(name and len(name) >= 2),
        'value': name
    }
    
    # Check entity type
    entity_type = entity_data.get('type', '')
    valid_types = ['corporation', 'non-profit', 'shell', 'financial_intermediary']
    validation_result['details']['type_check'] = {
        'passed': entity_type in valid_types,
        'value': entity_type
    }
    
    # Check identifier if available
    identifier = entity_data.get('identifier', '')
    has_valid_identifier = False
    identifier_check = {'passed': False, 'value': identifier}
    
    if identifier:
        # Validate based on likely identifier format
        if entity_type == 'corporation':
            # Common formats for business identifiers
            patterns = [
                r'^\d{2}-\d{7}$',  # US EIN
                r'^[A-Z]{2}\d{8,12}$',  # VAT ID
                r'^[A-Z0-9]{5,15}$'  # Generic registration number
            ]
            identifier_check['passed'] = any(re.match(pattern, identifier) for pattern in patterns)
        elif entity_type == 'financial_intermediary':
            # Common formats for financial identifiers
            patterns = [
                r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$',  # SWIFT/BIC code
                r'^[A-Z]{2}\d{2}[A-Z0-9]{4}[A-Z0-9]{8,}$'  # IBAN
            ]
            identifier_check['passed'] = any(re.match(pattern, identifier) for pattern in patterns)
        else:
            # Generic validation - at least 5 characters with alphanumerics
            identifier_check['passed'] = bool(re.match(r'^[A-Z0-9]{5,}$', identifier))
        
        has_valid_identifier = identifier_check['passed']
    
    validation_result['details']['identifier_check'] = identifier_check
    
    # Overall basic validation passes if name is valid and either type is valid or has a valid identifier
    validation_result['passed'] = (
        validation_result['details']['name_check']['passed'] and
        (validation_result['details']['type_check']['passed'] or has_valid_identifier)
    )
    
    return validation_result

def validate_entity_extended(entity_data):
    """
    Perform extended validation on entity information
    
    Args:
        entity_data (dict): Entity information
        
    Returns:
        dict: Extended validation results
    """
    validation_result = {
        'check_type': 'extended',
        'passed': False,
        'details': {}
    }
    
    # Check for suspicious patterns in entity name
    name = entity_data.get('name', '')
    suspicious_name = False
    suspicious_name_reasons = []
    
    # Check for very generic names
    generic_terms = ['holdings', 'group', 'international', 'worldwide', 'global', 'trading', 'investments']
    if any(term in name.lower() for term in generic_terms) and len(name.split()) <= 2:
        suspicious_name = True
        suspicious_name_reasons.append("Generic company name with limited descriptive terms")
    
    # Check for excessive use of abbreviations
    if len(re.findall(r'\b[A-Z]{2,}\b', name)) > 2:
        suspicious_name = True
        suspicious_name_reasons.append("Excessive use of abbreviations")
    
    validation_result['details']['name_analysis'] = {
        'passed': not suspicious_name,
        'suspicious': suspicious_name,
        'reasons': suspicious_name_reasons
    }
    
    # Analyze transaction patterns if available
    transaction_analysis = {}
    if 'transactions' in entity_data:
        tx_count = entity_data['transactions'].get('total', 0)
        outgoing_volume = entity_data['volume'].get('as_sender', 0)
        incoming_volume = entity_data['volume'].get('as_receiver', 0)
        
        transaction_analysis = {
            'passed': True,
            'high_volume_discrepancy': False,
            'high_transaction_count': False,
            'details': {
                'tx_count': tx_count,
                'outgoing_volume': outgoing_volume,
                'incoming_volume': incoming_volume,
                'net_flow': incoming_volume - outgoing_volume
            }
        }
        
        # Flag for high volume discrepancy
        if tx_count > 0 and abs(incoming_volume - outgoing_volume) / max(incoming_volume, outgoing_volume) > 0.7:
            transaction_analysis['high_volume_discrepancy'] = True
            transaction_analysis['passed'] = False
        
        # Flag for unusually high transaction count
        if entity_data.get('type') == 'shell' and tx_count > 20:
            transaction_analysis['high_transaction_count'] = True
            transaction_analysis['passed'] = False
    
    validation_result['details']['transaction_analysis'] = transaction_analysis
    
    # Overall extended validation result
    validation_checks = [
        validation_result['details']['name_analysis']['passed'],
        transaction_analysis.get('passed', True)
    ]
    
    validation_result['passed'] = all(validation_checks)
    
    return validation_result

def validate_entity_external(entity_data):
    """
    Validate entity using external APIs
    
    Args:
        entity_data (dict): Entity information
        
    Returns:
        dict: External validation results
    """
    validation_result = {
        'validation_passed': False,
        'sources': {},
        'summary': {}
    }
    
    try:
        name = entity_data.get('name', '')
        entity_type = entity_data.get('type', '')
        identifier = entity_data.get('identifier', '')
        
        # Try to validate with OpenCorporates API (if available)
        opencorporates_result = validate_with_opencorporates(name, identifier)
        if opencorporates_result:
            validation_result['sources']['opencorporates'] = opencorporates_result
        
        # Check against Company House API (UK) if it matches the pattern
        if re.match(r'^[A-Z0-9]{8}$', identifier):
            companies_house_result = validate_with_companies_house(identifier)
            if companies_house_result:
                validation_result['sources']['companies_house'] = companies_house_result
        
        # For financial intermediaries, check BIC directory (if available)
        if entity_type == 'financial_intermediary' and re.match(r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$', identifier):
            swift_result = validate_with_swift_directory(identifier)
            if swift_result:
                validation_result['sources']['swift_bic'] = swift_result
        
        # Summarize results from external sources
        validation_sources = validation_result['sources']
        if validation_sources:
            # Calculate overall validation status
            sources_validating = sum(1 for source in validation_sources.values() 
                                    if source.get('validated', False))
            total_sources = len(validation_sources)
            
            validation_result['validation_passed'] = sources_validating > 0
            validation_result['summary'] = {
                'sources_checked': total_sources,
                'sources_validating': sources_validating,
                'confidence': round(sources_validating / total_sources, 2) if total_sources > 0 else 0.0
            }
        else:
            validation_result['summary'] = {
                'sources_checked': 0,
                'sources_validating': 0,
                'confidence': 0.0
            }
        
        return validation_result
    
    except Exception as e:
        logger.error(f"Error in external validation: {str(e)}")
        return {
            'validation_passed': False,
            'error': str(e),
            'sources': {},
            'summary': {
                'sources_checked': 0,
                'sources_validating': 0,
                'confidence': 0.0
            }
        }

def validate_with_opencorporates(name, identifier=None):
    """
    Validate entity with OpenCorporates API
    
    Args:
        name (str): Entity name
        identifier (str, optional): Entity identifier
        
    Returns:
        dict: Validation results or None if not available
    """
    # Check if the API key is available
    api_key = os.environ.get('OPENCORPORATES_API_KEY')
    if not api_key:
        logger.warning("OpenCorporates API key not available, skipping validation")
        return None
    
    try:
        # Prepare search parameters
        params = {
            'q': name,
            'api_token': api_key
        }
        
        # Add jurisdiction if identifier suggests a specific one
        # This is a simplified example; real implementation would be more sophisticated
        if identifier and re.match(r'^US', identifier):
            params['jurisdiction_code'] = 'us'
        
        # Make API request
        response = requests.get('https://api.opencorporates.com/v0.4/companies/search', params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if any companies were found
            companies = data.get('results', {}).get('companies', [])
            if companies:
                # Check for name similarity with the top result
                top_result = companies[0]['company']
                name_similarity = calculate_name_similarity(name, top_result['name'])
                
                validated = name_similarity >= 0.8  # 80% similarity threshold
                
                return {
                    'validated': validated,
                    'similarity': name_similarity,
                    'matches': len(companies),
                    'top_match': {
                        'name': top_result['name'],
                        'jurisdiction': top_result.get('jurisdiction_code', ''),
                        'company_number': top_result.get('company_number', ''),
                        'incorporation_date': top_result.get('incorporation_date', ''),
                        'company_type': top_result.get('company_type', '')
                    }
                }
            else:
                return {
                    'validated': False,
                    'similarity': 0,
                    'matches': 0
                }
        else:
            logger.warning(f"OpenCorporates API error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error validating with OpenCorporates: {str(e)}")
        return None

def validate_with_companies_house(identifier):
    """
    Validate entity with UK Companies House API
    
    Args:
        identifier (str): Company number
        
    Returns:
        dict: Validation results or None if not available
    """
    # Check if the API key is available
    api_key = os.environ.get('COMPANIES_HOUSE_API_KEY')
    if not api_key:
        logger.warning("Companies House API key not available, skipping validation")
        return None
    
    try:
        # Prepare API request with basic auth (API key as username, no password)
        headers = {
            'Authorization': f'Basic {api_key}'
        }
        
        # Make API request
        response = requests.get(f'https://api.companieshouse.gov.uk/company/{identifier}', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant information
            company_status = data.get('company_status', '')
            company_name = data.get('company_name', '')
            
            # Determine validation status
            validated = company_status.lower() in ['active', 'open']
            
            return {
                'validated': validated,
                'company_status': company_status,
                'company_name': company_name,
                'company_type': data.get('type', ''),
                'incorporation_date': data.get('date_of_creation', ''),
                'registered_address': data.get('registered_office_address', {})
            }
        elif response.status_code == 404:
            return {
                'validated': False,
                'reason': 'Company not found'
            }
        else:
            logger.warning(f"Companies House API error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error validating with Companies House: {str(e)}")
        return None

def validate_with_swift_directory(bic_code):
    """
    Validate financial institution with SWIFT BIC directory
    Note: This is a simplified version as the actual SWIFT API is restricted
    
    Args:
        bic_code (str): BIC/SWIFT code
        
    Returns:
        dict: Validation results or None if not available
    """
    # This is a placeholder for a real SWIFT API integration
    # In practice, access to the SWIFT BIC directory requires specific agreements
    
    # For demonstration purposes, we'll simulate basic validation of BIC format
    if re.match(r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$', bic_code):
        # Extract information from BIC components
        bank_code = bic_code[:4]
        country_code = bic_code[4:6]
        location_code = bic_code[6:8]
        branch_code = bic_code[8:11] if len(bic_code) > 8 else 'XXX'
        
        return {
            'validated': True,  # Only format validation
            'bic_components': {
                'bank_code': bank_code,
                'country_code': country_code,
                'location_code': location_code,
                'branch_code': branch_code
            },
            'note': 'BIC format validated only; full validation requires SWIFT directory access'
        }
    else:
        return {
            'validated': False,
            'reason': 'Invalid BIC format'
        }

def calculate_name_similarity(name1, name2):
    """
    Calculate similarity between two entity names
    
    Args:
        name1 (str): First name
        name2 (str): Second name
        
    Returns:
        float: Similarity score between 0 and 1
    """
    # Convert to lowercase
    name1 = name1.lower()
    name2 = name2.lower()
    
    # Remove common legal suffixes
    legal_suffixes = ['inc', 'inc.', 'llc', 'llc.', 'ltd', 'ltd.', 'corp', 'corp.', 
                      'corporation', 'co', 'co.', 'company', 'gmbh', 'ag', 'plc']
    
    for suffix in legal_suffixes:
        name1 = re.sub(r'\b' + re.escape(suffix) + r'\b', '', name1)
        name2 = re.sub(r'\b' + re.escape(suffix) + r'\b', '', name2)
    
    # Remove punctuation and extra spaces
    name1 = re.sub(r'[^\w\s]', '', name1).strip()
    name2 = re.sub(r'[^\w\s]', '', name2).strip()
    
    # Simple exact match
    if name1 == name2:
        return 1.0
    
    # Simple word overlap
    words1 = set(name1.split())
    words2 = set(name2.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0
