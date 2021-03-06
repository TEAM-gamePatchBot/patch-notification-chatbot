class QuickReply(object):

    CONTENT_TYPES = [
        'text',
        'location'
    ]

    def __init__(self, title=None, payload=None, image_url=None, content_type=None):

        if content_type is None:
            content_type = 'text'
        if content_type not in self.CONTENT_TYPES:
            raise ValueError('Invalid content_type provided.')
        if title and len(title) > 20:
            raise ValueError('Title cannot be longer 20 characters.')
        if payload and len(payload) > 1000:
            raise ValueError('Payload cannot be longer 1000 characters.')

        self.title = title
        self.payload = payload
        self.image_url = image_url
        self.content_type = content_type

    def to_dict(self):
        d = {
            'content_type': self.content_type,
        }

        if self.title:
            d['title'] = self.title
        if self.payload:
            d['payload'] = self.payload
        if self.image_url:
            d['image_url'] = self.image_url

        return d


class QuickReplies(object):
    def __init__(self, quick_replies):
        if len(quick_replies) > 10:
            raise ValueError('You cannot have more than 10 quick replies.')
        self.quick_replies = quick_replies

    def to_dict(self):
        return [
            quick_reply.to_dict() for quick_reply in self.quick_replies
        ]
