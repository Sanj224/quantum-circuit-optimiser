# Rewrite rules borrowed from PyZX and a function to return all the possible rewrite rules on each vertex
import math

from pyzx.rewrite_rules.fuse_rule import check_fuse, fuse

def try_spider_fuse(g, v, w):
    """
    Attempt to fuse vertices v and w in ZX-graph g.
    Returns True if fused, False if not applicable.
    """
    if not check_fuse(g, v, w):
        return False 
    return fuse(g, v, w)
