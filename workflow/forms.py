from django import forms

from workflow.models import DECISION_CODES, WorkflowStep, WorkflowTemplate


class TemplateForm(forms.ModelForm):
    class Meta:
        model = WorkflowTemplate
        fields = ['code', 'name', 'category', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                'class', 'form-select' if isinstance(field.widget, forms.Select)
                else 'form-control'
            )


class StepForm(forms.ModelForm):
    decisions = forms.MultipleChoiceField(
        choices=[(c, c.replace('_', ' ').title()) for c in DECISION_CODES],
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )
    condition_text = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'rows': 5}),
        label='Condition (JSON, optional)',
        help_text='Examples: {"unit_kind": ["suite", "hall"]} or '
                  '{"any": [{"min_nights": 4}, {"applicant_category": ["organization"]}]}. '
                  'Leave blank to always include this step.',
    )

    class Meta:
        model = WorkflowStep
        fields = ['order', 'name', 'role', 'sla_hours', 'is_final']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['decisions'].initial = self.instance.allowed_decisions
        for name, field in self.fields.items():
            if name in ('decisions', 'condition_text'):
                continue
            field.widget.attrs.setdefault(
                'class', 'form-select' if isinstance(field.widget, forms.Select)
                else 'form-control'
            )

    def save(self, commit=True):
        step = super().save(commit=False)
        step.allowed_decisions = self.cleaned_data['decisions']
        if commit:
            step.save()
        return step
