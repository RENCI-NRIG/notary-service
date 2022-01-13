import os
import json
from django.shortcuts import render
from jwcrypto import jwk


def handler400(request, exception):
    if request.GET["code"] is None:
        response = render(request, '400.html', {})
    else:
        response = render(
            request, 'authresponse.html',
            {
                'code': request.GET["code"],
                'state': request.GET["state"]
            }
        )
    response.status_code = 400
    return response


def handler404(request, exception):
    response = render(request, '404.html', {})
    response.status_code = 404
    return response


def handler500(request):
    response = render(request, '500.html', {})
    response.status_code = 500
    return response


def whoami(request):
    hostname = os.getenv('NS_NAME', 'localhost')
    return render(request, 'whoami.html', {'home_page': 'active', 'hostname': hostname})


def jwks(request):
    pubkey_dict = { 'keys': [{
        'use': 'sig',
        'alg': 'RS256'
    }]}
    with open(os.getenv('NS_PRESIDIO_JWT_PUBLIC_KEY_PATH'), 'rb') as f:
        if f.readable():
            pubkey = jwk.JWK.from_pem(f.read())
        else:
            pubkey = None
    if pubkey:
        for key in pubkey.keys():
            pubkey_dict['keys'][0][str(key)] = str(pubkey.get(key))

    from_json = jwk.JWK.from_json(json.dumps(pubkey_dict.get('keys')[0]))
    print(from_json.export_to_pem())
    return render(request, 'jwks.html', {'home_page': 'active', 'jwks': json.dumps(pubkey_dict)})


def signup1(request):
    enrollment_url = os.getenv('OIDC_USER_ENROLLMENT_WORKFLOW')
    return render(request, 'signup1.html', {'home_page': 'active', 'enrollment_url': enrollment_url})


def signup2(request):
    return render(request, 'signup2.html', {'home_page': 'active'})


def signup3(request):
    return render(request, 'signup3.html', {'home_page': 'active'})
