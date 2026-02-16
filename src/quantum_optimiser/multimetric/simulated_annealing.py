from . import rewrite
from .. import integration
import random
import math
import pyzx
import random

def simulated_annealing_zx(
    diagram,
    cost_function,
    get_neighbor,
    initial_temp=100.0,
    cooling_rate=0.95,
    max_iterations=1000,
    min_temp=0.01,
    max_no_improvement=50,
):
    """
    Simulated Annealing for ZX diagram optimization.
    """
    # Initialize
    current_diagram = diagram.copy()
    current_cost = cost_function(current_diagram)
    initial_cost = current_cost
    best_diagram = current_diagram.copy()
    best_cost = current_cost
    
    temperature = initial_temp
    history = []
    
    no_improvement_count = 0
    accepted_moves = 0
    rejected_moves = 0
    failed_conversions = 0
    failed_neighbors = 0    
    iteration = 0

    while temperature > min_temp and iteration < max_iterations:
        # Generate neighbor and evaluate it
        circuit_copy = current_diagram.copy()
        new_diagram = get_neighbor(circuit_copy)    
        new_cost = cost_function(new_diagram)
        
        # Skip if conversion failed
        if new_cost == float('inf'):
            failed_conversions += 1
            iteration += 1
            continue
        
        # Decide whether to accept
        delta = new_cost - current_cost
        accept = False
        if delta < 0:
            # Accept if the new circuit is an improvement to the old one
            accept = True
            no_improvement_count = 0
            
            if new_cost < best_cost:
                ## Update the best diagram if we have found something better
                best_diagram = new_diagram.copy()
                best_cost = new_cost
        else:
            #If the new circuit does not offer us an improvement, then we accent with a probability
            acceptance_prob = math.exp(-delta / temperature)
            if random.random() < acceptance_prob:
                accept = True
            no_improvement_count += 1
        print("\nWe are on iteration ",iteration,"Our new cost is ",new_cost, "accept=",accept, "our best is ", best_cost)
        # Apply acceptance decision
        if accept:
            current_diagram = new_diagram
            current_cost = new_cost
            accepted_moves += 1
        else:
            rejected_moves += 1
        
        # If we haven't found an improvement then we stop early
        if no_improvement_count >= max_no_improvement:
            break
        
        # Cool down, so the probability of accepting a worse move declines
        temperature *= cooling_rate
        iteration += 1
        
        # Track history
        history.append({
            'iteration': iteration,
            'temperature': temperature,
            'current_cost': current_cost,
            'best_cost': best_cost,
            'delta': delta,
            'accepted': accept
        })
        
    print(initial_cost, best_cost)
    return best_diagram, best_cost, history


## neighbour strategies

def get_neighbor_random_vertex_random_rule(diagram):
    """
    Apply a random rule to a random vertex.
    Uses get_applicable_rules to avoid trying invalid moves.
    """
    vertices = list(diagram.vertices())
    if not vertices:
        return False
    
    # Shuffle to randomize
    random.shuffle(vertices)
    
    # Try each vertex
    for v in vertices:
        # Get applicable rules for this vertex
        applicable = rewrite.get_applicable_rules(diagram, v)
        if not applicable:
            continue
        
        # Shuffle applicable rules
        random.shuffle(applicable)
        
        # Try each applicable rule
        for rule_name in applicable:
            print("we try ",rule_name)
            try:
                # Handle pair-wise rules
                if 'fuse_with_' in rule_name:
                    result = rewrite.try_fuse(diagram, v)
                elif 'strong_comp_with_' in rule_name:
                    result = rewrite.try_strong_comp(diagram, v)

                else:
                    # Single vertex rules
                    rule_func = getattr(rewrite, f'try_{rule_name}')
                    result = rule_func(diagram, v)
                
                if result is not False:
                    return result

                    
            except Exception as e:
                print(f"Warning: Rule {rule_name} failed unexpectedly: {e}")
                continue
    
    return False


def get_neighbor_weighted_rules(diagram):
    """
    Apply rules with different probabilities.
    Uses get_applicable_rules to check validity first.
    """
    vertices = list(diagram.vertices())
    if not vertices:
        return False
    
    v = random.choice(vertices)
    
    # Get applicable rules
    applicable = rewrite.get_applicable_rules(diagram, v)
    
    if not applicable:
        # Try another vertex with random strategy
        return get_neighbor_random_vertex_random_rule(diagram) 
    
    # Define rule priorities (higher = more likely to try)
    rule_weights = {
        'remove_id': 0.30,
        'fuse': 0.25,
        'strong_comp': 0.20,
        'pi_commute_Z': 0.10,
        'pi_commute_X': 0.10,
        'color_change': 0.03,
        'copy_X': 0.01,
        'copy_Z': 0.01,
    }
    
    # Create weighted list of applicable rules
    weighted_applicable = []
    for rule_name in applicable:
        # Extract base rule name (remove _with_X suffix for pair rules)
        base_rule = rule_name.split('_with_')[0]
        weight = rule_weights.get(base_rule, 0.05)
        weighted_applicable.append((weight, rule_name))
    
    # Sort by weight (highest first) with some randomness
    weighted_applicable.sort(reverse=True, key=lambda x: x[0] * random.uniform(0.8, 1.2))
    
    # Try rules in weighted order
    for weight, rule_name in weighted_applicable:
        # Higher weight = higher chance to try
        if random.random() < weight:
            try:
                if 'fuse_with_' in rule_name:
                    result = rewrite.try_fuse(diagram, v)
                elif 'strong_comp_with_' in rule_name:
                    result = rewrite.try_strong_comp(diagram, v)
                else:
                    rule_func = getattr(rewrite, f'try_{rule_name}')
                    result = rule_func(diagram, v)
                
                if result is not False:
                    return result
                    
            except Exception as e:
                print(f"Warning: Rule {rule_name} failed unexpectedly: {e}")
                continue
    
    # Fallback
    return get_neighbor_random_vertex_random_rule(diagram)



