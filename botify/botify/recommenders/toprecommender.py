from typing import Dict, List

from .contextual import Contextual
from .recommender import Recommender
from .toppop import TopPop, Random
from ..track import Track

class TopRecommender(Recommender):
    def __init__(self, track_redis, catalog, tracks, asrtists):
        self.track_redis = track_redis
        self.catalog = catalog

        self.contextrec = Contextual(track_redis, catalog)
        self.randomrec = Random(track_redis)

        self.tracks: Dict[int, List[int]] = tracks
        self.asrtists: Dict[int, List[str]] = asrtists

        self.rec_from_top = TopPop(track_redis, catalog.top_tracks[:100])



    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        for var in [self.contextrec, self.rec_from_top, self.randomrec]:
            track_id = self.try_rec(var, user, prev_track, prev_track_time)
            if track_id:
                return track_id

        track_id = self.randomrec.recommend_next(user, prev_track, prev_track_time)
        track: Track = self.catalog.from_bytes(self.track_redis.get(prev_track))
        self.tracks[user].append(track_id)
        self.asrtists[user].append(track.artist)
        return track_id

    def try_rec(self, recommender: Recommender, user: int, prev_track: int, prev_track_time: float):
        for i in range(10):
            track_id = recommender.recommend_next(user, prev_track, prev_track_time)
            if track_id not in self.tracks[user]:
                track: Track = self.catalog.from_bytes(self.track_redis.get(prev_track))
                if track.artist not in self.asrtists:
                    self.tracks[user].append(track_id)
                    self.asrtists[user].append(track.artist)
                    return track_id