from celery import shared_task
import requests
import logging

logger = logging.getLogger(__name__)

@shared_task
def get_character_id_from_sso_code(authorization_code):
        #first we need to exchange the code for a token
        client_id = settings.SSO_CLIENT_ID
        client_secret = settings.SSO_CLIENT_SECRET
        authorization_code = '%s:%s' % (client_id, client_secret)
        code_64 = base64.b64encode(authorization_code.encode('utf-8'))
        authorization = 'Basic ' + code_64
        custom_headers = {
            'Authorization': authorization,
            'content-type': 'application/json',
        }
        data = {
            'grant_type': 'authorization_code',
            'code': code,
        }
        path = "https://login.eveonline.com/oauth/token"
        r = requests.post(path, headers=custom_headers, json=data)
        if not r.status_code in [200, 201]:
            logger.error("Received bad status from code exchange: %s" % r.status_code)
            return None
        token = r.json()['access_token']
        logger.debug("Received access token: %s" % token)

        #now pull character ID from token
        custom_headers = {'Authorization': 'Bearer ' + token}
        path = "https://login.eveonline.com/oauth/verify"
        r = requests.get(path, headers=custom_headers)
        if not r.status_code in [200,201]:
            logger.error("Received bad status from token validation: %s" % r.status_code)
            return None
        character_id = r.json()['CharacterID']
        logger.debug("Received character id %s" % str(character_id))
        return character_id
