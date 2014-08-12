#!/usr/bin/env python

from __future__ import print_function


class SubscriptionError(Exception):
    pass


class SubscriptionService:
    _subscriptions = {}

    @classmethod
    def create_topic(cls, topic):
        if not topic in cls._subscriptions:
            cls._subscriptions[topic] = []
            return True
        return False

    @classmethod
    def subscribe(cls, topic, method):
        if not topic in cls._subscriptions:
            raise SubscriptionError("Service not found")
        if method in cls._subscriptions[topic]:
            return
        cls._subscriptions[topic].append(method)

    @classmethod
    def unsubscribe(cls, topic, method):
        if not topic in cls._subscriptions:
            return
        if method in cls._subscriptions[topic]:
            cls._subscriptions.remove(topic)

    @classmethod
    def broadcast(cls, topic, *args, **kwargs):
        if not topic in cls._subscriptions:
            raise SubscriptionError("Service not found.")
        for sub in cls._subscriptions[topic]:
            sub(*args, **kwargs)
