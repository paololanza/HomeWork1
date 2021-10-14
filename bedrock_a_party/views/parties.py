from flakon import JsonBlueprint
from flask import abort, jsonify, request

from bedrock_a_party.classes.party import CannotPartyAloneError, ItemAlreadyInsertedByUser, NotExistingFoodError, NotInvitedGuestError, Party

parties = JsonBlueprint('parties', __name__)

_LOADED_PARTIES = {}  # dict of available parties
_PARTY_NUMBER = 0  # index of the last created party

@parties.route("/parties", methods = ['POST', 'GET'])
def all_parties():
    result = None
    if request.method == 'POST':
        try:
            #create a new party
            result = create_party(request)

        #case in which the party hasn't guests
        except CannotPartyAloneError as e:
            abort(400, str(e))

    elif request.method == 'GET':
        #call the function that return all parties
        result = get_all_parties()

    return result

@parties.route("/parties/loaded", methods = ['GET'])
def loaded_parties():
    #return the number of the party loaded
    return jsonify({"loaded_parties" : len(_LOADED_PARTIES)})


@parties.route("/party/<id>", methods = ['GET', 'DELETE'])
def single_party(id):
    global _LOADED_PARTIES

    #call the function that checks if the party exist
    exists_party(id)

    if 'GET' == request.method:
        #get the party identified by id and return the object Party serialized
        result = jsonify(_LOADED_PARTIES.get(id).serialize())

    elif 'DELETE' == request.method:
        #delete a party identified by id
        del _LOADED_PARTIES[id]

        #return a message that the delete operation is fine
        result = jsonify({"msg" : "Party deleted!"})

    return result

@parties.route("/party/<id>/foodlist", methods = ['GET'])
def get_foodlist(id):
    global _LOADED_PARTIES

    #call the function that checks if the party exist
    exists_party(id)

    if 'GET' == request.method:
        #return the object Foodlist serialized of the party identified by id 
        result = jsonify({"foodlist" : _LOADED_PARTIES[id].get_food_list().serialize()})

    return result


@parties.route("/party/<id>/foodlist/<user>/<item>", methods = ['POST', 'DELETE'])
def edit_foodlist(id, user, item):
    global _LOADED_PARTIES

    #call the function that checks if the party exist
    exists_party(id)

    #get the party identified by id
    party = _LOADED_PARTIES[id]
    result = ""

    if 'POST' == request.method:
        #add Food object in the FoodList of the Party identified by id
        try:
            result = jsonify(party.add_to_food_list(item, user).serialize())
        
        #case in which the user is not invited at the party identified by id
        except NotInvitedGuestError as e:
            abort(401, str(e))

        #case in which the Food object is already insert by user
        except ItemAlreadyInsertedByUser as e:
            abort(400, str(e))

    if 'DELETE' == request.method:
        #delete Food object from the Foodlist of the party identified by id
        try:
            #remove the item
            party.remove_from_food_list(item, user)

            #return a message that the delete operation is fine
            result = jsonify({"msg" : "Food deleted!"})

        #case in which the Food not existing 
        except NotExistingFoodError as e:
            abort(400, str(e))

    return result

#
# These are utility functions. Use them, DON'T CHANGE THEM!!
#

def create_party(req):
    global _LOADED_PARTIES, _PARTY_NUMBER

    # get data from request
    json_data = req.get_json()

    # list of guests
    try:
        guests = json_data['guests']
    except:
        raise CannotPartyAloneError("you cannot party alone!")

    # add party to the loaded parties lists
    _LOADED_PARTIES[str(_PARTY_NUMBER)] = Party(_PARTY_NUMBER, guests)
    _PARTY_NUMBER += 1

    return jsonify({'party_number': _PARTY_NUMBER - 1})


def get_all_parties():
    global _LOADED_PARTIES

    return jsonify(loaded_parties=[party.serialize() for party in _LOADED_PARTIES.values()])


def exists_party(_id):
    global _PARTY_NUMBER
    global _LOADED_PARTIES

    if int(_id) > _PARTY_NUMBER:
        abort(404)  # error 404: Not Found, i.e. wrong URL, resource does not exist
    elif not(_id in _LOADED_PARTIES):
        abort(410)  # error 410: Gone, i.e. it existed but it's not there anymore
