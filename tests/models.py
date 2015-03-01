from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import force_text
from django.utils.six import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from dynamic_choices.db.models import (
    DynamicChoicesForeignKey, DynamicChoicesManyToManyField,
    DynamicChoicesOneToOneField,
)

ALIGNMENT_EVIL = 0
ALIGNMENT_GOOD = 1
ALIGNMENT_NEUTRAL = 2

ALIGNMENT_CHOICES = [
    (ALIGNMENT_EVIL, _('Evil')),
    (ALIGNMENT_GOOD, _('Good')),
    (ALIGNMENT_NEUTRAL, _('Neutral')),
]


def same_alignment(queryset, alignment=None):
    return queryset.filter(alignment=alignment)


def alignment_display(alignment):
    for align, label in ALIGNMENT_CHOICES:
        if alignment == align:
            return force_text(label)


@python_2_unicode_compatible
class Master(models.Model):
    alignment = models.SmallIntegerField(choices=ALIGNMENT_CHOICES)

    class Meta:
        app_label = 'dynamic_choices'

    def __str__(self):
        return "%s master (%s)" % (self.get_alignment_display(), self.pk)


@python_2_unicode_compatible
class Puppet(models.Model):
    alignment = models.SmallIntegerField(choices=ALIGNMENT_CHOICES)
    master = DynamicChoicesForeignKey(Master, choices=same_alignment)
    secret_lover = DynamicChoicesOneToOneField(
        'self', choices='choices_for_secret_lover', related_name='secretly_loves_me', blank=True, null=True
    )
    friends = DynamicChoicesManyToManyField('self', choices='choices_for_friends', blank=True, null=True)
    enemies = DynamicChoicesManyToManyField('self', through='Enemy', symmetrical=False, blank=True, null=True)

    class Meta:
        app_label = 'dynamic_choices'

    def __str__(self):
        return "%s puppet (%s)" % (self.get_alignment_display(), self.pk)

    def choices_for_friends(self, queryset, id=None, alignment=None):
        """Make sure our friends share our alignment or are neutral"""
        same_alignment = queryset.filter(alignment=alignment).exclude(id=id)
        if alignment in (None, ALIGNMENT_NEUTRAL):
            return same_alignment
        return (
            (alignment_display(alignment), same_alignment),
            ('Neutral', queryset.filter(alignment=ALIGNMENT_NEUTRAL))
        )

    def choices_for_secret_lover(self, queryset):
        if self.pk:
            try:
                secretly_loves_me_qs = queryset.filter(secret_lover=self.pk)
                secretly_loves_me_qs.get()
            except (Puppet.DoesNotExist, Puppet.MultipleObjectsReturned):
                pass
            else:
                return secretly_loves_me_qs
        return queryset


class Enemy(models.Model):
    puppet = DynamicChoicesForeignKey(Puppet)
    enemy = DynamicChoicesForeignKey(Puppet, choices='choices_for_enemy', related_name='+')
    because_of = DynamicChoicesForeignKey(Master, choices='choices_for_because_of', related_name='becauses_of')
    since = models.DateField()

    class Meta:
        app_label = 'dynamic_choices'

    def choices_for_because_of(self, queryset, enemy__alignment=None):
        return queryset.filter(alignment=enemy__alignment)

    def choices_for_enemy(self, queryset, puppet__alignment=None):
        if puppet__alignment is None:
            return queryset.none()
        return [
            (label, queryset.filter(alignment=alignment))
            for alignment, label in ALIGNMENT_CHOICES if alignment != puppet__alignment
        ]
