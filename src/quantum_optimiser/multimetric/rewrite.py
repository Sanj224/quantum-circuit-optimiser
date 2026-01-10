# Rewrite rules borrowed from PyZX with wrappers that return new graph objects

import pyzx as zx
from pyzx import basicrules as br
from pyzx.graph.base import BaseGraph, VT, ET
from typing import Union, List, Tuple, Optional


def try_color_change(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to color change vertex v. Returns new graph if successful, False otherwise."""
    if not br.check_color_change(g, v):
        return False
    g_new = g.copy()
    br.color_change(g_new, v)
    return g_new


def try_copy_X(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to apply copy rule for X spider. Returns new graph if successful, False otherwise."""
    if not br.check_copy_X(g, v):
        return False
    g_new = g.copy()
    br.copy_X(g_new, v)
    return g_new


def try_copy_Z(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to apply copy rule for Z spider. Returns new graph if successful, False otherwise."""
    if not br.check_copy_Z(g, v):
        return False
    g_new = g.copy()
    br.copy_Z(g_new, v)
    return g_new


def try_pi_commute_Z(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to apply pi-commutation for Z spider. Returns new graph if successful, False otherwise."""
    if not br.check_pi_commute_Z(g, v):
        return False
    g_new = g.copy()
    br.pi_commute_Z(g_new, v)
    return g_new


def try_pi_commute_X(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to apply pi-commutation for X spider. Returns new graph if successful, False otherwise."""
    if not br.check_pi_commute_X(g, v):
        return False
    g_new = g.copy()
    br.pi_commute_X(g_new, v)
    return g_new


def try_remove_id(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to remove identity spider. Returns new graph if successful, False otherwise."""
    if not br.check_remove_id(g, v):
        return False
    g_new = g.copy()
    br.remove_id(g_new, v)
    return g_new


def try_strong_comp(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """
    Try to apply strong complementarity with v and one of its neighbors.
    Returns new graph if successful, False otherwise.
    """
    for w in g.neighbors(v):
        if br.check_strong_comp(g, v, w):
            g_new = g.copy()
            br.strong_comp(g_new, v, w)
            return g_new
    return False


def try_fuse(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """
    Try to fuse v with one of its neighbors.
    Returns new graph if successful, False otherwise.
    """
    for w in g.neighbors(v):
        if br.check_fuse(g, v, w):
            g_new = g.copy()
            br.fuse(g_new, v, w)
            return g_new
    return False


def get_applicable_rules(g: BaseGraph[VT, ET], v: VT) -> List[str]:
    """
    Get list of all rules applicable to vertex v.
    Returns list of rule names without applying them or copying the graph.
    """
    applicable = []
    
    if br.check_color_change(g, v):
        applicable.append('color_change')
    if br.check_copy_X(g, v):
        applicable.append('copy_X')
    if br.check_copy_Z(g, v):
        applicable.append('copy_Z')
    if br.check_pi_commute_Z(g, v):
        applicable.append('pi_commute_Z')
    if br.check_pi_commute_X(g, v):
        applicable.append('pi_commute_X')
    if br.check_remove_id(g, v):
        applicable.append('remove_id')
    
    # Check pair-wise rules
    for w in g.neighbors(v):
        if br.check_strong_comp(g, v, w):
            applicable.append(f'strong_comp_with_{w}')
        if br.check_fuse(g, v, w):
            applicable.append(f'fuse_with_{w}')
    
    return applicable


def apply_all_rules_at_vertex(g: BaseGraph[VT, ET], v: VT) -> List[Tuple[str, BaseGraph[VT, ET]]]:
    """
    Apply all applicable rules at vertex v.
    Returns list of (rule_name, new_graph) tuples.
    """
    results = []
    
    # Single vertex rules
    single_rules = [
        ('color_change', try_color_change),
        ('copy_X', try_copy_X),
        ('copy_Z', try_copy_Z),
        ('pi_commute_Z', try_pi_commute_Z),
        ('pi_commute_X', try_pi_commute_X),
        ('remove_id', try_remove_id),
    ]
    
    for rule_name, rule_func in single_rules:
        result = rule_func(g, v)
        if result is not False:
            results.append((rule_name, result))
    
    # Pair-wise rules
    for w in g.neighbors(v):
        if br.check_strong_comp(g, v, w):
            g_new = g.copy()
            br.strong_comp(g_new, v, w)
            results.append((f'strong_comp_with_{w}', g_new))
        
        if br.check_fuse(g, v, w):
            g_new = g.copy()
            br.fuse(g_new, v, w)
            results.append((f'fuse_with_{w}', g_new))
    
    return results