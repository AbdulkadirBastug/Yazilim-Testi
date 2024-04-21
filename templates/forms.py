from django import forms

class GitHubRepoForm(forms.Form):#Github repo urlsi için form
    repository_url = forms.URLField(label='GitHub Repository URL', max_length=1000)
