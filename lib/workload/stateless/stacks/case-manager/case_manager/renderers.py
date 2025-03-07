from rest_framework.renderers import BaseRenderer, JSONRenderer, StaticHTMLRenderer


class BinaryRenderer(BaseRenderer):
    media_type = "application/octet-stream"
    charset = None
    render_style = "binary"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class ImageRenderer(BaseRenderer):
    media_type = "image/*"
    charset = None
    render_style = "binary"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class JPEGRenderer(ImageRenderer):
    media_type = "image/jpeg"
    format = "jpg"


class PNGRenderer(ImageRenderer):
    media_type = "image/png"
    format = "png"


class GIFRenderer(ImageRenderer):
    media_type = "image/gif"
    format = "gif"


content_renderers = [JSONRenderer, StaticHTMLRenderer, ImageRenderer, BinaryRenderer]
