"""
Concrete aggregation strategies.

Each module provides a class that satisfies
:class:`~griphogram.types.AggregationStrategy` via structural subtyping.
"""

from griphogram.strategy.allreduce import AllReduceStrategy
from griphogram.strategy.gossip import GossipStrategy
from griphogram.strategy.parameter_server import ParameterServerStrategy

__all__ = ["AllReduceStrategy", "GossipStrategy", "ParameterServerStrategy"]
