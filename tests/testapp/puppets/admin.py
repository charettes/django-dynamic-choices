
from django.contrib import admin
from dynamic_choices.admin import DynamicAdmin

from models import Puppet, Master

class EnemyInline(admin.TabularInline):

    model = Puppet.enemies.through #@UndefinedVariable
    fk_name = 'puppet'

class PuppetAdmin(DynamicAdmin):
    
    inlines = (EnemyInline,)
    
#    filter_horizontal = ('friends',)

class MasterAdmin(DynamicAdmin):
    pass

admin.site.register(Puppet, PuppetAdmin)
admin.site.register(Master, MasterAdmin)
