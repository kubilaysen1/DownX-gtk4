import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from settings import GLOBAL_CONFIG

class SpotifyClient:
    def __init__(self):
        self.sp = None
        self._connect()

    def _connect(self):
        client_id = GLOBAL_CONFIG.get("spotify_client_id")
        client_secret = GLOBAL_CONFIG.get("spotify_client_secret")

        if not client_id or not client_secret:
            print("⚠️ [API] Client ID/Secret eksik.")
            return

        try:
            self.sp = spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(
                    client_id=client_id,
                    client_secret=client_secret
                )
            )
            print("✅ [API] Bağlantı Başarılı.")
        except Exception as e:
            print(f"❌ [API] Bağlantı Hatası: {e}")
            self.sp = None

    def get_content_info(self, url):
        if not self.sp: return None

        try:
            if "playlist/" in url:
                return self._get_playlist_tracks(url)
            elif "album/" in url:
                return self._get_album_tracks(url)
            elif "track/" in url:
                return self._get_single_track(url)
            return None
        except Exception as e:
            print(f"❌ [API] Veri Hatası: {e}")
            return None

    def _get_playlist_tracks(self, playlist_url):
        try:
            playlist_id = playlist_url.split("playlist/")[-1].split("?")[0]
            
            # --- DEĞİŞİKLİK: fields parametresini kaldırdık. Her şeyi çek! ---
            results = self.sp.playlist(playlist_id)
            
            # İsmi al (API'den gelen 'name' kesinlikle dolu olmalı)
            playlist_name = results['name']
            owner_name = results['owner']['display_name']
            
            # İsim boşsa ID'yi kullan (İmkansız ama önlem)
            if not playlist_name:
                playlist_name = f"Playlist {playlist_id}"
                
            print(f"✅ [API] Playlist: '{playlist_name}' (Sahibi: {owner_name})")

            tracks = []
            items_data = results['tracks']
            
            while True:
                for item in items_data['items']:
                    track = item.get('track')
                    if not track: continue
                    
                    # Playlist adını albüm adı olarak zorla
                    parsed = self._parse_track_object(track, override_album=playlist_name)
                    if parsed: tracks.append(parsed)
                
                if items_data.get('next'):
                    items_data = self.sp.next(items_data)
                else:
                    break

            return {
                "title": playlist_name, 
                "type": "playlist", 
                "tracks": tracks, 
                "album": playlist_name 
            }
        except Exception as e:
            print(f"❌ [API] Playlist Hatası: {e}")
            return None

    def _get_album_tracks(self, album_url):
        try:
            album_id = album_url.split("album/")[-1].split("?")[0]
            album = self.sp.album(album_id)
            album_name = album['name']
            
            print(f"✅ [API] Albüm: {album_name}")
            
            tracks = []
            results = self.sp.album_tracks(album_id)
            
            while True:
                for item in results['items']:
                    track_obj = self._parse_simple_track(item, album, album_name)
                    tracks.append(track_obj)
                
                if results.get('next'):
                    results = self.sp.next(results)
                else:
                    break
            
            return {"title": album_name, "type": "album", "tracks": tracks, "album": album_name}
        except Exception as e:
            print(f"❌ [API] Albüm Hatası: {e}")
            return None

    def _get_single_track(self, track_url):
        try:
            track_id = track_url.split("track/")[-1].split("?")[0]
            track = self.sp.track(track_id)
            parsed = self._parse_track_object(track)
            return {
                "title": parsed['title'],
                "type": "track",
                "tracks": [parsed],
                "album": parsed['album']
            }
        except: return None

    def _parse_track_object(self, track, override_album=None):
        try:
            artist = track['artists'][0]['name'] if track.get('artists') else "Bilinmiyor"
            title = track['name']
            
            # Playlist adı varsa onu kullan, yoksa şarkının albümü
            album = override_album if override_album else track['album']['name']
            
            cover = ""
            if track.get('album') and track['album'].get('images'):
                cover = track['album']['images'][0]['url']
            
            year = ""
            if track.get('album') and track.get('album').get('release_date'):
                 year = track['album']['release_date'][:4]

            return {
                "artist": artist,
                "title": title,
                "album": album, # Klasör adı
                "cover_url": cover,
                "year": year,
                "track_no": track.get('track_number', 0),
                "url": track['external_urls']['spotify']
            }
        except: return None

    def _parse_simple_track(self, item, album_data, album_name):
        cover = ""
        if album_data.get('images'):
             cover = album_data['images'][0]['url']
             
        return {
            "artist": item['artists'][0]['name'],
            "title": item['name'],
            "album": album_name,
            "cover_url": cover,
            "year": album_data.get('release_date', '')[:4],
            "track_no": item.get('track_number', 0),
            "url": item['external_urls']['spotify']
        }