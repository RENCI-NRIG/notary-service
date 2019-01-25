import os
from django.shortcuts import render
from .forms import TerminalForm, ComanageForm
import subprocess as sp
from ldap3 import Connection, Server, ALL

ldap_host = os.getenv('LDAP_HOST', '')
ldap_user = os.getenv('LDAP_USER', '')
ldap_password = os.getenv('LDAP_PASSWORD', '')
ldap_search_base = os.getenv('LDAP_SEARCH_BASE', '')

server = Server(ldap_host, use_ssl=True, get_info=ALL)


def debug(request):
    debug_page = "active"
    if request.user.is_authenticated:
        terminal, terminal_output = debug_terminal(request)
        comanage, comanage_output = debug_comanage(request)
        if terminal_output:
            output = terminal_output
        elif comanage_output:
            output = comanage_output
    return render(request, 'debug.html', locals())


# Create your views here.
def debug_terminal(request):
    terminal_output = ""
    terminal = TerminalForm()

    if request.method == "POST" and request.POST.get('submit_terminal'):
        terminal = TerminalForm(request.POST)
        if terminal.is_valid():
            execute_command = terminal.cleaned_data['command']
            try:
                terminal_output = sp.check_output(execute_command, shell=True)
                terminal_output = terminal_output.decode()
            except sp.CalledProcessError:
                terminal_output = "Command '" + terminal.cleaned_data['command'] + "' returned non-zero exit status"
    return terminal, terminal_output


def debug_comanage(request):
    ATTRIBUTES = [
        'sn',
        'cn',
        'objectClass',
        'givenName',
        'mail',
        'employeeNumber',
        'uid',
        'eduPersonAffiliation',
        'eduPersonPrincipalName',
        'isMemberOf',
        'dc',
        'o',
        'description',
        'userPassword'
    ]
    comanage_output = ''
    comanage = ComanageForm()
    if request.method == "POST" and request.POST.get('submit_comanage'):
        comanage = ComanageForm(request.POST)
        if comanage.is_valid():
            ldap_search_filter = '(objectclass=' + comanage.cleaned_data['object_class'] + ')'
            conn = Connection(server, ldap_user, ldap_password, auto_bind=True)
            personnel_found = conn.search(
                ldap_search_base,
                ldap_search_filter,
                attributes=ATTRIBUTES
            )
            if personnel_found:
                for entry in conn.entries:
                    comanage_output = comanage_output + str(entry)
            conn.unbind()

    return comanage, comanage_output
