# Rewrite rules borrowed from PyZX with wrappers that return new graph objects

import pyzx as zx
from pyzx import basicrules as br
from pyzx import rules

from pyzx.graph.base import BaseGraph, VT, ET
from typing import Union, List, Tuple, Optional
from .. import integration

def try_color_change(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to color change vertex v. Returns new graph if successful, False otherwise."""
    try:
        if not br.check_color_change(g, v):
            return False
        g_new = g.copy()
        success = br.color_change(g_new, v)
        if not success:
            return False
        if not integration.can_convert_to_circuit(g_new):
            return False
        return g_new
    except Exception:
        return False


def try_copy_X(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to apply copy rule for X spider. Returns new graph if successful, False otherwise."""
    try:
        if not br.check_copy_X(g, v):
            return False
        g_new = g.copy()
        success = br.copy_X(g_new, v)
        if not success:
            return False
        if not integration.can_convert_to_circuit(g_new):
            return False
        return g_new
    except Exception:
        return False


def try_copy_Z(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to apply copy rule for Z spider. Returns new graph if successful, False otherwise."""
    try:
        if not br.check_copy_Z(g, v):
            return False
        g_new = g.copy()
        success = br.copy_Z(g_new, v)  # FIXED: was pi_commute_Z
        if not success:
            return False
        if not integration.can_convert_to_circuit(g_new):
            return False
        return g_new
    except Exception:
        return False


def try_pi_commute_Z(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to apply pi-commutation for Z spider. Returns new graph if successful, False otherwise."""
    try:
        if not br.check_pi_commute_Z(g, v):
            return False
        g_new = g.copy()
        success = br.pi_commute_Z(g_new, v)
        if not success:
            return False
        if not integration.can_convert_to_circuit(g_new):
            return False
        return g_new
    except Exception:
        return False


def try_pi_commute_X(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to apply pi-commutation for X spider. Returns new graph if successful, False otherwise."""
    try:
        # Don't use check_pi_commute_X - it modifies the graph!
        if g.type(v) != zx.VertexType.X:
            return False
        g_new = g.copy()
        success = br.pi_commute_X(g_new, v)
        if not success:
            return False
        if not integration.can_convert_to_circuit(g_new):
            return False
        return g_new
    except Exception:
        return False


def try_remove_id(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """Try to remove identity spider. Returns new graph if successful, False otherwise."""
    try:
        if not br.check_remove_id(g, v):
            return False
        g_new = g.copy()
        success = br.remove_id(g_new, v)
        if not success:
            return False
        if not integration.can_convert_to_circuit(g_new):
            return False
        return g_new
    except Exception:
        return False


def try_strong_comp(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """
    Try to apply strong complementarity with v and one of its neighbors.
    Returns new graph if successful, False otherwise.
    """
    try:
        for w in g.neighbors(v):
            if br.check_strong_comp(g, v, w):
                g_new = g.copy()
                br.strong_comp(g_new, v, w)
                if not integration.can_convert_to_circuit(g_new):
                    continue
                return g_new
        return False
    except Exception:
        return False


def try_fuse(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    """
    Try to fuse v with one of its neighbors.
    Returns new graph if successful, False otherwise.
    """
    try:
        for w in g.neighbors(v):
            if br.check_fuse(g, v, w):
                g_new = g.copy()
                br.fuse(g_new, v, w)
                if not integration.can_convert_to_circuit(g_new):
                    continue
                return g_new
        return False
    except Exception:
        return False

def try_lcomp(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        g_new = g.copy()
        matches = rules.match_lcomp_parallel(g_new)
        vertices = rules.lcomp(g_new,matches)  # takes a list
        if vertices is None:
            return False
        if not integration.can_convert_to_circuit(g_new):
            print("got here")
            return False
        return g_new
    except Exception:
        return False


def try_pivot(g: BaseGraph[VT, ET], v: VT) -> Union[BaseGraph[VT, ET], bool]:
    try:
        for w in g.neighbors(v):
            g_new = g.copy()
            matches = rules.match_pivot_parallel(g_new)
            result = rules.pivot(g_new,matches)  
            if result is None:
                continue
            if not integration.can_convert_to_circuit(g_new):
                continue
            return g_new
        return False
    except Exception:
        return False


def get_applicable_rules(g: BaseGraph[VT, ET], v: VT) -> List[str]:
    """
    Get list of all rules applicable to vertex v.
    Actually tests each rule on a copy to ensure it will work.
    """
    applicable = []
    single_rules = [
        ('color_change', try_color_change),
        ('copy_X', try_copy_X),
        ('copy_Z', try_copy_Z),
        ('pi_commute_Z', try_pi_commute_Z),
        ('pi_commute_X', try_pi_commute_X),
        ('remove_id', try_remove_id),
        ('fuse', try_fuse),
        ('strong_comp', try_strong_comp),
        ('lcomp', try_lcomp),
        ('pivot', try_pivot)]
    
    for rule_name, check_func in single_rules:
        try:
            result = check_func(g, v) 
            if result is not False:  
                applicable.append(rule_name)
        except Exception as e:
            continue
    
    return applicable

