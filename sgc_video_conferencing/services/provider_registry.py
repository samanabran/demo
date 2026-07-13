# -*- coding: utf-8 -*-
###############################################################################
#    Part of the SGC Odoo Suite <https://sgctech.ai>
#
#    SGC TECH AI
#    Copyright (C) 2026 SGC TECH AI (<https://sgctech.ai>)
#
#    This module and its source code are licensed under the Odoo Proprietary
#    License v1.0 (OPL-1). You may not redistribute or resell it. See
#    https://www.odoo.com/documentation/19.0/legal/licenses.html for terms.
###############################################################################

import logging

_logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Registry mapping provider codes to their service classes.
    
    To add a new provider:
        1. Create a new service class inheriting BaseVideoProvider
        2. Register it by adding to _providers dict
    """

    _providers = {}

    @classmethod
    def register(cls, provider_class):
        """
        Register a provider service class.
        
        Args:
            provider_class: A class inheriting from BaseVideoProvider
        """
        code = provider_class.provider_code
        cls._providers[code] = provider_class
        _logger.info("Registered video provider: %s (%s)", provider_class.provider_name, code)
        return provider_class

    @classmethod
    def get_service(cls, provider_code, env=None):
        """
        Get a service instance for the given provider code.
        
        Args:
            provider_code (str): The provider code (e.g., 'google_meet', 'zoom')
            env: Odoo environment (optional)
            
        Returns:
            BaseVideoProvider instance, or None if not found
        """
        provider_class = cls._providers.get(provider_code)
        if provider_class:
            return provider_class(env) if env else provider_class
        _logger.warning("No provider registered for code: %s", provider_code)
        return None

    @classmethod
    def get_all_services(cls, env=None):
        """
        Get instances of all registered providers.
        
        Returns:
            List of BaseVideoProvider instances
        """
        if env:
            return [cls(env) for cls in cls._providers.values()]
        return list(cls._providers.values())

    @classmethod
    def get_registered_codes(cls):
        """Get list of all registered provider codes."""
        return list(cls._providers.keys())
