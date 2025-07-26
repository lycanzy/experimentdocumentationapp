from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from urllib.parse import urlencode
from django.contrib.auth.models import User
import logging

from .models import Experiment, Flow, Step, Sample, Metadata, StepType
from .forms import ExperimentForm, FlowForm, StepForm, SampleForm, MetadataForm

# Configure logging
logging.basicConfig(
    filename='step_creation.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
from django.contrib import messages
from .models import Experiment, Flow, Step, Sample, Metadata, StepType
from .forms import ExperimentForm, FlowForm, StepForm, SampleForm, MetadataForm, StepLinkForm

@login_required
def dashboard(request):
    experiments = Experiment.objects.filter(created_by=request.user)
    selected_experiment = None
    selected_flows = []
    
    if request.GET.get('experiment_id'):
        selected_experiment = get_object_or_404(Experiment, id=request.GET.get('experiment_id'))
        selected_flows = selected_experiment.flows.all().prefetch_related('steps', 'steps__people')
    
    # Get all users for the people selection in step creation
    from django.contrib.auth.models import User
    users = User.objects.all()
    
    # Get all step types for the dropdown
    from .models import StepType
    step_types = StepType.objects.all()
    
    return render(request, 'experiments/dashboard.html', {
        'experiments': experiments,
        'selected_experiment': selected_experiment,
        'selected_flows': selected_flows,
        'users': users,
        'step_types': step_types
    })

@login_required
def experiment_create(request):
    if request.method == 'POST':
        form = ExperimentForm(request.POST)
        if form.is_valid():
            experiment = form.save(commit=False)
            experiment.created_by = request.user
            experiment.save()
            messages.success(request, 'Experiment created successfully.')
            return redirect('experiment_detail', experiment_id=experiment.id)
    else:
        form = ExperimentForm()
    return render(request, 'experiments/experiment_form.html', {'form': form})

@login_required
def experiment_detail(request, experiment_id):
    experiment = get_object_or_404(Experiment, id=experiment_id)
    flows = experiment.flows.all()
    return render(request, 'experiments/experiment_detail.html', {
        'experiment': experiment,
        'flows': flows
    })

@login_required
def flow_create(request, experiment_id):
    experiment = get_object_or_404(Experiment, id=experiment_id)
    if request.method == 'POST':
        form = FlowForm(request.POST)
        if form.is_valid():
            flow = form.save(commit=False)
            flow.experiment = experiment
            flow.save()
            messages.success(request, 'Flow created successfully.')
            return redirect('flow_detail', flow_id=flow.id)
    else:
        form = FlowForm()
    return render(request, 'experiments/flow_form.html', {
        'form': form,
        'experiment': experiment
    })

@login_required
def flow_detail(request, flow_id):
    flow = get_object_or_404(Flow, id=flow_id)
    steps = flow.steps.all()
    return render(request, 'experiments/flow_detail.html', {
        'flow': flow,
        'steps': steps
    })

@login_required
def step_create(request, flow_id):
    flow = get_object_or_404(Flow, id=flow_id)
    experiment_id = flow.experiment.id
    
    if request.method == 'POST':
        logger.debug(f"POST data received: {request.POST}")
        
        # Get the selected step type
        step_type_code = request.POST.get('step_type')
        if not step_type_code:
            messages.error(request, 'Step type is required')
            return redirect(f"{reverse('dashboard')}?experiment_id={experiment_id}")
        
        try:
            # Get the step type object
            step_type = get_object_or_404(StepType, code=step_type_code)
            logger.debug(f"Found step type: {step_type.code} - {step_type.name}")
            
            # Generate next step number
            next_number = Step.get_next_number(flow.id, step_type.code)
            full_step_suffix = f"{step_type.code}{next_number:02d}"
            full_step_id = f"{flow.id}-{full_step_suffix}"
            logger.debug(f"Generated step ID: {full_step_id}")
            
            # Check for existing step
            if Step.objects.filter(id=full_step_id).exists():
                logger.error(f"Step ID {full_step_id} already exists")
                messages.error(request, f'Step ID {full_step_id} already exists')
                return redirect(f"{reverse('dashboard')}?experiment_id={experiment_id}")
            
            # Create a new dictionary with the POST data
            step_data = request.POST.copy()
            step_data['id'] = full_step_id
            logger.debug(f"Created step data with ID: {full_step_id}")
            
            # Create and validate the form with the flow context
            form = StepForm(step_data, flow=flow)
            logger.debug(f"Form data: {form.data}")
            
            if form.is_valid():
                logger.debug("Form is valid, saving...")
                try:
                    with transaction.atomic():
                        step = form.save(commit=False)
                        step.flow = flow
                        step.step_type = step_type
                        
                        # Handle previous step relationship
                        previous_step_id = request.POST.get('previous_step')
                        if previous_step_id:
                            step.previous_step = Step.objects.get(id=previous_step_id)
                            logger.debug(f"Set previous step: {previous_step_id}")
                        
                        step.save()
                        logger.debug(f"Step saved with ID: {step.id}")
                        
                        # Handle the many-to-many relationship for people
                        people_ids = request.POST.getlist('people')
                        step.people.set(people_ids)
                        logger.debug(f"Added people: {people_ids}")
                        
                        messages.success(request, 'Step created successfully.')
                except Exception as e:
                    logger.error(f"Error saving step: {str(e)}")
                    messages.error(request, f'Error saving step: {str(e)}')
                    return redirect(f"{reverse('dashboard')}?experiment_id={experiment_id}")
            else:
                logger.error(f"Form validation errors: {form.errors}")
                error_messages = []
                for field, errors in form.errors.items():
                    error_messages.append(f"{field}: {', '.join(errors)}")
                messages.error(request, 'Please correct the following errors: ' + '; '.join(error_messages))
        except Exception as e:
            logger.error(f"Error generating step ID: {str(e)}")
            messages.error(request, f'Error generating step ID: {str(e)}')
            return redirect(f"{reverse('dashboard')}?experiment_id={experiment_id}")
    
    # Always redirect back to the dashboard with the experiment ID
    base_url = reverse('dashboard')
    query_params = urlencode({'experiment_id': experiment_id})
    return redirect(f'{base_url}?{query_params}')

@login_required
def step_detail(request, step_id):
    step = get_object_or_404(Step, id=step_id)
    samples = step.samples.all()
    metadata = step.metadata.all()

    if request.method == 'POST' and 'update_previous_step' in request.POST:
        link_form = StepLinkForm(request.POST, instance=step, flow=step.flow, exclude_step=step)
        if link_form.is_valid():
            link_form.save()
            messages.success(request, 'Step relationship updated successfully.')
            return redirect('step_detail', step_id=step.id)
    else:
        link_form = StepLinkForm(instance=step, flow=step.flow, exclude_step=step)

    sample_form = SampleForm()
    metadata_form = MetadataForm()
    
    return render(request, 'experiments/step_detail.html', {
        'step': step,
        'samples': samples,
        'metadata': metadata,
        'sample_form': sample_form,
        'metadata_form': metadata_form,
        'link_form': link_form
    })

@login_required
def add_sample(request, step_id):
    step = get_object_or_404(Step, id=step_id)
    if request.method == 'POST':
        form = SampleForm(request.POST)
        if form.is_valid():
            sample = form.save(commit=False)
            sample.step = step
            sample.save()
            messages.success(request, 'Sample added successfully.')
    return redirect('step_detail', step_id=step.id)

@login_required
def add_metadata(request, step_id):
    step = get_object_or_404(Step, id=step_id)
    if request.method == 'POST':
        form = MetadataForm(request.POST)
        if form.is_valid():
            metadata = form.save(commit=False)
            metadata.step = step
            metadata.save()
            messages.success(request, 'Metadata added successfully.')
    return redirect('step_detail', step_id=step.id)

@login_required
def delete_step(request, step_id):
    step = get_object_or_404(Step, id=step_id)
    experiment_id = step.flow.experiment.id
    
    if request.method == 'POST':
        # Check if step has any next steps (children)
        if step.next_steps.exists():
            messages.error(request, 'Cannot delete this step because it has dependent steps. Remove the dependencies first.')
        else:
            # Store flow_id before deletion for redirect
            flow_id = step.flow.id
            # Delete the step
            step.delete()
            messages.success(request, f'Step {step_id} was successfully deleted.')
    
    return redirect(f"{reverse('dashboard')}?experiment_id={experiment_id}")
