import csv
import io
from django import forms
from .models import Deck, Card


class DeckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Korean Vocabulary'}),
            'description': forms.Textarea(attrs={'placeholder': 'Optional description...', 'rows': 3}),
        }


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['front', 'back']
        widgets = {
            'front': forms.TextInput(attrs={'placeholder': 'Front (question / word)'}),
            'back': forms.TextInput(attrs={'placeholder': 'Back (answer / translation)'}),
        }


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Two columns: front, back. With or without a header row.'
    )

    def clean_csv_file(self):
        f = self.cleaned_data['csv_file']
        if not f.name.endswith('.csv'):
            raise forms.ValidationError('File must be a .csv file.')
        return f

    def get_cards(self):
        f = self.cleaned_data['csv_file']
        content = f.read().decode('utf-8-sig')  # handle BOM from Excel
        reader = csv.reader(io.StringIO(content))
        cards = []
        for i, row in enumerate(reader):
            if len(row) < 2:
                continue
            front = row[0].strip()
            back = row[1].strip()
            if not front or not back:
                continue
            # skip header row if it looks like one
            if i == 0 and front.lower() in ('front', 'word', 'question', 'term'):
                continue
            cards.append((front, back))
        return cards