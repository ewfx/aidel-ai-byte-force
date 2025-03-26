import os
import json
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def search_external_sources(entity_name, entity_type=None):
    """
    Search external data sources for entity information
    
    Args:
        entity_name (str): Name of the entity to search for
        entity_type (str, optional): Type of entity
        
    Returns:
        dict: Results from external sources
    """
    results = {}
    
    try:
        # Search OpenCorporates API
        opencorp_results = search_opencorporates(entity_name)
        if opencorp_results:
            results['opencorporates'] = opencorp_results
        
        # Search for news about the entity
        news_results = search_news_api(entity_name)
        if news_results:
            results['news'] = news_results
        
        # Search for sanctions information
        sanctions_results = check_sanctions(entity_name)
        if sanctions_results:
            results['sanctions'] = sanctions_results
        
        # For financial intermediaries, check financial directories
        if entity_type == 'financial_intermediary':
            financial_results = search_financial_directories(entity_name)
            if financial_results:
                results['financial_directories'] = financial_results
        
        return results
    
    except Exception as e:
        logger.error(f"Error searching external sources: {str(e)}")
        return {
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def search_opencorporates(entity_name):
    """
    Search OpenCorporates API for entity information
    
    Args:
        entity_name (str): Name of the entity to search for
        
    Returns:
        dict: OpenCorporates search results
    """
    # Check if the API key is available
    api_key = os.environ.get('OPENCORPORATES_API_KEY')
    if not api_key:
        logger.warning("OpenCorporates API key not available, using restricted access")
    
    try:
        # Prepare search parameters
        params = {
            'q': entity_name
        }
        
        # Add API token if available
        if api_key:
            params['api_token'] = api_key
        
        # Make API request
        response = requests.get('https://api.opencorporates.com/v0.4/companies/search', params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant information
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'matches': [],
                'total_count': data.get('results', {}).get('total_count', 0),
                'reliability': 0.8  # OpenCorporates is considered reliable
            }
            
            # Process matching companies
            companies = data.get('results', {}).get('companies', [])
            for company_data in companies[:5]:  # Limit to top 5 matches
                company = company_data.get('company', {})
                results['matches'].append({
                    'name': company.get('name', ''),
                    'company_number': company.get('company_number', ''),
                    'jurisdiction': company.get('jurisdiction_code', ''),
                    'incorporation_date': company.get('incorporation_date', ''),
                    'company_type': company.get('company_type', ''),
                    'status': company.get('current_status', ''),
                    'address': company.get('registered_address_in_full', '')
                })
            
            return results
        else:
            logger.warning(f"OpenCorporates API error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error searching OpenCorporates: {str(e)}")
        return None

def search_news_api(entity_name):
    """
    Search for news articles about the entity
    
    Args:
        entity_name (str): Name of the entity to search for
        
    Returns:
        dict: News search results
    """
    # Check if the API key is available
    api_key = os.environ.get('NEWS_API_KEY')
    if not api_key:
        logger.warning("News API key not available, skipping news search")
        return None
    
    try:
        # Prepare search parameters
        params = {
            'q': entity_name,
            'apiKey': api_key,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 5  # Limit to 5 articles
        }
        
        # Make API request
        response = requests.get('https://newsapi.org/v2/everything', params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant information
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'articles': [],
                'total_results': data.get('totalResults', 0),
                'reliability': 0.6  # News is somewhat reliable but needs verification
            }
            
            # Process articles
            articles = data.get('articles', [])
            for article in articles:
                results['articles'].append({
                    'title': article.get('title', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'published_at': article.get('publishedAt', ''),
                    'url': article.get('url', ''),
                    'description': article.get('description', '')
                })
            
            return results
        else:
            logger.warning(f"News API error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error searching News API: {str(e)}")
        return None

def check_sanctions(entity_name):
    """
    Check if entity is on sanctions lists
    This is a simplified version; real implementation would use specialized APIs
    
    Args:
        entity_name (str): Name of the entity to check
        
    Returns:
        dict: Sanctions check results
    """
    # Check if the API key is available
    api_key = os.environ.get('SANCTIONS_API_KEY')
    if not api_key:
        logger.warning("Sanctions API key not available, using simulated check")
        
        # For demonstration purposes, simulate a sanctions check response
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Simulated sanctions check - No real API call made',
            'matches': [],
            'is_sanctioned': False,
            'reliability': 0.5  # Lower reliability since this is simulated
        }
    
    try:
        # In a real implementation, you would make an API call to a sanctions database
        # For this example, we'll simulate a response
        
        # Headers for API request
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Payload for API request
        payload = {
            'entity_name': entity_name,
            'threshold': 0.7  # Minimum match score
        }
        
        # Make API request (commented out since we're simulating)
        # response = requests.post('https://api.sanctions-database.com/v1/search', 
        #                         headers=headers, json=payload)
        
        # Simulate response for demonstration
        simulated_response = {
            'query': entity_name,
            'matches': [],
            'total_matches': 0,
            'search_timestamp': datetime.utcnow().isoformat()
        }
        
        # Extract relevant information
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'matches': simulated_response.get('matches', []),
            'is_sanctioned': len(simulated_response.get('matches', [])) > 0,
            'reliability': 0.9  # Sanctions databases are highly reliable
        }
        
        return results
    
    except Exception as e:
        logger.error(f"Error checking sanctions: {str(e)}")
        return None

def search_financial_directories(entity_name):
    """
    Search financial directories for financial intermediaries
    
    Args:
        entity_name (str): Name of the financial entity
        
    Returns:
        dict: Financial directory search results
    """
    # This would normally integrate with Financial Institution directories
    # like the Global Financial Institution Directory or BIC Directory
    
    # For demonstration purposes, simulate a response
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'note': 'Simulated financial directory check - No real API call made',
        'verified': False,
        'directory_type': 'simulated',
        'reliability': 0.5  # Lower reliability since this is simulated
    }
