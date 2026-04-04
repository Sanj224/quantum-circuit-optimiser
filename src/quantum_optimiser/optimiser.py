from multiprocessing import Pool
import os
import numpy as np
from quantum_optimiser.hardware_aware import hardwares
from quantum_optimiser.multimetric import loss, simulated_annealing
from quantum_optimiser import integration
from qiskit.circuit.random import random_circuit
import random
from qiskit import QuantumCircuit

FUNCTIONS = {
    "naive":        loss.naive_loss,
    "informed":     loss.informed_loss,
    "log_weighted": loss.log_weighted_loss,
    "quadratic":    loss.quadratic_loss_circuit
}

def get_metrics(circuit, hardware=None):
    s = loss._compute_stats(circuit,hardware)
    return {
        "qubits":    s['q'],
        "two_qubit": s['g2'],
        "gates":     s['g'],
        "depth":     s['d'],
        "t":         s['t'],
    }

def evaluate_once(args):
    circuit, hardware = args
    round_trip_circuit = integration.pyzx_to_qiskit(integration.qiskit_to_pyzx(circuit))
    round_trip_circuit=hardware.make_compatible(round_trip_circuit)
    results = {}
    for name, loss_fn in FUNCTIONS.items():
        before_L = loss_fn(round_trip_circuit)  
        before_m = get_metrics(round_trip_circuit)
        #print(before_m)

        optimised_circuit, _, optimised_cost, _ = simulated_annealing.simulated_annealing_zx(
            circuit=circuit,  
            cost_function=loss_fn,
            get_neighbor=simulated_annealing.get_neighbor_weighted_rules,
            initial_temp=100.0,
            cooling_rate=0.95,
            max_iterations=500,
            max_no_improvement=50,
            hardware=hardware
        )
        after_m = get_metrics(optimised_circuit)
        dL = before_L - optimised_cost
        dm = {k: before_m[k] - after_m[k] for k in before_m}
        results[name] = (dL, dm)
    
    return results

def random_circuit_generator(max_qubits, max_depth):
    one_qubit_gates = ["h", "s", "sdg", "t", "tdg", "x", "z"]
    two_qubit_gates = ["cx", "cz"]

    qubits = random.randint(2, max_qubits)
    depth = random.randint(2, max_depth)
    qc = QuantumCircuit(qubits)

    for i in range(depth):
        if random.random() < 0.6:
            q = random.randrange(qubits)
            gate = random.choice(one_qubit_gates)
            getattr(qc, gate)(q)
        else:
            q1, q2 = random.sample(range(qubits), 2)
            gate = random.choice(two_qubit_gates)
            getattr(qc, gate)(q1, q2)

    return qc


def evaluate(qubits,n_circuits=10, depth=100, hardware=None):


    circuits = [random_circuit_generator(qubits, depth) for _ in range(n_circuits)]
    args     = [(qc, hardware) for qc in circuits]

    with Pool(processes=os.cpu_count()) as pool:
        all_results = pool.map(evaluate_once, args)

    cost_deltas   = {name: [] for name in FUNCTIONS}
    metric_deltas = {name: [] for name in FUNCTIONS}

    for circuit_result in all_results:
        for name, (dL, dm) in circuit_result.items():
            cost_deltas[name].append(dL)
            metric_deltas[name].append(dm)

    print(f"\nBenchmark over {n_circuits} circuits | qubits≤{qubits} depth≤{depth}\n")
    for name in FUNCTIONS:
        avg_dL      = float(np.mean(cost_deltas[name]))
        avg_metrics = {
            k: float(np.mean([m[k] for m in metric_deltas[name]]))
            for k in metric_deltas[name][0]
        }
        print(f"{name}")
        print(f"  Avg cost decrease: {avg_dL:.4f}")
        for k, v in avg_metrics.items():
            print(f"  Avg {k} decrease: {v:.4f}")
        print()


if __name__ == "__main__":
    evaluate()