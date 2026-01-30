from . import rewrite
from .. import integration
import random
import math
import pyzx

def simulated_annealing_zx(
    diagram,
    cost_function,
    get_neighbor,
    initial_temp=100.0,
    cooling_rate=0.95,
    max_iterations=1000,
    min_temp=0.01,
    max_no_improvement=50,
    verbose=False,
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
        
    if verbose:
        print(f"Initial cost: {current_cost:.2f}")
    
    iteration = 0
    while temperature > min_temp and iteration < max_iterations:
        # Generate neighbor
        try:
            import inspect
            sig = inspect.signature(get_neighbor)
            if 'cost_function' in sig.parameters:
                new_diagram = get_neighbor(current_diagram, cost_function)
            else:
                new_diagram = get_neighbor(current_diagram)
        except Exception as e:
            iteration += 1
            continue
        
        if new_diagram is False:
            failed_neighbors += 1
            iteration += 1
            continue
        
        # Evaluate new diagram
        new_cost = cost_function(new_diagram)
        
        # Skip if conversion failed
        if new_cost == float('inf'):
            failed_conversions += 1
            iteration += 1
            continue
        
        delta = new_cost - current_cost
        
        # Decide whether to accept
        accept = False
        if delta < 0:
            accept = True
            no_improvement_count = 0
            
            if new_cost < best_cost:
                best_diagram = new_diagram.copy()
                best_cost = new_cost
                if verbose:
                    print(f"Iter {iteration}: NEW BEST! {best_cost:.2f} (delta: {delta:.2f})")
        else:
            acceptance_prob = math.exp(-delta / temperature)
            if random.random() < acceptance_prob:
                accept = True
                if verbose and iteration % 100 == 0:
                    print(f"Iter {iteration}: Accepted worse move (delta: {delta:.2f}, prob: {acceptance_prob:.3f})")
            no_improvement_count += 1
        
        # Apply acceptance decision
        if accept:
            current_diagram = new_diagram
            current_cost = new_cost
            accepted_moves += 1
        else:
            rejected_moves += 1
        
        # Check for early stopping
        if no_improvement_count >= max_no_improvement:
            if verbose:
                print(f"Early stopping: {max_no_improvement} iterations without improvement")
            break
        
        # Cool down
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
        
        # Periodic status
        if verbose and iteration % 100 == 0:
            accept_rate = accepted_moves / (accepted_moves + rejected_moves) if (accepted_moves + rejected_moves) > 0 else 0
            print(f"Iter {iteration}: T={temperature:.2f}, Current={current_cost:.2f}, Best={best_cost:.2f}, Accept={accept_rate:.1%}")
    
    if verbose:
        print(f"\n=== FINAL RESULTS ===")
        print(f"Original cost:" initial_cost)
        print(f"Best cost: {best_cost:.2f}")
        print(f"Accepted: {accepted_moves}, Rejected: {rejected_moves}")
        print(f"Failed neighbors: {failed_neighbors}, Failed conversions: {failed_conversions}")
        print(f"Total iterations: {iteration}")
    print(initial_cost, best_cost)
    return best_diagram, best_cost, history
import random

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


def get_neighbor_all_vertices_first_rule(diagram):
    """
    Try to apply any rule to any vertex (more exhaustive).
    Uses get_applicable_rules for efficiency.
    """
    vertices = list(diagram.vertices())
    random.shuffle(vertices)
    
    # Priority order (try these first)
    priority_order = [
        'remove_id',
        'fuse',
        'strong_comp',
        'pi_commute_Z',
        'pi_commute_X',
        'color_change',
        'copy_X',
        'copy_Z',
    ]
    
    for v in vertices:
        applicable = rewrite.get_applicable_rules(diagram, v)
        
        if not applicable:
            continue
        
        # Sort by priority
        sorted_applicable = []
        for priority_rule in priority_order:
            matching = [r for r in applicable if r.startswith(priority_rule)]
            sorted_applicable.extend(matching)
        
        # Add any rules not in priority list
        sorted_applicable.extend([r for r in applicable if r not in sorted_applicable])
        
        # Try first applicable rule
        for rule_name in sorted_applicable:
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
    
    return False


def get_neighbor_all_applicable_random_pick(diagram):
    """
    Collect ALL applicable rules across ALL vertices, then pick one randomly.
    Gives equal probability to each possible move.
    Uses get_applicable_rules for efficiency.
    """
    all_moves = []
    
    # Collect all possible moves
    for v in diagram.vertices():
        applicable = rewrite.get_applicable_rules(diagram, v)
        for rule_name in applicable:
            all_moves.append((v, rule_name))
    
    if not all_moves:
        return False
    
    # Pick a random move
    v, rule_name = random.choice(all_moves)
    
    try:
        if 'fuse_with_' in rule_name:
            result = rewrite.try_fuse(diagram, v)
        elif 'strong_comp_with_' in rule_name:
            result = rewrite.try_strong_comp(diagram, v)
        else:
            rule_func = getattr(rewrite, f'try_{rule_name}')
            result = rule_func(diagram, v)
        
        return result if result is not False else False
        
    except Exception as e:
        print(f"Warning: Rule {rule_name} failed unexpectedly: {e}")
        return False


def get_neighbor_greedy(diagram, cost_function):
    """
    Greedy neighbor: try all applicable rules and pick the one that reduces cost most.
    More expensive but potentially better moves.
    """
    best_neighbor = False
    best_cost = float('inf')
    
    for v in diagram.vertices():
        applicable = rewrite.get_applicable_rules(diagram, v)
        
        for rule_name in applicable:
            try:
                # Apply rule
                if 'fuse_with_' in rule_name:
                    candidate = rewrite.try_fuse(diagram, v)
                elif 'strong_comp_with_' in rule_name:
                    candidate = rewrite.try_strong_comp(diagram, v)
                else:
                    rule_func = getattr(rewrite, f'try_{rule_name}')
                    candidate = rule_func(diagram, v)
                
                if candidate is not False:
                    # Evaluate cost
                    candidate_cost = cost_function(candidate)
                    if candidate_cost < best_cost:
                        best_cost = candidate_cost
                        best_neighbor = candidate
                        
            except Exception as e:
                continue
    
    return best_neighbor


def get_neighbor_semi_greedy(diagram, cost_function, sample_size=10):
    """
    Semi-greedy: sample a few random moves and pick the best one.
    Balance between speed and quality.
    """
    all_moves = []
    
    # Collect all possible moves
    for v in diagram.vertices():
        applicable = rewrite.get_applicable_rules(diagram, v)
        for rule_name in applicable:
            all_moves.append((v, rule_name))
    
    if not all_moves:
        return False
    
    # Sample random moves
    sample_size = min(sample_size, len(all_moves))
    sampled_moves = random.sample(all_moves, sample_size)
    
    best_neighbor = False
    best_cost = float('inf')
    
    for v, rule_name in sampled_moves:
        try:
            # Apply rule
            if 'fuse_with_' in rule_name:
                candidate = rewrite.try_fuse(diagram, v)
            elif 'strong_comp_with_' in rule_name:
                candidate = rewrite.try_strong_comp(diagram, v)
            else:
                rule_func = getattr(rewrite, f'try_{rule_name}')
                candidate = rule_func(diagram, v)
            
            if candidate is not False:
                # Evaluate cost
                candidate_cost = cost_function(candidate)
                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_neighbor = candidate
                    
        except Exception as e:
            continue
    
    return best_neighbor