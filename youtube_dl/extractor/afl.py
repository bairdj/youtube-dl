# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from collections import OrderedDict
import re


class AFLIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?afl\.com\.au/match-centre/[0-9]+/[0-9]+/[a-z-]+'
    _TEST = {
        'url': 'http://www.afl.com.au/match-centre/2016/25/haw-v-wb',
        'md5': 'b6c14816a8a683f330604bd3e5f62c98',
        'info_dict': {
            'id': 'CD_M20160142502_1',
            'ext': 'mp4',
            'title': 'Quarter 1'
        }
    }
    qualityPriority = {
        'low': {'format_id': 'low', 'width': 320, 'height': 180, 'quality': 1},
        'med': {'format_id': 'med', 'width': 720, 'height': 480, 'quality': 2},
        'high': {'format_id': 'high', 'width': 1280, 'height': 720, 'quality': 3}
    }
    
    def get_period_id(self, matchId, periodName):
        match = re.match('Quarter ([0-9]+)', periodName)
        if match is not None:
            return matchId + '_' + match.group(1)
        return matchId + '_' + periodName

    def _real_extract(self, url):
        webpage = self._download_webpage(url, None)
        #Get the Champion Data round ID which we need to fetch the video URLs
        round = self._html_search_regex(r'<meta name="omni-match-round-id" content="(.*)"', webpage, 'Round ID')
		#Match ID to serve as a video ID
        match = self._html_search_regex(r'<meta name="omni-match-sds-id" content="(.*)"', webpage, 'Match ID')
        matchName = self._html_search_regex(r'<meta name="omni-match-name" content="(.*)"', webpage, 'Match name')
        
        #Get the round XML
        roundVideo = self._download_xml('http://www.afl.com.au/api/gas/afl/roundVideo/' + round, match)
        #Match element
        matchVideo = roundVideo.find('./matches/match[@id="' + match + '"]')
        videoNames = OrderedDict()
        #Go through the qualities and add them to a list
        for quality in matchVideo.iter('quality'):
            for period in quality.iter('period'):
                #Add key for this period if necessary
                if period.get('name') not in videoNames:
                    videoNames[period.get('name')] = []
                detail = {}
                detail.update({'url': period.get('url')})
                detail.update(self.qualityPriority.get(quality.get('name'), {}))
                videoNames[period.get('name')].append(detail)
        #Convert our data into youtube-dl format
        entries = []
        for periodName, details in videoNames.items():
            entry = {'title': periodName, 'formats': [], 'id': self.get_period_id(match, periodName)}
            for url in details:
                entry['formats'].append(url)
            entries.append(entry)
        return {
            'id': match,
            'title': matchName,
            'location': matchVideo.get('venue'),
			'_type': 'multi_video',
            'entries': entries
        }