
"""
This file contains the main logic for the simulated annealing algorithm
Including how a new diagram is derived
"""
from . import rewrite
from .. import integration
import random
import math
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
    Args: 
        circuit: quantum circuit to be optimised
        cost_function: cost function used to guide optimisation
        initial_temp: starting temperature, defaulted to 100
        cooling_rate: cooling rate of the temperature, defaulated to 0.95
        max_terations: the number of iterations before the algorithm terminates
        min_temp: the lowest temperature the algorithm will get to
        max_no_improvements: the number of iterations allowed without an improvement
        hardware: the hardware map the circuit must be routed to
    """
    #Compute the initial stats like the diagram and the cost
    diagram = integration.qiskit_to_pyzx(circuit)
    cost_function = loss.cost_function_from_circuit(cost_function, None, hardware)
    current_diagram = diagram
    current_cost = cost_function(diagram)  
    best_diagram = diagram.copy()
    best_cost = current_cost

    temperature = initial_temp
    history = []
    
    best_no_improvement_count = 0
    no_improvement_count = 0
    accepted_moves = 0
    rejected_moves = 0
    failed_conversions = 0
    iteration = 0
    while temperature > min_temp and iteration < max_iterations:
        # Generate neighbor and evaluate it
        new_diagram = get_neighbor(current_diagram)    
        if new_diagram is False:  
            #If the new diagram is invalid, skip this iteration
            continue
        if hardware is not None:
            #scramble the qubits to try find a better arrangement
            new_circuit = integration.pyzx_to_qiskit(new_diagram)
            candidate = hardware.try_qubit_permutation(new_circuit)
            if candidate is not None:
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

    if hardware is not None:
        best_circuit = hardware.make_compatible(best_circuit)
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
    


def get_neighbor_weighted_rules(diagram):
    """
    This function generates a neighbour by prioritising the rules most likely to offer an improvement
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
        #'insert_hadamard_pair': 0.02,
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
            #try each rule until we find one that works
            chosen = random.choices(rules, weights=weights, k=1)[0]
            idx = rules.index(chosen)
            rules.pop(idx)
            weights.pop(idx)
            result = _apply_rule(diagram, v, chosen)
            if result is not False and integration.can_convert_to_circuit(result):
                return result
    #If no rule is found, return False
    return False


