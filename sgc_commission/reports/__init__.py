# Commission Reports Module - Python-based generators
# Import order optimized to prevent circular dependencies

try:
    from . import commission_python_generator
    from . import commission_report  # Keep legacy for backward compatibility
    from . import commission_partner_statement_report  # Keep legacy AbstractModel
except ImportError as e:
    import logging
    _logger = logging.getLogger(__name__)
    _logger.warning("Commission report import failed: %s", str(e))
    # Continue loading without commission_report if there are issues