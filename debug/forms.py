from django import forms


class TerminalForm(forms.Form):
    command = forms.CharField(max_length=200)


class ComanageForm(forms.Form):
    CHOICES = (
        ('organization', 'organization'),
        ('organizationalUnit', 'organizationalUnit'),
        ('groupOfNames', 'groupOfNames'),
        ('person', 'person'),
        ('organizationalPerson', 'organizationalPerson'),
        ('inetOrgPerson', 'inetOrgPerson'),
        ('eduPerson', 'eduPerson'),
        ('eduMember', 'eduMember'),
        ('CILogonPerson', 'CILogonPerson'),
        ('account', 'account'),
        ('simpleSecurityObject', 'simpleSecurityObject'),
    )
    object_class = forms.ChoiceField(
        choices=CHOICES,
        label='objectClass',
        initial=CHOICES[3][1]
    )
