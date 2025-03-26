import os
import json
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set up OpenAI API
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def analyze_entity_data(entity_data, transaction_data):
    """
    Use the OpenAI API to analyze entity and transaction data
    Returns insights about the entity and its risk factors
    
    Args:
        entity_data (dict): Entity information
        transaction_data (list): List of transactions related to the entity
        
    Returns:
        dict: Analysis results including risk factors, anomalies, and patterns
    """
    
    try:
        # Create a context with entity and transaction data
        context = {
            "entity": entity_data,
            "transactions": transaction_data[:50]  # Limit to 50 transactions to avoid token limits
        }
        
        # Prompt for entity analysis
        prompt = f"""
        You are a financial intelligence analyst. Analyze the following entity and its transaction data
        to identify potential risks, patterns, and anomalies.
        
        Entity Information:
        {json.dumps(entity_data, indent=2)}
        
        Transaction Data Sample (up to 50 transactions):
        {json.dumps(transaction_data[:50], indent=2)}
        
        Please provide a comprehensive analysis including:
        1. Entity profile assessment
        2. Transaction pattern analysis
        3. Risk indicators and red flags
        4. Anomaly detection
        5. Recommendations for further investigation
        
        Provide your analysis in JSON format with these sections.
        """
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial intelligence and risk analysis expert. Provide detailed analysis in structured JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        # Extract and parse the response
        analysis_json = json.loads(response.choices[0].message.content)
        
        return analysis_json
    
    except Exception as e:
        logger.error(f"Error analyzing entity data with AI: {str(e)}")
        return {
            "error": str(e),
            "entity_profile": {
                "name": entity_data.get("name", "Unknown"),
                "assessment": "Error analyzing entity"
            },
            "transaction_patterns": [],
            "risk_indicators": [],
            "anomalies": [],
            "recommendations": ["Retry analysis or perform manual review due to analysis error."]
        }

def analyze_transaction_patterns(transactions):
    """
    Use AI to analyze patterns in transaction data
    
    Args:
        transactions (list): List of transaction dictionaries
        
    Returns:
        dict: Pattern analysis results
    """
    
    try:
        if not transactions or len(transactions) < 2:
            return {
                "patterns_identified": False,
                "reason": "Insufficient transaction data for pattern analysis",
                "patterns": []
            }
        
        # Prepare transaction summary for analysis
        transaction_summary = []
        for tx in transactions[:100]:  # Limit to 100 transactions for token efficiency
            transaction_summary.append({
                "amount": tx.get("amount", 0),
                "currency": tx.get("currency", "USD"),
                "timestamp": tx.get("timestamp", ""),
                "type": tx.get("type", "unknown"),
                "sender": tx.get("sender", ""),
                "receiver": tx.get("receiver", "")
            })
        
        # Prompt for pattern analysis
        prompt = f"""
        Analyze the following transaction data to identify patterns, anomalies, or suspicious activities:
        
        {json.dumps(transaction_summary, indent=2)}
        
        Identify and describe:
        1. Timing patterns (regular intervals, unusual times)
        2. Amount patterns (rounded amounts, structuring, unusual large/small transactions)
        3. Counterparty patterns (frequent interactions with specific entities)
        4. Flow patterns (circular flows, layering)
        5. Volume anomalies (unusual spikes or drops in activity)
        
        Provide your analysis in JSON format with an array of identified patterns.
        """
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial transaction analysis expert. Analyze patterns and anomalies in transaction data and provide structured results."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        # Extract and parse the response
        analysis_json = json.loads(response.choices[0].message.content)
        
        return analysis_json
    
    except Exception as e:
        logger.error(f"Error analyzing transaction patterns with AI: {str(e)}")
        return {
            "patterns_identified": False,
            "reason": f"Error analyzing patterns: {str(e)}",
            "patterns": []
        }

def generate_entity_summary(entity, evidence_items):
    """
    Generate a comprehensive summary of an entity based on available evidence
    
    Args:
        entity (dict): Entity information
        evidence_items (list): Evidence collected about the entity
        
    Returns:
        dict: Entity summary with key findings
    """
    
    try:
        # Create a context with entity and evidence data
        evidence_content = []
        for item in evidence_items:
            if isinstance(item, dict):
                evidence_content.append(item)
            else:
                # Handle Evidence model objects
                try:
                    content = json.loads(item.content) if hasattr(item, 'content') else {}
                    evidence_content.append({
                        "source": item.source if hasattr(item, 'source') else "Unknown",
                        "type": item.evidence_type if hasattr(item, 'evidence_type') else "Unknown",
                        "reliability": item.reliability_score if hasattr(item, 'reliability_score') else 1.0,
                        "content": content
                    })
                except:
                    continue
        
        # Prepare entity data
        entity_data = {}
        if hasattr(entity, 'to_dict'):
            entity_data = entity.to_dict()
        elif isinstance(entity, dict):
            entity_data = entity
        
        # Prompt for entity summary
        prompt = f"""
        Based on the following entity information and collected evidence, generate a comprehensive summary.
        
        Entity:
        {json.dumps(entity_data, indent=2)}
        
        Evidence:
        {json.dumps(evidence_content, indent=2)}
        
        Generate a detailed summary including:
        1. Entity profile and key information
        2. Key findings from evidence
        3. Identified risk factors
        4. Verification status and confidence
        5. Overall assessment
        
        Provide your summary in JSON format with these sections.
        """
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an entity research and risk analysis expert. Synthesize entity information and evidence into a comprehensive summary."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        # Extract and parse the response
        summary_json = json.loads(response.choices[0].message.content)
        
        return summary_json
    
    except Exception as e:
        logger.error(f"Error generating entity summary with AI: {str(e)}")
        entity_name = entity.get('name', 'Unknown') if isinstance(entity, dict) else getattr(entity, 'name', 'Unknown')
        return {
            "error": str(e),
            "entity_profile": {
                "name": entity_name,
                "summary": "Error generating entity summary"
            },
            "key_findings": [],
            "risk_factors": [],
            "verification_status": {
                "status": "unknown",
                "confidence": 0
            },
            "overall_assessment": "Unable to generate assessment due to an error"
        }
