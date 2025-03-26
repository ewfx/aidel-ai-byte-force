import logging
import json
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def calculate_risk_score(entity_data, validation_data):
    """
    Calculate a risk score for an entity based on various risk factors
    
    Args:
        entity_data (dict): Entity information
        validation_data (dict): Validation results
        
    Returns:
        dict: Risk score and contributing factors
    """
    try:
        # Initialize risk factors with default weights
        risk_factors = {
            'entity_type': {
                'weight': 0.15,
                'score': 0,
                'details': {}
            },
            'validation': {
                'weight': 0.25,
                'score': 0,
                'details': {}
            },
            'transaction_patterns': {
                'weight': 0.30,
                'score': 0,
                'details': {}
            },
            'external_data': {
                'weight': 0.20,
                'score': 0,
                'details': {}
            },
            'sanctions': {
                'weight': 0.10,
                'score': 0,
                'details': {}
            }
        }
        
        # Factor 1: Entity type risk
        entity_type = entity_data.get('type', '')
        
        # Risk scores by entity type (1-10 scale)
        type_risk_scores = {
            'corporation': 3,
            'non-profit': 4,
            'financial_intermediary': 6,
            'shell': 9
        }
        
        risk_factors['entity_type']['score'] = type_risk_scores.get(entity_type, 5)
        risk_factors['entity_type']['details'] = {
            'type': entity_type,
            'inherent_risk': type_risk_scores.get(entity_type, 5)
        }
        
        # Factor 2: Validation risk
        validation_score = 0
        if validation_data:
            if isinstance(validation_data, dict) and 'is_valid' in validation_data:
                # If validation_data is from validate_entity()
                validation_passed = validation_data.get('is_valid', False)
                confidence = validation_data.get('confidence_score', 0)
                validation_score = 2 if validation_passed else 8
                
                # Adjust based on confidence
                if validation_passed and confidence < 0.7:
                    validation_score += 2  # Increase risk if confidence is low
                
                risk_factors['validation']['details'] = {
                    'validation_passed': validation_passed,
                    'confidence': confidence
                }
            else:
                # More detailed validation results
                checks_passed = sum(1 for check in validation_data.get('checks', []) if check.get('passed', False))
                total_checks = max(1, len(validation_data.get('checks', [])))
                
                # Calculate validation score based on passing percentage
                passing_percentage = checks_passed / total_checks
                validation_score = 10 - (passing_percentage * 8)  # 10 (all failed) to 2 (all passed)
                
                risk_factors['validation']['details'] = {
                    'checks_passed': checks_passed,
                    'total_checks': total_checks,
                    'passing_percentage': passing_percentage
                }
        else:
            # No validation data available
            validation_score = 7  # Higher risk due to lack of validation
            risk_factors['validation']['details'] = {
                'validation_performed': False
            }
        
        risk_factors['validation']['score'] = validation_score
        
        # Factor 3: Transaction patterns
        transaction_risk = 5  # Default medium risk
        
        # Check transaction data if available
        if 'transactions' in entity_data:
            tx_count = entity_data['transactions'].get('total', 0)
            volume_as_sender = entity_data['volume'].get('as_sender', 0)
            volume_as_receiver = entity_data['volume'].get('as_receiver', 0)
            
            # Risk indicators in transaction patterns
            risk_indicators = []
            
            # High volume discrepancy
            if max(volume_as_sender, volume_as_receiver) > 0:
                volume_ratio = abs(volume_as_sender - volume_as_receiver) / max(volume_as_sender, volume_as_receiver)
                if volume_ratio > 0.8:
                    risk_indicators.append({
                        'type': 'high_volume_discrepancy',
                        'details': f"One-sided flow: {volume_ratio:.2f} ratio",
                        'risk_contribution': 2
                    })
            
            # Shell company with high transaction volume
            if entity_type == 'shell' and tx_count > 10:
                risk_indicators.append({
                    'type': 'high_transaction_volume_for_shell',
                    'details': f"Shell company with {tx_count} transactions",
                    'risk_contribution': 3
                })
            
            # Round number transactions
            if 'ai_analysis' in validation_data:
                ai_results = validation_data['ai_analysis']
                if isinstance(ai_results, dict) and 'transaction_patterns' in ai_results:
                    patterns = ai_results['transaction_patterns']
                    for pattern in patterns:
                        if 'round_amounts' in pattern.get('pattern_type', '').lower():
                            risk_indicators.append({
                                'type': 'round_amount_transactions',
                                'details': pattern.get('description', 'Multiple round-number transactions'),
                                'risk_contribution': 2
                            })
            
            # Calculate transaction risk score based on indicators
            if risk_indicators:
                # Start with baseline risk
                transaction_risk = 4
                
                # Add risk contributions from indicators (capped at 10)
                for indicator in risk_indicators:
                    transaction_risk += indicator.get('risk_contribution', 1)
                
                transaction_risk = min(10, transaction_risk)
            
            risk_factors['transaction_patterns']['details'] = {
                'tx_count': tx_count,
                'volume_as_sender': volume_as_sender,
                'volume_as_receiver': volume_as_receiver,
                'risk_indicators': risk_indicators
            }
        
        risk_factors['transaction_patterns']['score'] = transaction_risk
        
        # Factor 4: External data risk
        external_risk = 5  # Default medium risk
        
        if 'external_data' in validation_data:
            external_data = validation_data['external_data']
            
            # Risk indicators from external data
            external_indicators = []
            
            # Check OpenCorporates data
            if 'opencorporates' in external_data:
                oc_data = external_data['opencorporates']
                
                # No matches found
                if oc_data.get('total_count', 0) == 0:
                    external_indicators.append({
                        'type': 'no_corporate_records',
                        'details': 'No matches found in corporate registries',
                        'risk_contribution': 3
                    })
                # Recently incorporated
                elif 'matches' in oc_data and oc_data['matches']:
                    for match in oc_data['matches']:
                        if 'incorporation_date' in match:
                            try:
                                inc_date = datetime.strptime(match['incorporation_date'], '%Y-%m-%d')
                                age_days = (datetime.now() - inc_date).days
                                
                                if age_days < 180:  # Less than 6 months old
                                    external_indicators.append({
                                        'type': 'recently_incorporated',
                                        'details': f"Company incorporated {age_days} days ago",
                                        'risk_contribution': 2
                                    })
                                    break
                            except:
                                pass
            
            # Check news data
            if 'news' in external_data:
                news_data = external_data['news']
                
                # Look for negative news
                negative_keywords = ['fraud', 'scam', 'investigation', 'scandal', 'lawsuit', 
                                    'crime', 'criminal', 'illegal', 'violation', 'sanction']
                
                negative_articles = 0
                for article in news_data.get('articles', []):
                    title = article.get('title', '').lower()
                    description = article.get('description', '').lower()
                    
                    if any(keyword in title or keyword in description for keyword in negative_keywords):
                        negative_articles += 1
                
                if negative_articles > 0:
                    external_indicators.append({
                        'type': 'negative_news',
                        'details': f"Found {negative_articles} articles with negative keywords",
                        'risk_contribution': min(4, negative_articles)  # Cap at 4
                    })
            
            # Check sanctions data
            if 'sanctions' in external_data:
                sanctions_data = external_data['sanctions']
                
                if sanctions_data.get('is_sanctioned', False):
                    external_indicators.append({
                        'type': 'sanctions_match',
                        'details': 'Entity appears on sanctions list',
                        'risk_contribution': 5  # High risk contribution
                    })
            
            # Calculate external risk score based on indicators
            if external_indicators:
                # Start with lower baseline for external data
                external_risk = 3
                
                # Add risk contributions from indicators (capped at 10)
                for indicator in external_indicators:
                    external_risk += indicator.get('risk_contribution', 1)
                
                external_risk = min(10, external_risk)
            
            risk_factors['external_data']['details'] = {
                'risk_indicators': external_indicators
            }
        
        risk_factors['external_data']['score'] = external_risk
        
        # Factor 5: Sanctions risk
        sanctions_risk = 1  # Default low risk
        
        # Check sanctions data directly
        if 'sanctions' in validation_data.get('external_data', {}):
            sanctions_data = validation_data['external_data']['sanctions']
            
            if sanctions_data.get('is_sanctioned', False):
                sanctions_risk = 10  # Maximum risk for sanctioned entities
                risk_factors['sanctions']['details'] = {
                    'is_sanctioned': True,
                    'matches': sanctions_data.get('matches', [])
                }
            else:
                risk_factors['sanctions']['details'] = {
                    'is_sanctioned': False
                }
        else:
            risk_factors['sanctions']['details'] = {
                'sanctions_checked': False
            }
        
        risk_factors['sanctions']['score'] = sanctions_risk
        
        # Calculate weighted average risk score
        total_weight = sum(factor['weight'] for factor in risk_factors.values())
        weighted_score = sum(factor['weight'] * factor['score'] for factor in risk_factors.values()) / total_weight
        
        # Round to one decimal place
        final_risk_score = round(weighted_score, 1)
        
        return {
            'score': final_risk_score,
            'factors': risk_factors,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error calculating risk score: {str(e)}")
        # Return a default medium-high risk score in case of error
        return {
            'score': 6.5,
            'factors': {
                'error': {
                    'weight': 1.0,
                    'score': 6.5,
                    'details': {'error': str(e)}
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }

def get_risk_level(score):
    """
    Convert numerical risk score to a risk level category
    
    Args:
        score (float): Risk score (1-10)
        
    Returns:
        str: Risk level category
    """
    if score >= 7.5:
        return 'critical'
    elif score >= 6:
        return 'high'
    elif score >= 4:
        return 'medium'
    elif score >= 2:
        return 'low'
    else:
        return 'minimal'

def get_risk_factors_summary(risk_data):
    """
    Generate a summary of risk factors
    
    Args:
        risk_data (dict): Risk data including factors
        
    Returns:
        list: List of risk factor summaries
    """
    summary = []
    
    if not risk_data or 'factors' not in risk_data:
        return summary
    
    factors = risk_data['factors']
    
    # Entity type risk
    if 'entity_type' in factors:
        entity_type = factors['entity_type']
        if entity_type['score'] >= 6:
            summary.append({
                'category': 'Entity Type',
                'level': get_risk_level(entity_type['score']),
                'description': f"High-risk entity type: {entity_type['details'].get('type', 'unknown')}"
            })
    
    # Validation risk
    if 'validation' in factors:
        validation = factors['validation']
        if validation['score'] >= 6:
            if not validation['details'].get('validation_passed', False):
                summary.append({
                    'category': 'Validation',
                    'level': get_risk_level(validation['score']),
                    'description': "Failed validation checks"
                })
            elif validation['details'].get('confidence', 1) < 0.7:
                summary.append({
                    'category': 'Validation',
                    'level': get_risk_level(validation['score']),
                    'description': "Low confidence in entity validation"
                })
    
    # Transaction patterns risk
    if 'transaction_patterns' in factors:
        transactions = factors['transaction_patterns']
        if transactions['score'] >= 6:
            indicators = transactions['details'].get('risk_indicators', [])
            for indicator in indicators:
                summary.append({
                    'category': 'Transaction Patterns',
                    'level': get_risk_level(transactions['score']),
                    'description': indicator.get('details', 'Suspicious transaction pattern detected')
                })
    
    # External data risk
    if 'external_data' in factors:
        external = factors['external_data']
        if external['score'] >= 6:
            indicators = external['details'].get('risk_indicators', [])
            for indicator in indicators:
                summary.append({
                    'category': 'External Data',
                    'level': get_risk_level(external['score']),
                    'description': indicator.get('details', 'Risk indicator from external data')
                })
    
    # Sanctions risk
    if 'sanctions' in factors:
        sanctions = factors['sanctions']
        if sanctions['score'] >= 6:
            summary.append({
                'category': 'Sanctions',
                'level': get_risk_level(sanctions['score']),
                'description': "Potential sanctions match detected"
            })
    
    return summary
