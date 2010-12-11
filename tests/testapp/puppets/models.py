from django.db import models
from django.db.models.query import EmptyQuerySet

from dynamic_choices.db.models import DynamicChoicesForeignKey, DynamicChoicesManyToManyField

ALIGNMENT_EVIL = 0
ALIGNMENT_GOOD = 1
ALIGNMENT_NEUTRAL = 2

ALIGNMENTS = (
    (ALIGNMENT_EVIL, 'Evil'),
    (ALIGNMENT_GOOD, 'Good'),
    (ALIGNMENT_NEUTRAL, 'Neutral'),
)

def same_alignment(queryset, alignment=None):
    return queryset.filter(alignment=alignment)

class Master(models.Model):
    
    alignment = models.SmallIntegerField(choices=ALIGNMENTS)
    
    def __unicode__(self):
        return u"%s master (%d)" % (self.get_alignment_display(), self.pk)

class Puppet(models.Model):
    
    alignment = models.SmallIntegerField(choices=ALIGNMENTS)
    master = DynamicChoicesForeignKey(Master, choices=same_alignment)
    friends = DynamicChoicesManyToManyField('self', choices='choices_for_friends', blank=True, null=True)
    enemies = DynamicChoicesManyToManyField('self', through='Enemy', symmetrical=False, blank=True, null=True)
    
    def choices_for_friends(self, queryset, id=None, alignment=None):
        """
            Make sure our friends share our alignment
        """
        return same_alignment(queryset, alignment=alignment).exclude(id=id)
    
    def __unicode__(self):
        return u"%s puppet (%d)" % (self.get_alignment_display(), self.id)

class Enemy(models.Model):
    
    puppet = DynamicChoicesForeignKey(Puppet)
    enemy = DynamicChoicesForeignKey(Puppet, choices='choices_for_enemy', related_name='bob')
    because_of = DynamicChoicesForeignKey(Master, choices='achoices_for_because_of', related_name='becauses_of')
    since = models.DateField()
    
    def achoices_for_because_of(self, queryset, enemy__alignment=None):
        return queryset.filter(alignment=enemy__alignment)
    
    def choices_for_enemy(self, queryset, puppet__alignment=None):
        """
            Filter our enemies
        """
        if puppet__alignment is None:
            return EmptyQuerySet()
        else:
            return queryset.exclude(alignment=puppet__alignment)
    
        