import subprocess
from trackloader import TrackLoader

class Decoder():
    def __init__(self, path_temp, player, clear_temp_dir):
        self.clear_temp_dir = clear_temp_dir
        self.decode_is_running = False
        self.decode_obj = None
        self.path_temp = path_temp
        #self.path_track = ""
        self.new_track = ["", 0, ""] #[path, chnl, codec]
        self.track_name = "" #is it really necessary
        self.player = player

    def update_decoder(self, dt):
        if self.decode_is_running is True and self.decode_obj.poll() is not None:  # TODO: return code check
            t = TrackLoader(self.player, self.path_temp + "/" + self.track_name[:-3] + "wav", self.new_track[1], self.clear_temp_dir)
            t.start()
            #self.player.refresh_snd[self.new_track[1]] = True
            # self.clear_temp_dir()
            self.decode_is_running = False

    def load_mp3(self, track_name, new_track):
        self.new_track = new_track
        self.track_name = track_name
        self.decode_obj = subprocess.Popen(["ffmpeg", "-i", self.new_track[0],
                                            self.path_temp + "/" + track_name[:-3] + "wav"])
        self.decode_is_running = True

