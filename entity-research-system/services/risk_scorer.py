from models import RiskLevel
import networkx as nx
import numpy as np

def calculate_risk_score(entity_data):
    """
    Calculate a risk score for an entity based on various factors
    
    Args:
        entity_data (dict): Entity data including transactions and characteristics
        
    Returns:
        tuple: (risk_score, risk_level) - Numerical score and risk level enum
    """
    # Initialize base risk score (0-10 scale)
    risk_score = 0.0
    
    # Risk factors with weights
    risk_factors = {
        'transaction_patterns': 0.3,
        'network_position': 0.2,
        'entity_type': 0.15,
        'geographic_risk': 0.2,
        'known_risk_indicators': 0.15
    }
    
    # 1. Transaction patterns analysis
    transaction_risk = _analyze_transaction_patterns(entity_data)
    
    # 2. Network position analysis
    network_risk = _analyze_network_position(entity_data)
    
    # 3. Entity type risk
    entity_type_risk = _analyze_entity_type_risk(entity_data)
    
    # 4. Geographic risk
    geographic_risk = _analyze_geographic_risk(entity_data)
    
    # 5. Known risk indicators
    indicator_risk = _analyze_risk_indicators(entity_data)
    
    # Calculate weighted risk score
    risk_score = (
        transaction_risk * risk_factors['transaction_patterns'] +
        network_risk * risk_factors['network_position'] +
        entity_type_risk * risk_factors['entity_type'] +
        geographic_risk * risk_factors['geographic_risk'] +
        indicator_risk * risk_factors['known_risk_indicators']
    )
    
    # Ensure risk score is within bounds
    risk_score = max(0.0, min(10.0, risk_score))
    
    # Determine risk level based on score
    if risk_score < 2.5:
        risk_level = RiskLevel.LOW
    elif risk_score < 5.0:
        risk_level = RiskLevel.MEDIUM
    elif risk_score < 7.5:
        risk_level = RiskLevel.HIGH
    else:
        risk_level = RiskLevel.CRITICAL
    
    return risk_score, risk_level

def _analyze_transaction_patterns(entity_data):
    """
    Analyze transaction patterns for risk indicators
    
    Args:
        entity_data (dict): Entity data including transactions
        
    Returns:
        float: Risk score component (0-10)
    """
    transactions = entity_data.get('transactions', [])
    
    if not transactions:
        return 5.0  # Neutral score if no transactions
    
    risk_score = 0.0
    
    # Calculate transaction metrics
    transaction_count = len(transactions)
    total_volume = sum(float(tx.get('amount', 0)) for tx in transactions)
    avg_transaction_size = total_volume / transaction_count if transaction_count else 0
    
    # Risk factor: High transaction count
    if transaction_count > 100:
        risk_score += 2.0
    elif transaction_count > 50:
        risk_score += 1.0
    
    # Risk factor: High average transaction size
    if avg_transaction_size > 1000000:  # > $1M
        risk_score += 2.5
    elif avg_transaction_size > 100000:  # > $100K
        risk_score += 1.5
    
    # Risk factor: Round numbers (potential indicator of artificial transactions)
    round_number_count = sum(1 for tx in transactions if float(tx.get('amount', 0)) % 1000 == 0)
    round_number_ratio = round_number_count / transaction_count if transaction_count else 0
    
    if round_number_ratio > 0.5:
        risk_score += 1.5
    
    # Risk factor: Transaction timing patterns
    # (This would be more sophisticated in a real system)
    # For now, we'll just use a placeholder
    time_pattern_risk = 0.5
    risk_score += time_pattern_risk
    
    # Risk factor: Transaction type diversity
    transaction_types = set(tx.get('type', 'Unknown') for tx in transactions)
    if len(transaction_types) == 1:
        # Single transaction type might indicate specialized or suspicious activity
        risk_score += 1.0
    
    # Scale to 0-10 range
    scaled_risk = min(10.0, risk_score)
    
    return scaled_risk

def _analyze_network_position(entity_data):
    """
    Analyze the entity's position in the transaction network
    
    Args:
        entity_data (dict): Entity data including counterparties
        
    Returns:
        float: Risk score component (0-10)
    """
    counterparties = entity_data.get('counterparties', [])
    
    if not counterparties:
        return 5.0  # Neutral score if no network data
    
    risk_score = 0.0
    
    # Risk factor: Limited number of counterparties
    if len(counterparties) < 3:
        risk_score += 2.0
    
    # Risk factor: Counterparty concentration
    # (This would be more sophisticated in a real system)
    # For now, we'll use a placeholder
    concentration_risk = 1.0
    risk_score += concentration_risk
    
    # Risk factor: Network position metrics
    # This would use the actual network analysis from NetworkX in a real system
    # For now, we'll use placeholders
    betweenness_risk = 1.0
    eigenvector_risk = 1.0
    
    risk_score += betweenness_risk + eigenvector_risk
    
    # Scale to 0-10 range
    scaled_risk = min(10.0, risk_score)
    
    return scaled_risk

def _analyze_entity_type_risk(entity_data):
    """
    Analyze risk based on entity type
    
    Args:
        entity_data (dict): Entity data including type
        
    Returns:
        float: Risk score component (0-10)
    """
    entity_type = entity_data.get('type', 'corporation')
    
    # Base risk scores by entity type
    type_risk_map = {
        'corporation': 3.0,
        'non_profit': 4.0,
        'shell_company': 8.0,
        'financial_intermediary': 5.0,
        'individual': 3.0,
        'other': 5.0
    }
    
    return type_risk_map.get(entity_type, 5.0)

def _analyze_geographic_risk(entity_data):
    """
    Analyze risk based on geographic factors
    
    Args:
        entity_data (dict): Entity data including countries
        
    Returns:
        float: Risk score component (0-10)
    """
    countries = entity_data.get('countries', [])
    
    if not countries:
        return 5.0  # Neutral score if no country data
    
    # High-risk countries (would be more comprehensive in a real system)
    high_risk_countries = [
        'afghanistan', 'belarus', 'burma', 'myanmar', 'central african republic',
        'democratic republic of the congo', 'eritrea', 'iran', 'iraq', 'libya',
        'north korea', 'somalia', 'south sudan', 'sudan', 'syria', 'venezuela',
        'yemen', 'zimbabwe'
    ]
    
    # Medium-risk countries
    medium_risk_countries = [
        'albania', 'bahamas', 'barbados', 'botswana', 'cambodia', 'ghana',
        'jamaica', 'mauritius', 'morocco', 'myanmar', 'nicaragua', 'pakistan',
        'panama', 'philippines', 'senegal', 'south africa', 'syria', 'uganda',
        'vanuatu'
    ]
    
    # Count high and medium risk countries
    high_risk_count = sum(1 for country in countries if country.lower() in high_risk_countries)
    medium_risk_count = sum(1 for country in countries if country.lower() in medium_risk_countries)
    
    # Calculate risk score based on country risk
    if high_risk_count > 0:
        # Any high-risk country gives a baseline high risk
        risk_score = 7.0 + (high_risk_count - 1) * 0.5
    elif medium_risk_count > 0:
        # Medium-risk countries give a moderate risk
        risk_score = 5.0 + medium_risk_count * 0.5
    else:
        # No high or medium risk countries
        risk_score = 3.0
    
    # Cap at 10
    risk_score = min(10.0, risk_score)
    
    return risk_score

def _analyze_risk_indicators(entity_data):
    """
    Analyze specific risk indicators in entity data
    
    Args:
        entity_data (dict): Entity data
        
    Returns:
        float: Risk score component (0-10)
    """
    # This would be a more sophisticated analysis in a real system
    # For now, we'll use some basic checks
    
    risk_score = 0.0
    
    # Check for suspicious keywords in name or description
    name = entity_data.get('name', '').lower()
    description = entity_data.get('description', '').lower()
    
    suspicious_keywords = [
        'offshore', 'shell', 'nominee', 'anonymous', 'hidden', 'secret',
        'concealed', 'undisclosed', 'confidential', 'private', 'international',
        'holding', 'overseas', 'global'
    ]
    
    for keyword in suspicious_keywords:
        if keyword in name:
            risk_score += 1.0
        if keyword in description:
            risk_score += 0.5
    
    # Check transaction patterns for round numbers
    transactions = entity_data.get('transactions', [])
    round_amounts = sum(1 for tx in transactions if float(tx.get('amount', 0)) % 1000 == 0)
    
    if transactions and round_amounts / len(transactions) > 0.5:
        risk_score += 1.0
    
    # Scale to 0-10 range
    scaled_risk = min(10.0, risk_score)
    
    return scaled_risk

def evaluate_relationship_risk(source_entity, target_entity, relationship_data):
    """
    Evaluate the risk level of a relationship between two entities
    
    Args:
        source_entity (dict): Source entity data
        target_entity (dict): Target entity data
        relationship_data (dict): Data about the relationship
        
    Returns:
        float: Relationship risk score (0-10)
    """
    # Base risk is the average of the two entities' risk scores
    source_risk = source_entity.get('risk_score', 5.0)
    target_risk = target_entity.get('risk_score', 5.0)
    base_risk = (source_risk + target_risk) / 2
    
    # Adjust based on relationship factors
    risk_score = base_risk
    
    # Factor: Transaction volume
    volume = relationship_data.get('volume', 0)
    if volume > 1000000:  # > $1M
        risk_score += 1.5
    elif volume > 100000:  # > $100K
        risk_score += 0.8
    
    # Factor: Transaction frequency
    frequency = relationship_data.get('frequency', 0)
    if frequency > 100:  # More than 100 transactions
        risk_score += 1.2
    
    # Factor: Relationship type
    rel_type = relationship_data.get('type', 'unknown')
    if rel_type == 'owner':
        risk_score += 0.5
    elif rel_type == 'subsidiary':
        risk_score += 0.7
    elif rel_type == 'partner':
        risk_score += 0.3
    
    # Factor: Jurisdictional risk
    if source_entity.get('country') != target_entity.get('country'):
        risk_score += 0.8  # Cross-border relationships have higher risk
    
    # Cap at 10
    risk_score = min(10.0, risk_score)
    
    return risk_score
