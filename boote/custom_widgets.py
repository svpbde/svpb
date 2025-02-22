from django.utils.html import escape, conditional_escape
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from django.forms.widgets import ClearableFileInput, CheckboxInput


class AdvancedFileInput(ClearableFileInput):
    # see https://djangosnippets.org/snippets/2581/

    def __init__(self, *args, **kwargs):

        self.url_length = kwargs.pop('url_length', 30)
        self.preview = kwargs.pop('preview', True)
        self.image_width = kwargs.pop('image_width', 200)
        super(AdvancedFileInput, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):

        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }
        template = '%(input)s'

        substitutions['input'] = super(ClearableFileInput, self).render(name, value, attrs)

        if value and hasattr(value, "url"):

            template = self.template_with_initial
            if self.preview:
                substitutions['initial'] = ('<a href="/{0}">{1}</a><br>\
                <a href="{0}" target="_blank"><img src="/{0}" width="{2}"></a><br>'.format
                    (escape(value.url), '...'+escape(force_str(value))[-self.url_length:],
                     self.image_width))
            else:
                substitutions['initial'] = ('<a href="/{0}">{1}</a>'.format
                    (escape(value.url), '...'+escape(force_str(value))[-self.url_length:]))
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)
