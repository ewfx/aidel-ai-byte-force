import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Risk factor weights
RISK_WEIGHTS = {
    # Entity type factors
    "shell_company": 0.8,
    "corporation": 0.4,
    "financial_intermediary": 0.6,
    "non-profit": 0.5,
    "unknown": 0.7,
    
    # Transaction pattern factors
    "high_volume_transactions": 0.7,
    "irregular_transaction_patterns": 0.8,
    "circular_transactions": 0.9,
    "overseas_transactions": 0.6,
    "large_round_numbers": 0.5,
    "inconsistent_transactions": 0.7,
    
    # Evidence-based factors
    "negative_news": 0.7,
    "regulatory_issues": 0.8,
    "incomplete_information": 0.6,
    "jurisdiction_high_risk": 0.8,
    "politically_exposed": 0.9,
    "sanctioned_entity": 1.0,
    "poor_transparency": 0.6,
    
    # Relationship factors
    "connection_to_high_risk_entity": 0.8,
    "complex_ownership_structure": 0.7,
    "frequent_management_changes": 0.6
}

def calculate_risk_score(entity_data, analysis_data):
    """
    Calculate a risk score for an entity based on various factors
    
    Args:
        entity_data (dict): Basic entity data
        analysis_data (dict): Analysis data from AI and external sources
        
    Returns:
        dict: Risk score and factors
    """
    risk_factors = []
    cumulative_risk = 0.0
    factor_count = 0
    
    try:
        # Entity type risk
        entity_type = entity_data.get('type', 'unknown')
        if entity_type in RISK_WEIGHTS:
            risk_factor = {
                "factor": f"Entity type: {entity_type}",
                "weight": RISK_WEIGHTS[entity_type],
                "description": f"Base risk for entity type '{entity_type}'"
            }
            risk_factors.append(risk_factor)
            cumulative_risk += risk_factor["weight"]
            factor_count += 1
        
        # Add risk factors from analysis
        if analysis_data.get('risk_factors'):
            for factor in analysis_data['risk_factors']:
                factor_type = determine_factor_type(factor)
                if factor_type in RISK_WEIGHTS:
                    risk_factor = {
                        "factor": factor,
                        "weight": RISK_WEIGHTS[factor_type],
                        "description": "AI-identified risk factor"
                    }
                    risk_factors.append(risk_factor)
                    cumulative_risk += risk_factor["weight"]
                    factor_count += 1
        
        # Transaction pattern analysis
        transaction_risks = analyze_transaction_patterns(entity_data.get('transactions', []))
        for risk in transaction_risks:
            if risk in RISK_WEIGHTS:
                risk_factor = {
                    "factor": f"Transaction pattern: {risk}",
                    "weight": RISK_WEIGHTS[risk],
                    "description": "Identified from transaction patterns"
                }
                risk_factors.append(risk_factor)
                cumulative_risk += risk_factor["weight"]
                factor_count += 1
        
        # Calculate the final risk score
        if factor_count > 0:
            final_score = cumulative_risk / factor_count
        else:
            final_score = 0.1  # Default low risk if no factors identified
        
        # Apply sigmoid-like normalization to keep between 0 and 1
        normalized_score = min(max(final_score, 0.0), 1.0)
        
        # Return the risk assessment
        return {
            "score": normalized_score,
            "factors": risk_factors,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating risk score: {str(e)}")
        return {
            "score": 0.5,  # Default medium risk on error
            "factors": [{"factor": "Error in risk calculation", "weight": 0.5, "description": str(e)}],
            "timestamp": datetime.now().isoformat()
        }

def determine_factor_type(factor_text):
    """
    Determine the type of risk factor from a text description
    
    Args:
        factor_text (str): Text description of a risk factor
        
    Returns:
        str: Factor type that maps to a weight in RISK_WEIGHTS
    """
    factor_text = factor_text.lower()
    
    # Map the factor text to a known factor type
    if any(keyword in factor_text for keyword in ["shell", "offshore", "nominee"]):
        return "shell_company"
    elif any(keyword in factor_text for keyword in ["high volume", "numerous transactions"]):
        return "high_volume_transactions"
    elif any(keyword in factor_text for keyword in ["circular", "round-trip"]):
        return "circular_transactions"
    elif any(keyword in factor_text for keyword in ["overseas", "foreign", "international"]):
        return "overseas_transactions"
    elif any(keyword in factor_text for keyword in ["round numbers", "even amounts"]):
        return "large_round_numbers"
    elif any(keyword in factor_text for keyword in ["inconsistent", "unusual", "irregular"]):
        return "irregular_transaction_patterns"
    elif any(keyword in factor_text for keyword in ["news", "media", "press", "negative"]):
        return "negative_news"
    elif any(keyword in factor_text for keyword in ["regulator", "compliance", "violation"]):
        return "regulatory_issues"
    elif any(keyword in factor_text for keyword in ["incomplete", "missing", "lack of"]):
        return "incomplete_information"
    elif any(keyword in factor_text for keyword in ["jurisdict", "country", "territory", "high risk"]):
        return "jurisdiction_high_risk"
    elif any(keyword in factor_text for keyword in ["pep", "political", "government", "official"]):
        return "politically_exposed"
    elif any(keyword in factor_text for keyword in ["sanction", "prohibited", "restricted"]):
        return "sanctioned_entity"
    elif any(keyword in factor_text for keyword in ["transparency", "disclosure", "opaque"]):
        return "poor_transparency"
    elif any(keyword in factor_text for keyword in ["connect", "link", "relation", "high risk"]):
        return "connection_to_high_risk_entity"
    elif any(keyword in factor_text for keyword in ["complex", "structure", "ownership"]):
        return "complex_ownership_structure"
    elif any(keyword in factor_text for keyword in ["management", "director", "change", "frequent"]):
        return "frequent_management_changes"
    
    # Default to unknown factor type
    return "unknown"

def analyze_transaction_patterns(transactions):
    """
    Analyze transaction patterns for risk indicators
    
    Args:
        transactions (list): List of transaction dictionaries
        
    Returns:
        list: Risk factors identified from transaction patterns
    """
    risk_factors = []
    
    if not transactions:
        return ["incomplete_information"]
    
    try:
        # Count transactions
        if len(transactions) > 20:
            risk_factors.append("high_volume_transactions")
        
        # Check for round numbers
        round_number_count = 0
        for tx in transactions:
            amount = tx.get('amount', 0)
            if amount % 1000 == 0 and amount >= 10000:
                round_number_count += 1
        
        if round_number_count > len(transactions) * 0.3:  # If more than 30% are round numbers
            risk_factors.append("large_round_numbers")
        
        # Check for overseas transactions
        overseas_count = 0
        for tx in transactions:
            # This is a simplistic check - in a real system, you'd have more data
            if tx.get('currency', 'USD') != 'USD':
                overseas_count += 1
        
        if overseas_count > 0:
            risk_factors.append("overseas_transactions")
        
        # Check for circular transactions (simplified)
        senders = set([tx.get('sender', '') for tx in transactions])
        receivers = set([tx.get('receiver', '') for tx in transactions])
        
        if len(senders.intersection(receivers)) > 0:
            risk_factors.append("circular_transactions")
        
        # Check for irregular patterns (simplified)
        # In a real system, you'd use more sophisticated time series analysis
        amounts = [tx.get('amount', 0) for tx in transactions]
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            max_amount = max(amounts)
            
            if max_amount > avg_amount * 5:  # If max is 5x the average
                risk_factors.append("irregular_transaction_patterns")
        
        return risk_factors
        
    except Exception as e:
        logger.error(f"Error analyzing transaction patterns: {str(e)}")
        return ["inconsistent_transactions"]

def get_risk_category(score):
    """
    Get a risk category label based on a numeric score
    
    Args:
        score (float): Risk score between 0 and 1
        
    Returns:
        str: Risk category label
    """
    if score >= 0.8:
        return "Very High Risk"
    elif score >= 0.6:
        return "High Risk"
    elif score >= 0.4:
        return "Medium Risk"
    elif score >= 0.2:
        return "Low Risk"
    else:
        return "Very Low Risk"

def get_risk_color(score):
    """
    Get a color code for a risk score
    
    Args:
        score (float): Risk score between 0 and 1
        
    Returns:
        str: CSS color code
    """
    if score >= 0.8:
        return "danger"  # Bootstrap danger class (red)
    elif score >= 0.6:
        return "warning"  # Bootstrap warning class (yellow/orange)
    elif score >= 0.4:
        return "info"     # Bootstrap info class (blue)
    else:
        return "success"  # Bootstrap success class (green)
