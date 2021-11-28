# coding: utf-8
import re

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.extractor.peertube import PeerTubeIE
from yt_dlp.utils import UnsupportedError
from ytdlp_plugins.utils import ParsedURL

__version__ = "2021.11.24"


# pylint: disable=abstract-method
class Auf1IE(InfoExtractor):
    IE_NAME = "auf1"
    _VALID_URL = r"""(?x)
                    https?://
                        (?:www\.)?
                        (?:auf1\.tv/)
                        (?:[^/]+/)*
                        (?P<id>[^/]+)
                    """

    _TESTS = [
        {
            "url": "https://auf1.tv/nachrichten-auf1/ampelkoalition-eine-abrissbirne-fuer-deutschland/",
            "info_dict": {
                "id": "j3fw1Qn2TGVtqjeLe8xCgv",
                "title": "Ampelkoalition: Eine Abrissbirne für Deutschland?",
                "description": "md5:5ebfa2e7db1e251a2c53b3d34491b188",
                "ext": "mp4",
                "thumbnail": r"re:https://auf1.gegenstimme.tv/static/thumbnails/[\w-]+.jpg",
                "timestamp": 1637948607,
                "upload_date": "20211126",
                "uploader": "auf1tv",
                "uploader_id": "3",
                "duration": 818,
                "view_count": int,
                "like_count": int,
                "dislike_count": int,
                "categories": ["News & Politics"],
            },
            "params": {"skip_download": True, "nocheckcertificate": True},
        },
        {
            # playlist
            "url": "https://auf1.tv/videos",
            "info_dict": {
                "id": "videos",
                "title": "AUF1.TV - Alle Videos",
            },
            "params": {"skip_download": True},
            "playlist_mincount": 10,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        parsed_url = ParsedURL(url)
        webpage = self._download_webpage(url, video_id=video_id)
        match = self._html_search_regex(
            r"<link\s+[^>]*href=\"([^\"]+/payload.js)", webpage, "payload"
        )
        payload_url = f"{parsed_url.scheme}://{parsed_url.netloc}{match}"
        payload = self._download_webpage(
            payload_url,
            video_id=video_id,
            encoding="unicode_escape",
            note="Downloading payload.js",
        )

        peertube_urls = []
        for _url in re.findall(
            r'"(https://auf1(?:\.\w+)+/videos/embed/[^"]+)"', payload
        ):
            parsed_url = ParsedURL(_url)
            peertube_urls.append(
                f"peertube:{parsed_url.netloc}:{parsed_url.path.split('/')[-1]}"
            )

        if not peertube_urls:
            return UnsupportedError(url)

        if len(peertube_urls) == 1:
            return self.url_result(peertube_urls[0], ie=PeerTubeIE.ie_key())

        return self.playlist_from_matches(
            peertube_urls,
            playlist_id=video_id,
            playlist_title=self._og_search_title(webpage),
            ie=PeerTubeIE.ie_key(),
        )
