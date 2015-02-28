from __future__ import unicode_literals

from django.template.loader import get_template
from django.template.loader_tags import ExtendsNode


def template_extends(template_name, expected_parent_name):
    """Returns whether or not a template extends the specified parent"""
    template = get_template(template_name)
    template = getattr(template, 'template', template)
    if template.nodelist and isinstance(template.nodelist[0], ExtendsNode):
        node = template.nodelist[0]
        parent_name = node.parent_name.resolve({})
        if parent_name == expected_parent_name:
            return True
        return template_extends(parent_name, expected_parent_name)
    return False
