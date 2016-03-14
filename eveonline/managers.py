import evelink.api
import evelink.char
import evelink.eve
import evelink.corp
import logging
from django.db import models
import requests
import datetime

logger = logging.getLogger(__name__)

class EVEContactManager(models.Manager):
    def create_from_api(self, dict, contact_source):
        model = self.model()
        model.object_id = dict['id']
        model.object_name = dict['name']
        model.standing = dict['standing']
        model.contact_source = contact_source
        model.save()
        return model

class EVEBaseManager(models.Manager):
    class Meta:
        abstract = True

    def check_id(self, id):
        return False

    def create(self, *args, **kwargs):
        model = super(EVEBaseManager, self).create(*args, **kwargs)
        if not self.check_id(model.id):
            model.delete()
            raise ValueError("Supplied ID is invalid")
        model.update()
        return model

    def get_or_create_by_id(self, id):
        if super(EVEBaseManager, self).get_queryset().filter(id=id).exists():
            logger.debug("Returning existing model with id %s" % id)
            return super(EVEBaseManager, self).get_queryset().get(id=id), False
        else:
            logger.debug("No model exists for id %s - triggering creation." % id)
            return self.create(id=id), True

    def get_by_id(self, id):
        return self.get_or_create_by_id(id)[0]

class EVECharacterManager(EVEBaseManager):
    DOOMHEIM_CORP_ID = 1000001

    def check_id(self, id):
        logger.debug("Checking if %s %s is valid character id" % (type(id), id))
        id = int(id)
        api = evelink.eve.EVE()
        result = api.affiliations_for_characters(id).result[id]
        if result['name']:
            if result['corp']['id'] != self.DOOMHEIM_CORP_ID:
                logger.debug("Determined character id %s is valid" % id)
                return True
            else:
                logger.debug("Determined character id %s has been biomassed and is invalid" % id)
                return False
        else:
            logger.debug("Determined character id %s is invalid" % id)
            return False

class EVECorporationManager(EVEBaseManager):
    def check_id(self, id):
        logger.debug("Checking if %s %s is valid corp id" % (type(id), id))
        id = int(id)
        try:
            a = evelink.api.API()
            api = evelink.corp.Corp(a)
            result = api.corporation_sheet(corp_id=id).result
            logger.debug("Determined corp id %s is valid" % id)
            return True
        except evelink.api.APIError as e:
            if int(e.code) == 523:
                logger.debug("Determined corp id %s is invalid" % id)
                return False
            else:
                raise e

class EVEAllianceManager(EVEBaseManager):

    CREST_ALLIANCE_ENDPOINT = "https://public-crest.eveonline.com/alliances/%s/"

    def create(self, *args, **kwargs):
        model = super(EVEAllianceManager, self).create(*args, **kwargs)
        if not self.check_id(model.id):
            model.delete()
            raise ValueError("Supplied ID is invalid")
        model.update(alliance_info=self.get_info(model.id))
        return model

    def check_id(self, id):
        r = requests.get(self.CREST_ALLIANCE_ENDPOINT % id)
        if r.status_code == 200:
            return True
        elif r.status_code == 403:
            return False
        else:
            e = evelink.api.APIError()
            e.code = r.status_code
            e.message = "Unexpected CREST error occured"
            e.expires = None
            e.timestamp = datetime.datetime.utcnow()
            raise e

    def get_info(self, id):
        r = requests.get(self.CREST_ALLIANCE_ENDPOINT % id)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 403:
            raise ValueError("Invalid alliance ID supplied")
        else:
            e = evelink.api.APIError()
            e.code = r.status_code
            e.message = "Unexpected CREST error occured"
            e.expires = None
            e.timestamp = datetime.datetime.utcnow()
            raise e

class EVEApiKeyPairManager(models.Manager):
    CONTACTLIST_MASK = 16

    def get_contact_source_apis(self):
        choices = []
        apis = super(EVEApiKeyPairManager,self).get_queryset().filter(type='corp').filter(is_valid=True)
        for api in apis:
            if api.access_mask & self.CONTACTLIST_MASK == self.CONTACTLIST_MASK:
                choices.append(api.pk)
        return {'pk__in':choices}

class EVEManager:

    @staticmethod
    def create_alliances(alliance_ids):
        for id in alliance_ids:
            alliance, created = EVEAlliance.objects.get_or_create(id = id)
            if created:
                logger.info("Created model for alliance id %s" % id)
            else:
                logger.warn("Attempting to create existing model for alliance id %s" % id)
            EVEManager.update_alliances([id])

    @staticmethod
    def update_alliances(ids):
        api = evelink.eve.EVE()
        result = api.alliances().result
        for id in ids:
            alliance = EVEManager.get_alliance_by_id(id)
            if id in result:
                logger.debug("Alliance id %s found in alliance list, updating." % id)
                alliance.name = result[id]['name']
                alliance.ticker = result[id]['ticker']
                alliance.save()
                logger.info("Updated alliance info for %s" % alliance)
            else:
                logger.info("Alliance %s no longer exists. Deleting model." % id)
                alliance.delete()
        logger.debug("Finished updating alliance models %s" % ids)

    @staticmethod
    def check_if_character_id_valid(id):
        logger.debug("Checking if %s %s is valid character id" % (type(id), id))
        id = int(id)
        api = evelink.eve.EVE()
        result = api.affiliations_for_characters(id).result[id]
        if 'name' in result:
            logger.debug("Determined character id %s is valid" % id)
            return True
        else:
            logger.debug("Determined character id %s is invalid" % id)
            return False

    @staticmethod
    def check_if_corp_id_valid(id):
        logger.debug("Checking if %s %s is valid corp id" % (type(id), id))
        id = int(id)
        a = evelink.api.API()
        api = evelink.corp.Corp(a)
        try:
            result = api.corporation_sheet(corp_id=id).result
            logger.debug("Determined corp id %s is valid" % id)
            return True
        except:
            logger.debug("Determined corp id %s is invalid" % id)
            return False

    @staticmethod
    def check_if_alliance_id_valid(id):
        logger.debug("Checking if %s %s is valid alliance id" % (type(id), id))
        id = int(id)
        api = evelink.eve.EVE()
        result = api.alliances().result
        if id in result:
            logger.debug("Determind alliance id %s is valid" % id)
            return True
        else:
            logger.debug("Determined alliance id %s is invalid" % id)
            return False
        
class EVEApiManager:
    @staticmethod
    def get_characters_from_api(id, vcode):
        chars = []
        logger.debug("Getting characters from api id %s" % id)
        try:
            api = evelink.api.API(api_key=(id, vcode))
            account = evelink.account.Account(api=api)
            chars = account.characters()
        except evelink.api.APIError as error:
            logger.exception("APIError occured while retrieving characters for api id %s" % api_id, exc_info=True)

        logger.debug("Retrieved characters %s from api id %s" % (chars, id))
        return chars

    @staticmethod
    def check_api_is_type_account(id, vcode):
        logger.debug("Checking if api id %s is account." % id)
        try:
            api = evelink.api.API(api_key=(id, vcode))
            account = evelink.account.Account(api=api)
            info = account.key_info()
            logger.debug("API id %s is type %s" % (id, info[0]['type']))
            return info[0]['type'] == "account"

        except evelink.api.APIError as error:
            logger.exception("APIError occured while checking if api id %s is type account" % id, exc_info=True)

        return None

    @staticmethod
    def check_api_key_is_valid(id, vcode):
        logger.debug("Checking if api id %s is valid." % id)
        try:
            api = evelink.api.API(api_key=(id, vcode))
            account = evelink.account.Account(api=api)
            info = account.key_info()
            logger.info("Verified api id %s is valid." % id)
            return True
        except:
            logger.info("API id %s is invalid." % id)
            return False

    @staticmethod
    def check_if_api_server_online():
        logger.debug("Checking if API server online.")
        try:
            api = evelink.api.API()
            server = evelink.server.Server(api=api)
            info = server.server_status()
            logger.info("Verified API server is online and reachable.")
            return True
        except evelink.api.APIError as error:
            logger.exception("APIError occured while trying to query api server status.", exc_info=True)

        logger.warn("Unable to reach API server.")
        return False

    @staticmethod
    def get_corp_standings_from_api(id, vcode):
        try:
            logger.debug("Getting corp standings with api id %s" % id)
            api = evelink.api.API(api_key=(id, vcode))
            corp = evelink.corp.Corp(api=api)
            corpinfo = corp.contacts()
            results = corpinfo[0]
            return results
        except evelink.api.APIError as error:
            logger.exception("APIError occured while retrieving corp standings from api id %s" % id, exc_info=True)
        return {}
