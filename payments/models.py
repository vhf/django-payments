from django.db import models
from django.utils.translation import ugettext_lazy as _
from uuid import uuid4
from django.conf import settings


DEFAULT_PAYMENT_STATUS_CHOICES = (
    ('waiting', _(u'Waiting for confirmation')),
    ('confirmed', _(u'Confirmed')),
    ('rejected', _(u'Rejected')),
    ('error', _(u'Error')),
)
PAYMENT_STATUS_CHOICES = getattr(settings, 'PAYMENT_STATUS_CHOICES',
                                 DEFAULT_PAYMENT_STATUS_CHOICES)
'''
List of possible payment statuses.
'''


class BasePayment(models.Model):
    '''
    Represents a single transaction. Each instance has one or more PaymentItem.
    '''
    variant = models.CharField(max_length=255)
    #: Transaction status
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES,
                              default='waiting')
    #: Creation date and time
    created = models.DateTimeField(auto_now_add=True)
    #: Date and time of last modification
    modified = models.DateTimeField(auto_now=True)
    #: Transaction ID (if applicable)
    transaction_id = models.CharField(max_length=255, blank=True)
    #: Currency code (may be provider-specific)
    currency = models.CharField(max_length=10)
    #: Total amount (gross)
    total = models.DecimalField(max_digits=9, decimal_places=2, default='0.0')
    delivery = models.DecimalField(max_digits=9, decimal_places=2,
                                   default='0.0')
    tax = models.DecimalField(max_digits=9, decimal_places=2, default='0.0')
    description = models.TextField(blank=True, default='')
    first_name = models.CharField(max_length=256, blank=True)
    last_name = models.CharField(max_length=256, blank=True)
    city = models.CharField(max_length=256, blank=True)
    country_area = models.CharField(max_length=256, blank=True)
    zip = models.CharField(max_length=256, blank=True)
    country = models.CharField(max_length=256, blank=True)
    extra_data = models.TextField(blank=True, default='')
    token = models.CharField(max_length=36, blank=True, default='')
    success_url = models.CharField(max_length=255, blank=True, default='')
    cancel_url = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        abstract = True

    def change_status(self, status):
        '''
        Updates the Payment status and sends the status_changed signal.
        '''
        from signals import status_changed
        self.status = status
        self.save()
        status_changed.send(sender=type(self), instance=self)

    def save(self, *args, **kwargs):
        if not self.token:
            for _i in xrange(100):
                token = str(uuid4())
                if not type(self).objects.filter(token=token).exists():
                    self.token = token
                    break
        return super(BasePayment, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.variant

    @models.permalink
    def get_absolute_url(self):
        return ('process_payment', (), {'variant': self.variant,
                                        'token': self.token})
