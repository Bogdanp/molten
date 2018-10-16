.. include:: global.rst

Advanced Topics
===============

Session Stores
^^^^^^^^^^^^^^

The ``molten.contrib.sessions`` module adds support for user sessions.
It works by providing a |Session| component -- a standard dictionary
that's guaranteed to contain a unique "id" key -- and a way to
serialize and deserialize Session objects via the |SessionStore|
protocol.

The only session store implementation that's provided out of the box
is |CookieStore|, which stores all the session information in browser
cookies.

Session Lifecycle
~~~~~~~~~~~~~~~~~

When a handler requests the |Session| component for the first time,
|SessionStore_load| is called to create the Session object based on
the incoming request data.  After the handler completes,
|SessionStore_dump| is called to serialize the Session and return a
|Cookie| representing it.

In pseudocode this process might look something like this::

  session = session_store.load()
  try:
      response = handler(session)
  finally:
      response.set_cookie(session_store.dump(session))

Custom Session Stores
~~~~~~~~~~~~~~~~~~~~~

To implement a custom session store, all you have to do is provide a
class that implements the |SessionStore| protocol.  Here's what a
redis-backed session store might look like, assuming you have a
``Redis`` component in the system that can communicate with a redis
server::

  class RedisStore:
      def load(self, cookies: Cookies, redis: Redis) -> Session:
          session_id = cookies.get("session-id")
          if not session_id:
              return Session.empty()

          session_data = redis.hgetall(session_id)
          if not session_data:
              return Session.empty()

          return Session(**session_data)

      def dump(self, session: Session, redis: Redis) -> Cookie:
          redis.hmset(session.id, session)
          return Cookie("session-id", session.id)

On ``load``, this store tries to get the current session id from the
request (via the "session-id" cookie) and then load the session data
from redis.  On ``dump``, it writes the session data to redis under
the session id key and it returns a |Cookie| containing the session id
so that subsequent calls to load can retrieve the session from Redis.
