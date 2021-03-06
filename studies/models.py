import uuid

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

from accounts.models import DemographicData, Organization, User
from guardian.shortcuts import assign_perm
from project.fields.datetime_aware_jsonfield import DateTimeAwareJSONField
from transitions.extensions import GraphMachine as Machine

from . import workflow


class Study(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4)
    name = models.CharField(max_length=255, blank=False, null=False)
    short_description = models.TextField()
    long_description = models.TextField()
    criteria = models.TextField()
    duration = models.TextField()
    contact_info = models.TextField()
    image = models.ImageField(null=True)
    organization = models.ForeignKey(Organization, on_delete=models.DO_NOTHING, related_name='studies', related_query_name='study')
    blocks = DateTimeAwareJSONField(default=dict)
    state = models.CharField(choices=workflow.STATE_CHOICES, max_length=25, default=workflow.STATE_CHOICES[0][0])
    public = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super(Study, self).__init__(*args, **kwargs)
        self.machine = Machine(
            self,
            states=workflow.states,
            transitions=workflow.transitions,
            initial=self.state,
            send_event=True,
            before_state_change='check_permission',
            after_state_change='_finalize_state_change'
        )

    def __str__(self):
        return f'<Study: {self.name}>'

    class Meta:
        permissions = (
            ('can_view', 'View Study'),
            ('can_edit', 'Edit Study'),
            ('can_submit', 'Submit Study'),
            ('can_respond', 'Can Respond'),
        )

    # WORKFLOW CALLBACKS
    def check_permission(self, ev):
        user = ev.kwargs.get('user')
        if user.is_superuser:
            return
        raise

    def notify_administrators_of_submission(self, ev):
        # TODO
        pass

    def notify_submitter_of_approval(self, ev):
        # TODO
        pass

    def notify_submitter_of_rejection(self, ev):
        # TODO
        pass

    def notify_administrators_of_retraction(self, ev):
        # TODO
        pass

    def notify_administrators_of_activation(self, ev):
        # TODO
        pass

    def notify_administrators_of_pause(self, ev):
        # TODO
        pass

    def notify_administrators_of_deactivation(self, ev):
        # TODO
        pass

    # Runs for every transition to log action
    def _log_action(self, ev):
        StudyLog.objects.create(action=ev.state.name, study=ev.model, user=ev.kwargs.get('user'))

    # Runs for every transition to save state and log action
    def _finalize_state_change(self, ev):
        ev.model.save()
        self._log_action(ev)

# TODO Need a post_save hook for edit that pulls studies out of approved state
# TODO or disallows editing in pre_save if they are approved

@receiver(post_save, sender=Study)
def study_post_save(sender, **kwargs):
    """
    Create groups for all newly created Study isntances. We only
    run on study creation to avoid having to check for existence
    on each call to Study.save.
    """
    study, created = kwargs['instance'], kwargs['created']
    if created:
        from django.contrib.auth.models import Group
        for group in ['read', 'admin']:
            group_instance = Group.objects.create(name=f'{slugify(study.name)}-STUDY_{group}'.upper())
            for perm in Study._meta.permissions:
                # add only view permissions to non-admin
                if group == 'read' and perm != 'can_view':
                    continue
                assign_perm(perm[0], group_instance, obj=study)



class Response(models.Model):
    study = models.ForeignKey(Study, on_delete=models.DO_NOTHING, related_name='responses')
    participant = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    demographic_snapshot = models.ForeignKey(DemographicData, on_delete=models.DO_NOTHING)
    results = DateTimeAwareJSONField(default=dict)
    def __str__(self):
        return f'<Response: {self.study} {self.participant.get_short_name}>'

    class Meta:
        permissions = (
            ('view_response', 'View Response'),
        )


class Log(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return f'<{self.__class__.name}: {self.action} @ {self.created_at:%c}>'

    class Meta:
        abstract = True


class StudyLog(Log):
    action = models.CharField(max_length=128)
    study = models.ForeignKey(Study, on_delete=models.DO_NOTHING, related_name='logs', related_query_name='logs')

    def __str__(self):
        return f'<StudyLog: {self.action} on {self.study.name} at {self.created_at} by {self.user.username}'


class ResponseLog(Log):
    action = models.CharField(max_length=128)
    response = models.ForeignKey(Response, on_delete=models.DO_NOTHING)
