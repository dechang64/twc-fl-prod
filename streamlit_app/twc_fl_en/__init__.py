"""
TWC-FL Platform - Three-Way Catalyst Federated Learning Collaboration Platform

Python core package. Modules:
    - data_vault: Formula data management (import/anonymization/quality report/similarity search)
    - knowledge_hub: TWC domain knowledge base (FAQ query/literature recommendation)
    - bayesian_optimizer: Bayesian formula optimization (surrogate model/candidate recommendation)
    - fl_engine: Federated learning engine (node management/FedAvg aggregation/model distribution)
    - audit_chain: Blockchain audit chain (data attestation/chain verification)
"""

from .data_vault import DataVault, FormulaRecord, DataQualityReport
from .knowledge_hub import KnowledgeHub, FAQEntry, LiteratureRef
from .bayesian_optimizer import BayesianOptimizer, CandidateFormula, OptimizationResult
from .fl_engine import FLEngine, FLClient, FLConfig, AggregationResult
from .audit_chain import AuditChain, AuditEntry

__version__ = "1.1.0"
__all__ = [
    "DataVault", "FormulaRecord", "DataQualityReport",
    "KnowledgeHub", "FAQEntry", "LiteratureRef",
    "BayesianOptimizer", "CandidateFormula", "OptimizationResult",
    "FLEngine", "FLClient", "FLConfig", "AggregationResult",
    "AuditChain", "AuditEntry",
]
