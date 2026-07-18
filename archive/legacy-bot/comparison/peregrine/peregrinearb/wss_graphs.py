"""Wss Graphs."""
import cryptosockets
import asyncio
import order_book_trackers


class WSSHandler:
    """WSS Handler."""

    def __init__(self, exchange, tracker):
        """Initialize."""
        self.exchange = exchange
        self.tracker = tracker
