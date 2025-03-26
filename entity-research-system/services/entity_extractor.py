import networkx as nx
from collections import defaultdict
import re

def extract_entities(transactions):
    """
    Extract entities from transaction data
    
    Args:
        transactions (list): List of standardized transaction dictionaries
        
    Returns:
        list: List of entity dictionaries with transaction references
    """
    # Track unique entities and their transactions
    entities = defaultdict(lambda: {
        'name': '',
        'type': 'corporation',  # Default type
        'transactions': [],
        'transaction_count': 0,
        'total_volume': 0,
        'countries': set(),
        'counterparties': set()
    })
    
    # Process each transaction
    for tx in transactions:
        source = tx.get('source', 'Unknown')
        destination = tx.get('destination', 'Unknown')
        amount = float(tx.get('amount', 0))
        country = tx.get('country', '')
        tx_type = tx.get('type', 'Unknown')
        
        # Skip transactions with missing source or destination
        if source == 'Unknown' and destination == 'Unknown':
            continue
        
        # Process source entity
        if source != 'Unknown':
            entities[source]['name'] = source
            entities[source]['transactions'].append(tx)
            entities[source]['transaction_count'] += 1
            entities[source]['total_volume'] += amount
            
            if country:
                entities[source]['countries'].add(country)
            
            if destination != 'Unknown':
                entities[source]['counterparties'].add(destination)
        
        # Process destination entity
        if destination != 'Unknown':
            entities[destination]['name'] = destination
            entities[destination]['transactions'].append(tx)
            entities[destination]['transaction_count'] += 1
            entities[destination]['total_volume'] += amount
            
            if country:
                entities[destination]['countries'].add(country)
            
            if source != 'Unknown':
                entities[destination]['counterparties'].add(source)
    
    # Convert to list and infer entity types
    entity_list = []
    for name, data in entities.items():
        # Infer entity type based on name and transaction patterns
        entity_type = _infer_entity_type(name, data)
        data['type'] = entity_type
        
        # Convert sets to lists for JSON serialization
        data['countries'] = list(data['countries'])
        data['counterparties'] = list(data['counterparties'])
        
        entity_list.append(data)
    
    return entity_list

def _infer_entity_type(name, data):
    """
    Infer entity type based on name and transaction patterns
    
    Args:
        name (str): Entity name
        data (dict): Entity data including transactions
        
    Returns:
        str: Inferred entity type
    """
    # Check for keywords in name
    name_lower = name.lower()
    
    # Non-profit indicators
    if any(indicator in name_lower for indicator in ['foundation', 'ngo', 'non-profit', 'nonprofit', 'charity', 'trust', 'association']):
        return 'non_profit'
    
    # Financial intermediary indicators
    if any(indicator in name_lower for indicator in ['bank', 'financial', 'investment', 'capital', 'securities', 'credit', 'finance', 'asset']):
        return 'financial_intermediary'
    
    # Shell company indicators
    if any(indicator in name_lower for indicator in ['holding', 'international', 'overseas', 'offshore', 'global', 'enterprise']):
        # Additional checks for shell companies - high transaction count with limited counterparties
        if data['transaction_count'] > 10 and len(data['counterparties']) < 3:
            return 'shell_company'
    
    # Individual indicators
    if re.search(r'^[A-Z][a-z]+ [A-Z][a-z]+$', name) or ',' in name:
        return 'individual'
    
    # Default to corporation if no specific indicators
    return 'corporation'

def build_entity_network(transactions):
    """
    Build a network graph of entity relationships based on transactions
    
    Args:
        transactions (list): List of standardized transaction dictionaries
        
    Returns:
        networkx.Graph: Entity relationship graph
    """
    # Create directed graph
    G = nx.DiGraph()
    
    # Process each transaction
    for tx in transactions:
        source = tx.get('source', 'Unknown')
        destination = tx.get('destination', 'Unknown')
        amount = float(tx.get('amount', 0))
        tx_type = tx.get('type', 'Unknown')
        
        # Skip transactions with missing source or destination
        if source == 'Unknown' or destination == 'Unknown':
            continue
        
        # Add nodes if they don't exist
        if not G.has_node(source):
            G.add_node(source, transaction_count=0, total_volume=0)
        
        if not G.has_node(destination):
            G.add_node(destination, transaction_count=0, total_volume=0)
        
        # Update node attributes
        G.nodes[source]['transaction_count'] = G.nodes[source].get('transaction_count', 0) + 1
        G.nodes[source]['total_volume'] = G.nodes[source].get('total_volume', 0) + amount
        
        G.nodes[destination]['transaction_count'] = G.nodes[destination].get('transaction_count', 0) + 1
        G.nodes[destination]['total_volume'] = G.nodes[destination].get('total_volume', 0) + amount
        
        # Add or update edge
        if G.has_edge(source, destination):
            G[source][destination]['weight'] = G[source][destination].get('weight', 0) + amount
            G[source][destination]['transaction_count'] = G[source][destination].get('transaction_count', 0) + 1
            # Append transaction type if not already in the list
            if 'types' not in G[source][destination]:
                G[source][destination]['types'] = []
            if tx_type not in G[source][destination]['types']:
                G[source][destination]['types'].append(tx_type)
        else:
            G.add_edge(source, destination, weight=amount, transaction_count=1, types=[tx_type])
    
    return G

def identify_key_entities(entity_network):
    """
    Identify key entities in the network based on centrality measures
    
    Args:
        entity_network (networkx.Graph): Entity relationship graph
        
    Returns:
        dict: Dictionary of key entities with importance metrics
    """
    # Calculate various centrality measures
    degree_centrality = nx.degree_centrality(entity_network)
    in_degree_centrality = nx.in_degree_centrality(entity_network)
    out_degree_centrality = nx.out_degree_centrality(entity_network)
    
    try:
        # These may fail in some graph configurations
        betweenness_centrality = nx.betweenness_centrality(entity_network)
        eigenvector_centrality = nx.eigenvector_centrality(entity_network, max_iter=1000)
    except:
        # Fallback to simpler measures if the above fail
        betweenness_centrality = {node: 0 for node in entity_network.nodes()}
        eigenvector_centrality = {node: 0 for node in entity_network.nodes()}
    
    # Combine metrics to identify key entities
    key_entities = {}
    for node in entity_network.nodes():
        importance_score = (
            degree_centrality.get(node, 0) * 0.2 +
            in_degree_centrality.get(node, 0) * 0.2 +
            out_degree_centrality.get(node, 0) * 0.2 +
            betweenness_centrality.get(node, 0) * 0.2 +
            eigenvector_centrality.get(node, 0) * 0.2
        )
        
        transaction_count = entity_network.nodes[node].get('transaction_count', 0)
        total_volume = entity_network.nodes[node].get('total_volume', 0)
        
        key_entities[node] = {
            'importance_score': importance_score,
            'transaction_count': transaction_count,
            'total_volume': total_volume,
            'degree_centrality': degree_centrality.get(node, 0),
            'in_degree_centrality': in_degree_centrality.get(node, 0),
            'out_degree_centrality': out_degree_centrality.get(node, 0),
            'betweenness_centrality': betweenness_centrality.get(node, 0),
            'eigenvector_centrality': eigenvector_centrality.get(node, 0)
        }
    
    # Sort by importance score
    sorted_entities = sorted(key_entities.items(), key=lambda x: x[1]['importance_score'], reverse=True)
    return dict(sorted_entities)
