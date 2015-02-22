from __future__ import unicode_literals

import django

if django.VERSION >= (1, 6):
    def get_model_name(opts):
        return opts.model_name
else:
    def get_model_name(opts):
        return opts.module_name
