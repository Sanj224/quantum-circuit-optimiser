# Rewrite rules borrowed from PyZX with wrappers that return new graph objects

import pyzx as zx
from pyzx import basicrules as br
from pyzx import rules
import random
from pyzx.graph.base import BaseGraph, VT, ET
from typing import Union, List, Tuple, Optional
from .. import integration
def try_color_change(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        if not br.check_color_change(g, v):
            return False
        g_new = g.copy()
        if not br.color_change(g_new, v):
            return False
        return g_new
    except Exception:
        return False


def try_copy_X(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        if not br.check_copy_X(g, v):
            return False
        g_new = g.copy()
        if not br.copy_X(g_new, v):
            return False
        return g_new
    except Exception:
        return False


def try_copy_Z(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        if not br.check_copy_Z(g, v):
            return False
        g_new = g.copy()
        if not br.copy_Z(g_new, v):
            return False
        return g_new
    except Exception:
        return False


def try_pi_commute_Z(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        if not br.check_pi_commute_Z(g, v):
            return False
        g_new = g.copy()
        if not br.pi_commute_Z(g_new, v):
            return False
        return g_new
    except Exception:
        return False


def try_pi_commute_X(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        if g.type(v) != zx.VertexType.X:
            return False
        g_new = g.copy()
        if not br.pi_commute_X(g_new, v):
            return False
        return g_new
    except Exception:
        return False


def try_remove_id(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        if not br.check_remove_id(g, v):
            return False
        g_new = g.copy()
        if not br.remove_id(g_new, v):
            return False
        return g_new
    except Exception:
        return False


def try_strong_comp(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        for w in g.neighbors(v):
            if br.check_strong_comp(g, v, w):
                g_new = g.copy()
                zx.simplify.to_graph_like(g_new)
                br.strong_comp(g_new, v, w)
                return g_new
        return False
    except Exception:
        return False


def try_fuse(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        for w in g.neighbors(v):
            if br.check_fuse(g, v, w):
                g_new = g.copy()
                br.fuse(g_new, v, w)
                return g_new
        return False
    except Exception:
        return False


def try_lcomp(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        g_new = g.copy()
        zx.simplify.to_graph_like(g_new)
        matches = rules.match_lcomp_parallel(g_new)
        if not matches:
            return False
        chosen = [random.choice(matches)]
        rules.lcomp(g_new, chosen)
        return g_new
    except Exception:
        return False


def try_pivot(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        g_new = g.copy()
        zx.simplify.to_graph_like(g_new)
        matches = rules.match_pivot_parallel(g_new)
        if not matches:
            return False
        chosen = [random.choice(matches)]
        rules.pivot(g_new, chosen)
        return g_new
    except Exception:
        return False

def try_split_spider(g, v):
    try:
        neighbors = list(g.neighbors(v))
        if len(neighbors) < 2:
            return False
        g_new = g.copy()
        mid = len(neighbors) // 2
        new_v = g_new.add_vertex(g_new.type(v), g_new.qubit(v), g_new.row(v) + 0.5)
        g_new.set_phase(new_v, 0)
        for w in neighbors[mid:]:
            g_new.remove_edge(g_new.edge(v, w))
            g_new.add_edge((new_v, w))
        g_new.add_edge((v, new_v))
        return g_new
    except Exception:
        return False


def try_insert_hadamard_pair(g, v):
    try:
        neighbors = list(g.neighbors(v))
        if not neighbors:
            return False
        w = random.choice(neighbors)
        g_new = g.copy()
        e = g_new.edge(v, w)
        etype = g_new.edge_type(e)
        g_new.remove_edge(e)
        h1 = g_new.add_vertex(zx.VertexType.H_BOX, g_new.qubit(v), g_new.row(v) + 0.3)
        h2 = g_new.add_vertex(zx.VertexType.H_BOX, g_new.qubit(v), g_new.row(v) + 0.6)
        g_new.add_edge((v, h1), etype)
        g_new.add_edge((h1, h2))
        g_new.add_edge((h2, w))
        return g_new
    except Exception:
        return False


def get_applicable_rules(g, v):
    applicable = []
    
    candidates = [
        ('remove_id',            try_remove_id),
        ('color_change',         try_color_change),
        ('copy_X',               try_copy_X),
        ('copy_Z',               try_copy_Z),
        ('pi_commute_Z',         try_pi_commute_Z),
        ('pi_commute_X',         try_pi_commute_X),
        ('fuse',                 try_fuse),
        ('strong_comp',          try_strong_comp),
        ('lcomp',                try_lcomp),
        ('pivot',                try_pivot),
        ('split_spider',         try_split_spider),
        ('insert_hadamard_pair', try_insert_hadamard_pair),
    ]
    
    for rule_name, fn in candidates:
        try:
            result = fn(g, v)
            if result is not False and integration.can_convert_to_circuit(result):
                applicable.append(rule_name)
        except Exception:
            continue
    
    return applicable
