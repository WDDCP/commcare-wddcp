from corehq.apps.users.models import CommCareUser


def _users_by_location(location_id, include_docs, wrap):
    view = CommCareUser.view if wrap else CommCareUser.get_db().view
    return view(
        'locations/users_by_location_id',
        startkey=[location_id],
        endkey=[location_id, {}],
        include_docs=include_docs,
    ).all()


def get_users_by_location_id(location_id, wrap=True):
    """
    Get all users for a given location
    """
    return _users_by_location(location_id, include_docs=True, wrap=wrap)


def get_user_ids_by_location(location_id):
    return [user['id'] for user in
            _users_by_location(location_id, include_docs=False, wrap=False)]
