from django import forms
from .models import Experiment, Flow, Step, Sample, Metadata

class ExperimentForm(forms.ModelForm):
    class Meta:
        model = Experiment
        fields = ['id', 'title', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class FlowForm(forms.ModelForm):
    class Meta:
        model = Flow
        fields = ['id', 'title', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class StepForm(forms.ModelForm):
    previous_step = forms.ModelChoiceField(
        queryset=Step.objects.none(),  # We'll set this dynamically in the view
        required=False,
        empty_label="(No previous step)"
    )

    class Meta:
        model = Step
        fields = ['id', 'title', 'description', 'people', 'date', 'step_type', 'previous_step']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'step_type': forms.Select(),
        }

    def __init__(self, *args, flow=None, **kwargs):
        super().__init__(*args, **kwargs)
        if flow:
            # Only show steps from the same flow as options for previous_step
            self.fields['previous_step'].queryset = Step.objects.filter(flow=flow)

class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class MetadataForm(forms.ModelForm):
    class Meta:
        model = Metadata
        fields = ['key', 'value']
        widgets = {
            'value': forms.Textarea(attrs={'rows': 2}),
        }

class StepLinkForm(forms.ModelForm):
    previous_step = forms.ModelChoiceField(
        queryset=Step.objects.none(),
        required=False,
        empty_label="(No previous step)"
    )

    class Meta:
        model = Step
        fields = ['previous_step']

    def __init__(self, *args, flow=None, exclude_step=None, **kwargs):
        super().__init__(*args, **kwargs)
        if flow:
            # Filter out the current step and its descendants to prevent cycles
            queryset = Step.objects.filter(flow=flow)
            if exclude_step:
                # Get all descendants of the current step
                descendants = [exclude_step.id]
                next_steps = list(exclude_step.next_steps.all())
                while next_steps:
                    step = next_steps.pop(0)
                    descendants.append(step.id)
                    next_steps.extend(list(step.next_steps.all()))
                queryset = queryset.exclude(id__in=descendants)
            self.fields['previous_step'].queryset = queryset
