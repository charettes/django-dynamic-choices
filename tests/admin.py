from django.contrib import admin
from dynamic_choices.admin import DynamicAdmin

from .forms import UserDefinedForm
from .models import Master, Puppet


class EnemyInline(admin.TabularInline):
    model = Puppet.enemies.through
    fk_name = 'puppet'
    form = UserDefinedForm


class PuppetAdmin(DynamicAdmin):
    inlines = (EnemyInline,)
    form = UserDefinedForm


class MasterAdmin(DynamicAdmin):
    pass


site = admin.AdminSite('admin')
site.register(Puppet, PuppetAdmin)
site.register(Master, MasterAdmin)
