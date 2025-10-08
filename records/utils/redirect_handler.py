"""
Utility functions for handling redirect URLs after form submissions.
"""
from django.urls import reverse


def build_url_with_params(base_url, query_params):
    """
    Build a URL with query parameters.

    Args:
        base_url (str): The base URL path
        query_params (QueryDict): Django QueryDict with query parameters

    Returns:
        str: URL with query parameters appended if any exist
    """
    if query_params:
        return f"{base_url}?{query_params.urlencode()}"
    return base_url


def get_assignee_redirect_url(assignee_id, query_params):
    """
    Get redirect URL for assignee records list.

    Args:
        assignee_id (str): The assignee's primary key
        query_params (QueryDict): Query parameters to preserve

    Returns:
        str: Full URL to assignee's record list
    """
    # Remove assignee_id from query params to avoid duplication
    query_params = query_params.copy()
    query_params.pop('assignee_id', None)

    base_url = reverse('assignee_records', kwargs={'pk': assignee_id})
    return build_url_with_params(base_url, query_params)


def get_record_detail_redirect_url(record_pk, query_params):
    """
    Get redirect URL for record detail page.

    Args:
        record_pk (int): The record's primary key
        query_params (QueryDict): Query parameters to preserve

    Returns:
        str: Full URL to record detail page
    """
    base_url = reverse('record_detail', kwargs={'pk': record_pk})
    return build_url_with_params(base_url, query_params)
