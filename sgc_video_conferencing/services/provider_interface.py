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

from abc import ABC, abstractmethod
import logging

_logger = logging.getLogger(__name__)


class BaseVideoProvider(ABC):
    """
    Abstract base class for all video conferencing providers.
    
    All provider implementations must inherit from this class and implement
    all abstract methods. This ensures a consistent interface across all
    providers.
    """

    def __init__(self, env):
        self.env = env

    # -----------------------------------------------------------------
    # Meeting lifecycle
    # -----------------------------------------------------------------
    @abstractmethod
    def create_meeting(self, meeting):
        """
        Create a meeting on the provider.
        
        Returns dict with:
            - join_url (str): URL for participants to join
            - start_url (str): URL for host to start (if different)
            - provider_meeting_id (str): Meeting ID from provider
            - password (str, optional): Meeting password
        """
        raise NotImplementedError

    @abstractmethod
    def update_meeting(self, meeting):
        """
        Update an existing meeting on the provider.
        
        Returns True on success, raises on failure.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_meeting(self, meeting):
        """
        Delete/cancel a meeting on the provider.
        
        Returns True on success, raises on failure.
        """
        raise NotImplementedError

    @abstractmethod
    def get_meeting(self, meeting):
        """
        Get meeting details from the provider.
        
        Returns dict with meeting details or None if not found.
        """
        raise NotImplementedError

    # -----------------------------------------------------------------
    # Meeting URLs
    # -----------------------------------------------------------------
    @abstractmethod
    def get_join_url(self, meeting):
        """
        Get the join URL for a meeting.
        
        Returns the URL as a string.
        """
        raise NotImplementedError

    def get_start_url(self, meeting):
        """
        Get the start URL for a meeting (host-specific).
        
        Default returns the join_url if no separate start URL exists.
        """
        return meeting.join_url

    # -----------------------------------------------------------------
    # OAuth / Auth
    # -----------------------------------------------------------------
    def get_oauth_url(self, account):
        """
        Get the OAuth authorization URL for this provider.
        
        Returns the URL as a string, or None if OAuth is not supported.
        """
        return None

    def exchange_oauth_code(self, account, code):
        """
        Exchange an OAuth authorization code for tokens.
        
        Returns dict with access_token, refresh_token, expires_at.
        """
        raise NotImplementedError("OAuth not implemented for this provider")

    def refresh_token(self, account):
        """
        Refresh the OAuth access token.
        
        Returns True on success, False on failure.
        """
        raise NotImplementedError("Token refresh not implemented for this provider")

    # -----------------------------------------------------------------
    # Connection verification
    # -----------------------------------------------------------------
    @abstractmethod
    def verify_connection(self, account):
        """
        Verify that the provider connection is working.
        
        Returns True if connection is valid, False otherwise.
        """
        raise NotImplementedError

    # -----------------------------------------------------------------
    # Recordings
    # -----------------------------------------------------------------
    def get_recordings(self, meeting):
        """
        Get recordings for a completed meeting.
        
        Returns list of dicts with recording details.
        """
        return []

    # -----------------------------------------------------------------
    # Provider metadata
    # -----------------------------------------------------------------
    @property
    @abstractmethod
    def provider_code(self):
        """
        Unique code for this provider (matches video.provider.code).
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def provider_name(self):
        """
        Human-readable name for this provider.
        """
        raise NotImplementedError

    @property
    def supports_oauth(self):
        """Whether this provider supports OAuth 2.0 authentication."""
        return False

    @property
    def supports_instant_meetings(self):
        """Whether this provider supports instant meetings."""
        return True

    @property
    def supports_recordings(self):
        """Whether this provider supports recording retrieval."""
        return False

    @property
    def supports_recurring_meetings(self):
        """Whether this provider supports recurring meetings."""
        return False
