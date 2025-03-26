import os
import json
import requests
import logging
import time
from urllib.parse import quote

logger = logging.getLogger(__name__)

# API Keys (from environment variables)
OPENCORPORATES_API_KEY = os.environ.get("OPENCORPORATES_API_KEY", "")
COMPANY_HOUSE_API_KEY = os.environ.get("COMPANY_HOUSE_API_KEY", "")

def fetch_entity_data(entity_name):
    """
    Fetch data about an entity from multiple external sources
    
    Args:
        entity_name (str): Name of the entity to search for
        
    Returns:
        dict: Data from various sources keyed by source name
    """
    results = {}
    
    # Attempt to fetch from multiple sources
    try:
        # OpenCorporates API
        opencorp_data = fetch_from_opencorporates(entity_name)
        if opencorp_data:
            results["OpenCorporates"] = opencorp_data
        
        # Companies House API (UK)
        if COMPANY_HOUSE_API_KEY:
            ch_data = fetch_from_companies_house(entity_name)
            if ch_data:
                results["Companies House"] = ch_data
        
        # Wikipedia - general information
        wiki_data = fetch_from_wikipedia(entity_name)
        if wiki_data:
            results["Wikipedia"] = wiki_data
        
        # News API - recent news about the entity
        news_data = fetch_from_news_api(entity_name)
        if news_data:
            results["News"] = news_data
        
    except Exception as e:
        logger.error(f"Error fetching entity data: {str(e)}")
    
    return results

def fetch_from_opencorporates(entity_name):
    """
    Fetch company data from OpenCorporates API
    
    Args:
        entity_name (str): Company name to search
        
    Returns:
        dict: Company data or None if not found
    """
    if not OPENCORPORATES_API_KEY:
        logger.warning("OpenCorporates API key not set, skipping")
        return None
    
    try:
        # Encode entity name for URL
        encoded_name = quote(entity_name)
        url = f"https://api.opencorporates.com/v0.4/companies/search?q={encoded_name}&api_token={OPENCORPORATES_API_KEY}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            # Check if we have results
            if data.get('results') and data['results'].get('companies'):
                companies = data['results']['companies']
                
                # Return the first match (most relevant)
                if companies:
                    return companies[0]['company']
        
        return None
    
    except Exception as e:
        logger.error(f"Error fetching from OpenCorporates: {str(e)}")
        return None

def fetch_from_companies_house(entity_name):
    """
    Fetch company data from UK Companies House API
    
    Args:
        entity_name (str): Company name to search
        
    Returns:
        dict: Company data or None if not found
    """
    if not COMPANY_HOUSE_API_KEY:
        return None
    
    try:
        encoded_name = quote(entity_name)
        url = f"https://api.companieshouse.gov.uk/search/companies?q={encoded_name}"
        
        auth = (COMPANY_HOUSE_API_KEY, '')
        response = requests.get(url, auth=auth)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we have results
            if data.get('items') and len(data['items']) > 0:
                # Get the company number of the first result
                company_number = data['items'][0]['company_number']
                
                # Fetch detailed company profile
                profile_url = f"https://api.companieshouse.gov.uk/company/{company_number}"
                profile_response = requests.get(profile_url, auth=auth)
                
                if profile_response.status_code == 200:
                    return profile_response.json()
        
        return None
    
    except Exception as e:
        logger.error(f"Error fetching from Companies House: {str(e)}")
        return None

def fetch_from_wikipedia(entity_name):
    """
    Fetch entity data from Wikipedia
    
    Args:
        entity_name (str): Entity name to search
        
    Returns:
        str: Wikipedia extract or None if not found
    """
    try:
        # Encode entity name for URL
        encoded_name = quote(entity_name)
        
        # First search for the page
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_name}&format=json"
        search_response = requests.get(search_url)
        
        if search_response.status_code != 200:
            return None
        
        search_data = search_response.json()
        
        # Check if we have search results
        if not search_data.get('query') or not search_data['query'].get('search') or len(search_data['query']['search']) == 0:
            return None
        
        # Get the page title from the first search result
        page_title = search_data['query']['search'][0]['title']
        encoded_title = quote(page_title)
        
        # Now get the page extract
        extract_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={encoded_title}&format=json"
        extract_response = requests.get(extract_url)
        
        if extract_response.status_code != 200:
            return None
        
        extract_data = extract_response.json()
        
        # Navigate the response to get the extract
        pages = extract_data.get('query', {}).get('pages', {})
        if not pages:
            return None
        
        # Get the first page (there should only be one)
        page_id = next(iter(pages))
        extract = pages[page_id].get('extract')
        
        return extract
    
    except Exception as e:
        logger.error(f"Error fetching from Wikipedia: {str(e)}")
        return None

def fetch_from_news_api(entity_name, days=30):
    """
    Fetch recent news about an entity
    
    Args:
        entity_name (str): Entity name to search
        days (int): Number of days to look back
        
    Returns:
        list: News articles or None if not found
    """
    NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
    if not NEWS_API_KEY:
        return None
    
    try:
        encoded_name = quote(entity_name)
        url = f"https://newsapi.org/v2/everything?q={encoded_name}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            # Check if we have results
            if data.get('status') == 'ok' and data.get('articles'):
                # Return up to 5 most recent articles
                articles = data['articles'][:5]
                
                # Extract relevant information
                simplified_articles = []
                for article in articles:
                    simplified_articles.append({
                        'title': article.get('title'),
                        'description': article.get('description'),
                        'source': article.get('source', {}).get('name'),
                        'published_at': article.get('publishedAt'),
                        'url': article.get('url')
                    })
                
                return simplified_articles
        
        return None
    
    except Exception as e:
        logger.error(f"Error fetching from News API: {str(e)}")
        return None

def search_entity_connections(entity_name):
    """
    Search for connections to other entities
    
    Args:
        entity_name (str): Entity name to search connections for
        
    Returns:
        list: Connected entities or empty list if none found
    """
    connected_entities = []
    
    try:
        # For now, simplify this to just use OpenCorporates
        if OPENCORPORATES_API_KEY:
            # Encode entity name for URL
            encoded_name = quote(entity_name)
            
            # First get the company details
            url = f"https://api.opencorporates.com/v0.4/companies/search?q={encoded_name}&api_token={OPENCORPORATES_API_KEY}"
            
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                
                # Check if we have results
                if data.get('results') and data['results'].get('companies') and data['results']['companies']:
                    company = data['results']['companies'][0]['company']
                    company_jurisdiction = company.get('jurisdiction_code')
                    company_number = company.get('company_number')
                    
                    if company_jurisdiction and company_number:
                        # Get officers (directors, etc.)
                        officers_url = f"https://api.opencorporates.com/v0.4/companies/{company_jurisdiction}/{company_number}/officers?api_token={OPENCORPORATES_API_KEY}"
                        officers_response = requests.get(officers_url)
                        
                        if officers_response.status_code == 200:
                            officers_data = officers_response.json()
                            
                            if officers_data.get('results') and officers_data['results'].get('officers'):
                                for officer in officers_data['results']['officers']:
                                    officer_name = officer['officer'].get('name')
                                    position = officer['officer'].get('position')
                                    
                                    # Search for other companies with this officer
                                    other_companies = search_officer_companies(officer_name)
                                    
                                    for company in other_companies:
                                        if company.get('name') != entity_name:
                                            connected_entities.append({
                                                'name': company.get('name'),
                                                'relationship': f"Shared officer: {officer_name} ({position})",
                                                'jurisdiction': company.get('jurisdiction_code'),
                                                'source': 'OpenCorporates'
                                            })
    
    except Exception as e:
        logger.error(f"Error searching entity connections: {str(e)}")
    
    return connected_entities

def search_officer_companies(officer_name):
    """
    Search for companies associated with an officer
    
    Args:
        officer_name (str): Officer name to search
        
    Returns:
        list: Companies associated with the officer
    """
    if not OPENCORPORATES_API_KEY:
        return []
    
    try:
        encoded_name = quote(officer_name)
        url = f"https://api.opencorporates.com/v0.4/officers/search?q={encoded_name}&api_token={OPENCORPORATES_API_KEY}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            companies = []
            if data.get('results') and data['results'].get('officers'):
                for officer_result in data['results']['officers']:
                    officer = officer_result.get('officer', {})
                    company = officer.get('company', {})
                    
                    if company:
                        companies.append({
                            'name': company.get('name'),
                            'jurisdiction_code': company.get('jurisdiction_code'),
                            'company_number': company.get('company_number')
                        })
            
            return companies
    
    except Exception as e:
        logger.error(f"Error searching officer companies: {str(e)}")
    
    return []
