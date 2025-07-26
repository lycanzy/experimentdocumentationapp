from django.contrib import admin
from .models import Experiment, Flow, Step, Sample, Metadata, StepType

@admin.register(StepType)
class StepTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')
    search_fields = ('code', 'name')
    ordering = ('code',)

@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_by', 'created_at')
    search_fields = ('id', 'title')
    list_filter = ('created_at',)

@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'experiment', 'created_at')
    search_fields = ('id', 'title')
    list_filter = ('created_at',)

@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'flow', 'step_type', 'date', 'created_at')
    search_fields = ('id', 'title')
    list_filter = ('date', 'created_at', 'step_type')
    filter_horizontal = ('people',)

@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('name', 'step')
    search_fields = ('name',)

@admin.register(Metadata)
class MetadataAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'step')
    search_fields = ('key', 'value')
