from django import template
import ast
from records.models import Assignee

register = template.Library()

@register.filter(name='clean_summary')
def clean_summary(value):
    """
    Cleans a string by removing leading/trailing brackets and quotes.
    Handles cases like "['some text']" or "[some text]".
    """
    if not isinstance(value, str):
        return value

    # First, try a robust literal evaluation to handle Python list representations
    if value.startswith('[') and value.endswith(']'):
        try:
            evaluated_list = ast.literal_eval(value)
            if isinstance(evaluated_list, list) and len(evaluated_list) == 1:
                return str(evaluated_list[0])
            elif isinstance(evaluated_list, list):
                # Joins multiple list items with a space
                return ' '.join(str(item) for item in evaluated_list)
        except (ValueError, SyntaxError):
            # If literal evaluation fails, fall back to simple stripping
            pass

    # Fallback to a simple strip for any remaining brackets/quotes
    cleaned_value = value.strip('[]')
    cleaned_value = cleaned_value.strip("'\"")

    return cleaned_value


@register.simple_tag
def get_active_assignees():
    """
    Returns all active assignees ordered by IDS range.
    """
    return Assignee.objects.filter(is_active=True).order_by('ids_from')