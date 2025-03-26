import json
import logging
from datetime import datetime
import os
from services.risk_analyzer import get_risk_level, get_risk_factors_summary
from services.ai_service import generate_entity_summary

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_entity_report(entity, risk, evidence, transactions):
    """
    Generate a comprehensive report for an entity
    
    Args:
        entity: Entity model object
        risk: Risk model object
        evidence: List of Evidence model objects
        transactions: List of Transaction model objects
        
    Returns:
        dict: Report content in structured format
    """
    try:
        # Convert model objects to dictionaries if they aren't already
        entity_data = entity.to_dict() if hasattr(entity, 'to_dict') else entity
        risk_data = risk.to_dict() if hasattr(risk, 'to_dict') else risk
        
        # Process evidence items
        evidence_items = []
        for item in evidence:
            if hasattr(item, 'to_dict'):
                evidence_items.append(item.to_dict())
            else:
                evidence_items.append(item)
        
        # Process transactions
        transaction_data = []
        for tx in transactions:
            if hasattr(tx, 'to_dict'):
                transaction_data.append(tx.to_dict())
            else:
                transaction_data.append(tx)
        
        # Get risk summary
        risk_level = get_risk_level(risk_data.get('score', 5))
        risk_factors = get_risk_factors_summary({'factors': json.loads(risk_data.get('factors', '{}'))})
        
        # Generate AI summary if OpenAI API is available
        ai_summary = None
        if os.environ.get('OPENAI_API_KEY'):
            try:
                ai_summary = generate_entity_summary(entity_data, evidence_items)
            except Exception as e:
                logger.error(f"Error generating AI summary: {str(e)}")
                ai_summary = {
                    "error": str(e),
                    "entity_profile": {
                        "name": entity_data.get('name', 'Unknown'),
                        "summary": "Error generating AI summary"
                    }
                }
        
        # Build report structure
        report = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "entity_id": entity_data.get('id'),
                "entity_name": entity_data.get('name'),
                "report_type": "entity_risk_assessment"
            },
            "entity_information": {
                "name": entity_data.get('name'),
                "type": entity_data.get('entity_type'),
                "identifier": entity_data.get('identifier'),
                "status": entity_data.get('status'),
                "source": entity_data.get('source'),
                "created_at": entity_data.get('created_at'),
                "additional_info": json.loads(entity_data.get('additional_info', '{}')) if isinstance(entity_data.get('additional_info'), str) else entity_data.get('additional_info', {})
            },
            "risk_assessment": {
                "score": risk_data.get('score'),
                "level": risk_level,
                "factors": risk_factors,
                "raw_factors": json.loads(risk_data.get('factors', '{}')) if isinstance(risk_data.get('factors'), str) else risk_data.get('factors', {}),
                "last_updated": risk_data.get('last_updated')
            },
            "transaction_summary": {
                "total_count": len(transaction_data),
                "as_sender": len([tx for tx in transaction_data if tx.get('sender') == entity_data.get('name')]),
                "as_receiver": len([tx for tx in transaction_data if tx.get('receiver') == entity_data.get('name')]),
                "total_volume_sent": sum(float(tx.get('amount', 0)) for tx in transaction_data if tx.get('sender') == entity_data.get('name')),
                "total_volume_received": sum(float(tx.get('amount', 0)) for tx in transaction_data if tx.get('receiver') == entity_data.get('name')),
                "transaction_types": get_transaction_types(transaction_data)
            },
            "evidence_summary": {
                "total_items": len(evidence_items),
                "by_source": get_evidence_by_source(evidence_items),
                "key_findings": extract_key_findings(evidence_items)
            },
            "ai_analysis": ai_summary if ai_summary else {"note": "AI analysis not available"},
            "recommendations": generate_recommendations(entity_data, risk_data, evidence_items, transaction_data)
        }
        
        return report
    
    except Exception as e:
        logger.error(f"Error generating entity report: {str(e)}")
        # Return basic error report
        return {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "entity_id": getattr(entity, 'id', 'unknown'),
                "entity_name": getattr(entity, 'name', 'Unknown Entity'),
                "report_type": "entity_risk_assessment",
                "error": str(e)
            },
            "error": f"Failed to generate complete report: {str(e)}"
        }

def get_transaction_types(transactions):
    """
    Summarize transaction types
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        dict: Transaction type counts
    """
    type_counts = {}
    
    for tx in transactions:
        tx_type = tx.get('transaction_type', 'unknown')
        type_counts[tx_type] = type_counts.get(tx_type, 0) + 1
    
    return type_counts

def get_evidence_by_source(evidence_items):
    """
    Group evidence items by source
    
    Args:
        evidence_items: List of evidence dictionaries
        
    Returns:
        dict: Evidence grouped by source
    """
    by_source = {}
    
    for item in evidence_items:
        source = item.get('source', 'unknown')
        by_source[source] = by_source.get(source, 0) + 1
    
    return by_source

def extract_key_findings(evidence_items):
    """
    Extract key findings from evidence items
    
    Args:
        evidence_items: List of evidence dictionaries
        
    Returns:
        list: Key findings
    """
    key_findings = []
    
    # Process evidence by type and extract important information
    for item in evidence_items:
        source = item.get('source', 'unknown')
        evidence_type = item.get('evidence_type', 'unknown')
        reliability = item.get('reliability_score', 0.5)
        
        # Parse content
        content = {}
        if isinstance(item.get('content'), str):
            try:
                content = json.loads(item.get('content', '{}'))
            except:
                content = {"error": "Could not parse content"}
        else:
            content = item.get('content', {})
        
        # Extract findings based on evidence type and source
        if evidence_type == 'external_data':
            if source == 'opencorporates':
                # Extract corporate registry information
                if content.get('matches', []):
                    for match in content.get('matches', [])[:1]:  # Take first match
                        key_findings.append({
                            'source': 'Corporate Registry',
                            'reliability': reliability,
                            'finding': f"Entity registered as {match.get('name', 'unknown')} in {match.get('jurisdiction', 'unknown')}",
                            'importance': 'high'
                        })
            
            elif source == 'news':
                # Extract news findings
                negative_keywords = ['fraud', 'scam', 'investigation', 'scandal', 'lawsuit', 
                                    'crime', 'criminal', 'illegal', 'violation', 'sanction']
                
                for article in content.get('articles', []):
                    title = article.get('title', '').lower()
                    
                    if any(keyword in title for keyword in negative_keywords):
                        key_findings.append({
                            'source': 'News Media',
                            'reliability': reliability,
                            'finding': f"Negative news: {article.get('title')}",
                            'importance': 'high',
                            'url': article.get('url', '')
                        })
            
            elif source == 'sanctions':
                # Extract sanctions information
                if content.get('is_sanctioned', False):
                    key_findings.append({
                        'source': 'Sanctions Database',
                        'reliability': reliability,
                        'finding': "Entity appears on sanctions list",
                        'importance': 'critical'
                    })
        
        elif evidence_type == 'analysis':
            if source == 'ai_analysis':
                # Extract key points from AI analysis
                if 'risk_indicators' in content:
                    for indicator in content.get('risk_indicators', [])[:3]:  # Top 3 indicators
                        key_findings.append({
                            'source': 'AI Analysis',
                            'reliability': reliability,
                            'finding': indicator.get('description', 'Risk indicator identified'),
                            'importance': 'medium'
                        })
    
    # Sort findings by importance
    importance_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    key_findings.sort(key=lambda x: importance_order.get(x.get('importance', 'low'), 999))
    
    return key_findings

def generate_recommendations(entity_data, risk_data, evidence_items, transactions):
    """
    Generate recommendations based on entity data and risk assessment
    
    Args:
        entity_data: Entity dictionary
        risk_data: Risk dictionary
        evidence_items: List of evidence dictionaries
        transactions: List of transaction dictionaries
        
    Returns:
        list: Recommendations
    """
    recommendations = []
    
    # Base recommendations on risk level
    risk_score = risk_data.get('score', 5)
    risk_level = get_risk_level(risk_score)
    
    # Add recommendations based on risk level
    if risk_level in ['critical', 'high']:
        recommendations.append({
            'priority': 'high',
            'action': 'Conduct enhanced due diligence on entity',
            'rationale': f"Entity has a {risk_level} risk score of {risk_score}"
        })
        
        recommendations.append({
            'priority': 'high',
            'action': 'Review all transactions with this entity',
            'rationale': 'High-risk entities require transaction monitoring'
        })
        
    elif risk_level == 'medium':
        recommendations.append({
            'priority': 'medium',
            'action': 'Perform standard due diligence on entity',
            'rationale': f"Entity has a medium risk score of {risk_score}"
        })
        
    # Add recommendations based on entity type
    entity_type = entity_data.get('entity_type', '')
    
    if entity_type == 'shell':
        recommendations.append({
            'priority': 'high',
            'action': 'Verify beneficial ownership information',
            'rationale': 'Shell companies require beneficial ownership verification'
        })
    
    elif entity_type == 'financial_intermediary':
        recommendations.append({
            'priority': 'medium',
            'action': 'Verify regulatory compliance status',
            'rationale': 'Financial intermediaries must maintain regulatory compliance'
        })
    
    # Add recommendations based on evidence gaps
    evidence_sources = set(item.get('source') for item in evidence_items)
    
    if 'opencorporates' not in evidence_sources and entity_type in ['corporation', 'shell']:
        recommendations.append({
            'priority': 'medium',
            'action': 'Verify entity registration with corporate registry',
            'rationale': 'No corporate registry information available'
        })
    
    if 'sanctions' not in evidence_sources:
        recommendations.append({
            'priority': 'medium',
            'action': 'Perform comprehensive sanctions screening',
            'rationale': 'No sanctions screening results available'
        })
    
    # Add recommendations based on transaction patterns
    if len(transactions) > 0:
        # Check for round number transactions (potential structuring)
        round_amounts = 0
        for tx in transactions:
            amount = float(tx.get('amount', 0))
            if amount > 0 and amount == int(amount):
                round_amounts += 1
        
        if round_amounts >= 3 and round_amounts / len(transactions) >= 0.3:  # At least 30% are round numbers
            recommendations.append({
                'priority': 'medium',
                'action': 'Investigate potential structuring in transactions',
                'rationale': f"Entity has {round_amounts} transactions with round amounts"
            })
    
    # Sort recommendations by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 999))
    
    return recommendations
