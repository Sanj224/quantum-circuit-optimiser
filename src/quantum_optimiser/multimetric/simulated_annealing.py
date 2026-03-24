from . import rewrite
from .. import integration
import random
import math
import pyzx
import random
from . import loss

def simulated_annealing_zx(
    circuit,
    cost_function,
    get_neighbor,
    initial_temp=100.0,
    cooling_rate=0.95,
    max_iterations=1000,
    min_temp=0.01,
    max_no_improvement=50,
    hardware=None
):
    """
    Simulated Annealing for ZX diagram optimization.
    """
    
    baseline = loss._compute_stats(circuit,hardware)
    print("our baseline is:", baseline)
    diagram = integration.qiskit_to_pyzx(circuit)
    cost_function = loss.cost_function_from_circuit(cost_function, None, hardware, baseline)

    current_diagram = diagram
    current_cost = cost_function(diagram)   
    best_diagram = diagram.copy()
    best_cost = current_cost
    initial_cost = current_cost

    temperature = initial_temp
    history = []
    
    best_no_improvement_count = 0
    no_improvement_count = 0
    accepted_moves = 0
    rejected_moves = 0
    failed_conversions = 0
    iteration = 0
    swap_try = 0
    swap_succes = 0
    while temperature > min_temp and iteration < max_iterations:
        # Generate neighbor and evaluate it
        
        new_diagram = get_neighbor(current_diagram)    
        if hardware is not None:
            swap_try += 1
            new_circuit = integration.pyzx_to_qiskit(new_diagram)
            candidate = hardware.try_qubit_permutation(new_circuit)
            if candidate is not None:
                swap_succes += 1
                candidate_diagram = integration.qiskit_to_pyzx(candidate)
                candidate_cost = cost_function(candidate_diagram)
                new_diagram_cost = cost_function(new_diagram)
                if candidate_cost < new_diagram_cost:
                    new_diagram = candidate_diagram
                    new_cost = candidate_cost
                else:
                    new_cost = new_diagram_cost
            else:
                new_cost = cost_function(new_diagram)
            

        else:
            new_cost = cost_function(new_diagram)
            
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
            no_improvement_count= 0
            if new_cost < best_cost:
                ## Update the best diagram if we have found something better
                print("we have an improvement")
                best_diagram = new_diagram.copy()
                best_cost = new_cost
                best_no_improvement_count = 0
            else:
                best_no_improvement_count += 1
        else:
            #If the new circuit does not offer us an improvement, then we accent with a probability
            acceptance_prob = math.exp(-delta / temperature)
            if random.random() < acceptance_prob:
                accept = True
                no_improvement_count += 1
                best_no_improvement_count +=1
        #print("\nWe are on iteration ",iteration,"Our new cost is ",new_cost, "accept=",accept, "our best is ", best_cost)
        #print(loss._compute_stats(integration.pyzx_to_qiskit(diagram),hardware))
        # Apply acceptance decision
        if accept:
            current_diagram = new_diagram
            current_cost = new_cost
            accepted_moves += 1
        else:
            rejected_moves += 1
        
        #If we haven't found an improvement then we go back to our original diagram 
        if best_no_improvement_count >= max_no_improvement:
            # restart from best known solution
            print("had to go here again")
            current_diagram = best_diagram.copy()
            current_cost = best_cost
            no_improvement_count = 0
            best_no_improvement_count = 0
            temperature = min(temperature * 2.0, initial_temp * 0.5)  # reheat a bit
            
        
        # Reheat if stuck to kick us out of local minima otherwise cool down
        if no_improvement_count > 5 and no_improvement_count % 20 == 0:
            temperature = min(temperature * 1.5, initial_temp * 0.5)
        else:
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

    best_circuit = integration.pyzx_to_qiskit(best_diagram)
    final = loss._compute_stats(best_circuit,hardware)
    print("our final is:", final)    

    if hardware is not None:
        best_circuit = hardware.make_compatible(best_circuit)
    print(swap_succes,swap_try)
    print(initial_cost, best_cost)
    return best_circuit, best_diagram, best_cost, history


## neighbour strategies
def _apply_rule(diagram, v, rule_name):
    try:
        if 'fuse' in rule_name:
            return rewrite.try_fuse(diagram, v)
        if 'strong_comp' in rule_name:
            return rewrite.try_strong_comp(diagram, v)
        rule_func = getattr(rewrite, f'try_{rule_name}')
        return rule_func(diagram, v)
    except Exception:
        return False
    
def get_neighbour_all_vertices(diagram, k=10):
    rule_weights = {
        'remove_id': 0.25,
        'fuse': 0.20,
        'strong_comp': 0.15,
        'pi_commute_Z': 0.08,
        'pi_commute_X': 0.05,
        'color_change': 0.02,
        'copy_X': 0.05,
        'copy_Z': 0.05,
        'lcomp': 0.10,    
        'pivot': 0.05}
    vertices = list(diagram.vertices())
    if not vertices:
        return False

    # sample up to k vertices to consider
    sample = vertices if len(vertices) <= k else random.sample(vertices, k)

    # stream-weighted pick among sampled vertices
    chosen = None
    total = 0.0
    for v in sample:
        for rule_name in rewrite.get_applicable_rules(diagram, v) or ():
            base = rule_name.split('_with_', 1)[0]
            w = rule_weights.get(base, 0.05)
            total += w
            if random.random() * total < w:
                chosen = (v, rule_name)

    if chosen is None:
        return False

    v, rule_name = chosen
    try:
        if 'fuse_with_' in rule_name:
            return rewrite.try_fuse(diagram, v) or False
        if 'strong_comp_with_' in rule_name:
            return rewrite.try_strong_comp(diagram, v) or False
        # avoid getattr overhead by using a dict mapping (next tip)
        rule_func = getattr(rewrite, f"try_{rule_name}")
        return rule_func(diagram, v) or False
    except Exception:
        return False

    

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
        
        # Shuffle a  pplicable rules
        random.shuffle(applicable)
        
        # Try each applicable rule
        for rule_name in applicable:
            #print("we try ",rule_name)
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
    rule_weights = {
        'remove_id':            0.25, 
        'fuse':                 0.25,  
        'strong_comp':          0.20,  
        'lcomp':                0.01,  
        'pivot':                0.01,  
        'pi_commute_Z':         0.02,
        'pi_commute_X':         0.02,
        'split_spider':         0.01,
        'insert_hadamard_pair': 0.02,
        'color_change':         0.01,
        'copy_X':               0.01,
        'copy_Z':               0.02,
    }
    
    vertices = list(diagram.vertices())
    if not vertices:
        return False

    random.shuffle(vertices)
    for v in vertices:
        # Build full rule list, weighted sample without replacement until one works
        rules = list(rule_weights.keys())
        weights = list(rule_weights.values())
        
        while rules:
            chosen = random.choices(rules, weights=weights, k=1)[0]
            idx = rules.index(chosen)
            rules.pop(idx)
            weights.pop(idx)
            result = _apply_rule(diagram, v, chosen)
            if result is not False and integration.can_convert_to_circuit(result):
                print(chosen)
                return result

    return False



def get_neighbor_high_degree(diagram, top_k=5):
    """
    Prioritise high-degree vertices — they contribute most to two-qubit gate count.
    Samples from the top_k highest-degree vertices, weighted by degree.
    Falls back to random if no rules apply.
    """
    rule_weights = {
        'remove_id':            0.25, 
        'fuse':                 0.25,  
        'strong_comp':          0.20,  
        'lcomp':                0.01,  
        'pivot':                0.01,  
        'pi_commute_Z':         0.02,
        'pi_commute_X':         0.02,
        'split_spider':         0.01,
        'insert_hadamard_pair': 0.02,
        'color_change':         0.01,
        'copy_X':               0.01,
        'copy_Z':               0.02,
    }
    
    vertices = list(diagram.vertices())
    if not vertices:
        return False

    # Rank by degree descending, take top_k
    vertices.sort(key=lambda v: diagram.vertex_degree(v), reverse=True)
    candidates = vertices[:top_k]

    # Weight candidates by degree so highest-degree is most likely chosen
    degrees = [diagram.vertex_degree(v) for v in candidates]
    total_degree = sum(degrees)
    if total_degree == 0:
        return get_neighbor_random_vertex_random_rule(diagram)  # fallback

    # Try candidates in degree-weighted order
    random.shuffle(candidates)  
    for v in candidates:
        applicable = rewrite.get_applicable_rules(diagram, v)
        if not applicable:
            continue

        # Weight applicable rules by rule_weights
        weighted = []
        for rule_name in applicable:
            base = rule_name.split('_with_', 1)[0]
            w = rule_weights.get(base, 0.05)
            weighted.append((w, rule_name))

        weighted.sort(reverse=True)  # try highest-weight rules first
        
        for w, rule_name in weighted:
            try:
                if 'fuse_with_' in rule_name:
                    result = rewrite.try_fuse(diagram, v)
                elif 'strong_comp_with_' in rule_name:
                    result = rewrite.try_strong_comp(diagram, v)
                else:
                    result = getattr(rewrite, f'try_{rule_name}')(diagram, v)

                if result is not False:
                    print(rule_name)
                    return result
            except Exception:
                continue

    # Nothing worked in top_k, fall back to random
    return get_neighbor_weighted_rules(diagram)