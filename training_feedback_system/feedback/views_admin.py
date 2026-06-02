from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import TrainingSession, Trainer
from .forms import TrainerForm

# All admin views are now public (no authentication)
def dashboard(request):
    return render(request, 'feedback/dashboard.html')

def manage_sessions(request):
    return render(request, 'feedback/manage_sessions.html')

def feedback_summary(request):
    return render(request, 'feedback/feedback_summary.html')

def trainer_list(request):
    trainers = Trainer.objects.all()
    return render(request, 'feedback/trainer_list.html', {'trainers': trainers})

def create_trainer(request):
    if request.method == 'POST':
        form = TrainerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trainer profile created successfully!')
            return redirect('feedback:trainer_list')
    else:
        form = TrainerForm()
    return render(request, 'feedback/create_trainer.html', {'form': form})

def edit_trainer(request, trainer_id):
    trainer = get_object_or_404(Trainer, id=trainer_id)
    if request.method == 'POST':
        form = TrainerForm(request.POST, instance=trainer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trainer updated successfully!')
            return redirect('feedback:trainer_list')
    else:
        form = TrainerForm(instance=trainer)
    return render(request, 'feedback/edit_trainer.html', {'form': form, 'trainer': trainer})

