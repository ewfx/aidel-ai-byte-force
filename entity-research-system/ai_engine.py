import os
import json
import logging
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user

logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_entity(entity_data, external_data=None):
    """
    Analyze entity data using AI to identify relevant information,
    generate description, and identify potential risk factors
    
    Args:
        entity_data (dict): Entity data including name, type, and transactions
        external_data (dict): Additional data from external sources
        
    Returns:
        dict: Analysis results including description, evidence, and risk factors
    """
    try:
        # Prepare data for analysis
        combined_data = {
            "entity": entity_data,
            "external_data": external_data or {}
        }
        
        # Format the data for the AI prompt
        data_str = json.dumps(combined_data, default=str)
        
        # Create prompt for the AI
        prompt = f"""
        Analyze the following entity data and provide a comprehensive analysis:
        
        {data_str}
        
        Please provide the following in JSON format:
        1. A detailed description of the entity
        2. List of evidence/facts discovered about the entity
        3. Potential risk factors
        4. Key relationships with other entities
        5. Recommended additional data sources to investigate

        Format your response as a valid JSON object.
        """
        
        # Make API call to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert financial analyst specializing in entity research and risk assessment. Provide detailed, factual analysis based only on the data provided."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Structure the analysis
        analysis = {
            "description": result.get("description", "No description available"),
            "evidence": [
                {
                    "content": item,
                    "source": "AI Analysis",
                    "confidence": 0.8  # Default confidence for AI-generated evidence
                }
                for item in result.get("evidence", [])
            ],
            "risk_factors": result.get("risk_factors", []),
            "relationships": result.get("key_relationships", []),
            "recommended_sources": result.get("recommended_additional_data_sources", [])
        }
        
        # Add external data as evidence if available
        if external_data:
            for source, data in external_data.items():
                if data:
                    analysis["evidence"].append({
                        "content": data,
                        "source": source,
                        "confidence": 0.9  # Higher confidence for external data
                    })
        
        return analysis
    
    except Exception as e:
        logger.error(f"Error analyzing entity with AI: {str(e)}")
        # Return basic analysis if AI fails
        return {
            "description": f"Entity: {entity_data.get('name')} (Type: {entity_data.get('type')})",
            "evidence": [],
            "risk_factors": [],
            "relationships": [],
            "recommended_sources": []
        }

def generate_evidence_summary(entity_id, evidence_list):
    """
    Generate a summary of evidence for a given entity
    
    Args:
        entity_id (int): Entity ID
        evidence_list (list): List of evidence objects
    
    Returns:
        str: Evidence summary
    """
    try:
        # Format evidence for the AI prompt
        evidence_str = "\n".join([f"- {item.source}: {item.content}" for item in evidence_list])
        
        prompt = f"""
        Summarize the following evidence about an entity (ID: {entity_id}):
        
        {evidence_str}
        
        Provide a concise, factual summary that highlights the most important points. Identify any contradictions or suspicious elements.
        """
        
        # Make API call to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in financial intelligence, summarizing evidence about entities."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"Error generating evidence summary: {str(e)}")
        return "Error generating summary. Please review the individual evidence items."

def analyze_transaction_patterns(entity_name, transactions):
    """
    Analyze transaction patterns for potential anomalies
    
    Args:
        entity_name (str): Name of the entity
        transactions (list): List of transaction dictionaries
    
    Returns:
        dict: Analysis of transaction patterns
    """
    try:
        # Format transactions for the AI prompt
        transactions_str = json.dumps(transactions, default=str)
        
        prompt = f"""
        Analyze the following transactions related to entity "{entity_name}":
        
        {transactions_str}
        
        Identify any suspicious patterns, anomalies, or red flags in these transactions. Consider:
        1. Unusual transaction sizes or frequencies
        2. Circular transactions
        3. Transactions with high-risk entities
        4. Irregular timing patterns
        5. Potential money laundering indicators
        
        Provide your analysis as a JSON object with the following structure:
        1. "patterns_detected": list of pattern descriptions
        2. "risk_indicators": list of risk indicators
        3. "recommended_investigations": list of recommended follow-up actions
        """
        
        # Make API call to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in financial crime detection and transaction analysis."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing transaction patterns: {str(e)}")
        return {
            "patterns_detected": [],
            "risk_indicators": [],
            "recommended_investigations": ["Unable to analyze transactions due to an error."]
        }

def generate_entity_report(entity, evidence, risk_score, transactions):
    """
    Generate a comprehensive report for an entity
    
    Args:
        entity: Entity object
        evidence: List of evidence objects
        risk_score: Risk score object
        transactions: List of transaction objects
    
    Returns:
        str: Generated report in markdown format
    """
    try:
        # Prepare data for the report
        entity_data = {
            "name": entity.name,
            "type": entity.entity_type,
            "description": entity.description,
            "created_at": str(entity.created_at)
        }
        
        evidence_data = [
            {"source": e.source, "content": e.content, "confidence": e.confidence}
            for e in evidence
        ]
        
        risk_data = {
            "score": risk_score.score,
            "factors": json.loads(risk_score.factors) if risk_score.factors else [],
            "last_updated": str(risk_score.last_updated)
        }
        
        transaction_data = [
            {
                "sender": tx.sender,
                "receiver": tx.receiver,
                "amount": tx.amount,
                "currency": tx.currency,
                "timestamp": str(tx.timestamp)
            }
            for tx in transactions
        ]
        
        report_data = {
            "entity": entity_data,
            "evidence": evidence_data,
            "risk_assessment": risk_data,
            "transactions": transaction_data
        }
        
        # Convert to JSON for prompt
        report_json = json.dumps(report_data, default=str)
        
        prompt = f"""
        Generate a comprehensive entity research report based on the following data:
        
        {report_json}
        
        The report should include:
        1. Executive Summary
        2. Entity Overview and Background
        3. Evidence Analysis
        4. Transaction Pattern Analysis
        5. Risk Assessment
        6. Recommendations for Further Investigation
        
        Format the report in markdown for easy reading.
        """
        
        # Make API call to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert financial analyst creating detailed entity research reports."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"Error generating entity report: {str(e)}")
        return f"# Error Generating Report\n\nUnable to generate report for {entity.name} due to an error.\n\nPlease review the raw data and try again."
