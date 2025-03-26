import os
import json
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def analyze_entity(entity_name, entity_type):
    """
    Analyze an entity using OpenAI to gather additional information and evidence.
    
    Args:
        entity_name (str): The name of the entity to analyze
        entity_type (str): The type of entity (corporation, non-profit, etc.)
    
    Returns:
        dict: Analysis results including evidence and risk assessment
    """
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        
        prompt = f"""
        Analyze the following entity:
        
        Entity Name: {entity_name}
        Entity Type: {entity_type}
        
        Task: Provide a comprehensive analysis of this entity for financial risk assessment purposes.
        
        Your response should be structured as a JSON object with the following sections:
        1. entity_info: General information about the entity (description, country, address, registration_number if available)
        2. evidence: Array of evidence items with the following structure:
           - type: The type of evidence (news, regulatory, financial, etc.)
           - description: Description of the evidence
           - source: Source of the information
           - confidence: Confidence score (0.0 to 1.0)
           - data: Additional structured data related to the evidence
        3. risk_score: A numerical score between 0.0 and 10.0 representing the risk level
        4. risk_level: One of "low", "medium", "high", "critical" based on the risk score
        
        Please focus only on factual information and use a structured approach to analyze potential risks.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial risk analyst specializing in entity verification and risk assessment. You provide factual, evidence-based analyses."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        raise Exception(f"Error analyzing entity with OpenAI: {str(e)}")

def analyze_transactions(transactions):
    """
    Analyze a set of transactions using OpenAI to identify patterns and potential risks.
    
    Args:
        transactions (list): List of transaction dictionaries
        
    Returns:
        dict: Analysis results including patterns and risk indicators
    """
    try:
        # Prepare transaction data for the prompt
        transaction_data = "\n".join([
            f"ID: {tx.get('id', 'Unknown')}, "
            f"Date: {tx.get('date', 'Unknown')}, "
            f"Amount: {tx.get('amount', 0)} {tx.get('currency', 'USD')}, "
            f"Type: {tx.get('type', 'Unknown')}, "
            f"Source: {tx.get('source', 'Unknown')}, "
            f"Destination: {tx.get('destination', 'Unknown')}"
            for tx in transactions[:20]  # Limit to 20 transactions to avoid token limits
        ])
        
        prompt = f"""
        Analyze the following transaction data for patterns, anomalies, and potential risk indicators:
        
        {transaction_data}
        
        Your response should be structured as a JSON object with the following sections:
        1. patterns: Array of identified patterns in the transactions
        2. anomalies: Array of potential anomalies or suspicious activities
        3. risk_indicators: Array of specific risk indicators with confidence scores
        4. overall_assessment: Overall assessment of the transaction patterns
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial transaction analyst specializing in detecting patterns and potential risks in transaction data."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        raise Exception(f"Error analyzing transactions with OpenAI: {str(e)}")

def generate_entity_description(entity_data):
    """
    Generate a detailed description of an entity based on available data.
    
    Args:
        entity_data (dict): Dictionary containing entity information
        
    Returns:
        str: Generated entity description
    """
    try:
        # Prepare entity data for the prompt
        entity_info = "\n".join([f"{key}: {value}" for key, value in entity_data.items() if value])
        
        prompt = f"""
        Based on the following entity information, generate a comprehensive and factual description:
        
        {entity_info}
        
        The description should be factual, professional, and suitable for a risk assessment report.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial documentation specialist who creates clear, factual descriptions of entities."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        raise Exception(f"Error generating entity description with OpenAI: {str(e)}")
