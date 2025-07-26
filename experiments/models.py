from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class StepType(models.Model):
    code = models.CharField(
        max_length=2,
        primary_key=True,
        validators=[RegexValidator(r'^[A-Z]{2}$', 'Code must be 2 uppercase letters')],
        help_text='Two-letter code for the step type (e.g., ML)'
    )
    name = models.CharField(max_length=100, help_text='Full name of the step type (e.g., Milling)')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']

class Experiment(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=6,
        validators=[RegexValidator(r'^[A-Z]{3}\d{3}$', 'Format must be AAA000')],
        help_text='Experiment ID in format AAA000'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.title}"

class Flow(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=8,
        validators=[RegexValidator(r'^[A-Z]{3}\d{3}[A-Z]{2}$', 'Format must be AAA000AA')],
        help_text='Flow ID in format AAA000AA'
    )
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='flows')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.title}"

class Step(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=13,
        validators=[RegexValidator(r'^[A-Z]{3}\d{3}[A-Z]{2}-[A-Z]{2}\d{2}$', 'Format must be AAA000AA-AA00')],
        help_text='Step ID in format AAA000AA-AA00'
    )
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, related_name='steps')
    step_type = models.ForeignKey(StepType, on_delete=models.PROTECT, related_name='steps')
    previous_step = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='next_steps')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    people = models.ManyToManyField(User, related_name='assigned_steps')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_next_number(cls, flow_id, step_type_code):
        """Get the next available number (00-99) for a given step type in a flow"""
        # Look for steps that match the pattern AAA000AA-XX00 where XX is the step_type_code
        existing_steps = cls.objects.filter(
            flow_id=flow_id,
            id__contains=f"-{step_type_code}"
        ).order_by('-id')
        
        if not existing_steps.exists():
            return 0
            
        last_step = existing_steps.first()
        last_number = int(last_step.id[-2:])  # Get the last two digits
        next_number = last_number + 1
        
        if next_number > 99:
            raise ValueError("Maximum step number (99) reached for this type")
            
        return next_number

    def __str__(self):
        return f"{self.id} - {self.title}"

class Sample(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='samples')
    
    def __str__(self):
        return f"{self.name} ({self.step.id})"

class Metadata(models.Model):
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='metadata')
    key = models.CharField(max_length=100)
    value = models.TextField()
    
    def __str__(self):
        return f"{self.key}: {self.value}"
