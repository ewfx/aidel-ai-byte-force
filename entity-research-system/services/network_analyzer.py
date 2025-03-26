import networkx as nx
import numpy as np
from collections import defaultdict

def analyze_network(entities):
    """
    Analyze entity network to identify relationships and patterns
    
    Args:
        entities (list): List of entity dictionaries with transaction data
        
    Returns:
        list: List of relationship data between entities
    """
    # Create entity lookup for faster access
    entity_lookup = {entity['name']: entity for entity in entities}
    
    # Create a directed graph for entity relationships
    G = nx.DiGraph()
    
    # Track all transaction pairs
    transaction_pairs = []
    
    # Add entities as nodes
    for entity in entities:
        G.add_node(entity['name'], 
                  type=entity['type'],
                  transaction_count=entity['transaction_count'],
                  total_volume=entity['total_volume'])
        
        # Extract transaction pairs
        for tx in entity['transactions']:
            source = tx.get('source', 'Unknown')
            destination = tx.get('destination', 'Unknown')
            
            if source != 'Unknown' and destination != 'Unknown':
                transaction_pairs.append({
                    'source': source,
                    'destination': destination,
                    'amount': float(tx.get('amount', 0)),
                    'type': tx.get('type', 'Unknown')
                })
    
    # Add edges based on transaction pairs
    edge_data = defaultdict(lambda: {'weight': 0, 'transactions': 0, 'types': set()})
    
    for pair in transaction_pairs:
        source = pair['source']
        destination = pair['destination']
        
        # Skip self-loops
        if source == destination:
            continue
        
        key = (source, destination)
        edge_data[key]['weight'] += pair['amount']
        edge_data[key]['transactions'] += 1
        edge_data[key]['types'].add(pair['type'])
    
    # Add edges to graph
    for (source, destination), data in edge_data.items():
        if G.has_node(source) and G.has_node(destination):
            G.add_edge(source, destination, 
                      weight=data['weight'],
                      transaction_count=data['transactions'],
                      types=list(data['types']))
    
    # Calculate network metrics
    try:
        betweenness = nx.betweenness_centrality(G, weight='weight')
        eigenvector = nx.eigenvector_centrality(G, weight='weight', max_iter=1000)
    except:
        # Fallback for cases where the algorithms fail
        betweenness = {node: 0 for node in G.nodes()}
        eigenvector = {node: 0 for node in G.nodes()}
    
    # Add metrics to nodes
    for node in G.nodes():
        G.nodes[node]['betweenness'] = betweenness.get(node, 0)
        G.nodes[node]['eigenvector'] = eigenvector.get(node, 0)
    
    # Identify communities using Louvain method
    try:
        from community import best_partition
        partition = best_partition(G.to_undirected())
        for node, community_id in partition.items():
            G.nodes[node]['community'] = community_id
    except:
        # If community detection fails or is unavailable, skip it
        for node in G.nodes():
            G.nodes[node]['community'] = 0
    
    # Generate relationship data
    relationships = []
    
    for source, destination, data in G.edges(data=True):
        # Only include edges with sufficient weight
        if data['weight'] > 0:
            # Infer relationship type
            relationship_type = _infer_relationship_type(
                G.nodes[source]['type'], 
                G.nodes[destination]['type'],
                data['types'],
                data['transaction_count']
            )
            
            relationships.append({
                'source': source,
                'target': destination,
                'type': relationship_type,
                'weight': data['weight'],
                'transaction_count': data['transaction_count'],
                'description': f"{relationship_type.capitalize()} relationship with {data['transaction_count']} transactions"
            })
    
    return relationships

def _infer_relationship_type(source_type, target_type, transaction_types, transaction_count):
    """
    Infer the type of relationship between two entities
    
    Args:
        source_type (str): Type of source entity
        target_type (str): Type of target entity
        transaction_types (list): Types of transactions between entities
        transaction_count (int): Number of transactions
        
    Returns:
        str: Inferred relationship type
    """
    # Convert transaction types to set for easier checking
    tx_types = set(transaction_types)
    
    # Check for parent/subsidiary relationship
    if source_type == 'corporation' and target_type == 'corporation':
        if 'dividend' in tx_types or 'investment' in tx_types:
            return 'parent-subsidiary'
    
    # Check for investment relationship
    if 'investment' in tx_types:
        return 'investor-investee'
    
    # Check for banking relationship
    if source_type == 'financial_intermediary' or target_type == 'financial_intermediary':
        return 'banking'
    
    # Check for customer relationship
    if 'payment' in tx_types and transaction_count > 5:
        return 'customer'
    
    # Check for supplier relationship
    if 'invoice' in tx_types or 'payment' in tx_types:
        return 'supplier'
    
    # Check for donation relationship
    if 'donation' in tx_types or target_type == 'non_profit':
        return 'donor'
    
    # Default to business relationship
    return 'business'

def detect_suspicious_patterns(entity_network):
    """
    Detect suspicious patterns in the entity network
    
    Args:
        entity_network (networkx.Graph): Entity relationship graph
        
    Returns:
        list: List of suspicious patterns detected
    """
    suspicious_patterns = []
    
    # 1. Detect circular transaction patterns
    try:
        cycles = list(nx.simple_cycles(entity_network))
        for cycle in cycles:
            if len(cycle) >= 3:  # Only consider cycles with 3 or more entities
                cycle_entities = ', '.join(cycle)
                suspicious_patterns.append({
                    'type': 'circular_transactions',
                    'description': f'Circular transaction pattern detected: {cycle_entities}',
                    'entities': cycle,
                    'severity': 'high'
                })
    except:
        # If cycle detection fails, skip it
        pass
    
    # 2. Detect shell company patterns (high betweenness, low transaction diversity)
    for node, data in entity_network.nodes(data=True):
        if data.get('betweenness', 0) > 0.3 and data.get('type') == 'shell_company':
            # Get incoming and outgoing transactions
            in_edges = entity_network.in_edges(node, data=True)
            out_edges = entity_network.out_edges(node, data=True)
            
            # Check if entity receives from multiple sources but sends to limited destinations
            if len(in_edges) > 3 and len(out_edges) < 2:
                suspicious_patterns.append({
                    'type': 'shell_company_pattern',
                    'description': f'Potential shell company pattern: {node} receives from multiple sources but sends to limited destinations',
                    'entity': node,
                    'severity': 'high'
                })
    
    # 3. Detect unusual transaction volume patterns
    # Get average transaction weight
    edge_weights = [data['weight'] for _, _, data in entity_network.edges(data=True)]
    if edge_weights:
        avg_weight = np.mean(edge_weights)
        std_weight = np.std(edge_weights)
        
        # Flag edges with abnormally high weights
        for source, target, data in entity_network.edges(data=True):
            if data['weight'] > avg_weight + 3 * std_weight:  # More than 3 standard deviations
                suspicious_patterns.append({
                    'type': 'unusual_volume',
                    'description': f'Unusual transaction volume from {source} to {target}: {data["weight"]}',
                    'source': source,
                    'target': target,
                    'amount': data['weight'],
                    'severity': 'medium'
                })
    
    # 4. Detect isolated high-risk clusters
    # This would require community detection which we've already attempted
    
    return suspicious_patterns
