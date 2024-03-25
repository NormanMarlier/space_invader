import pygame
import json
import time


from settings import *
from states import State, MainMenu


class Game():
    def __init__(self) -> None:
        pygame.init()

        # Screen
        self.game_canvas = pygame.Surface((GAME_W, GAME_H))
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Space Invaders")

        # Time
        self.dt = time.time()
        self.prev_dt = self.dt
        self.clock = pygame.time.Clock()

        # Events
        self.events = None

        # Load Assets
        self.load_assets()

        # Play the background
        self.bg_music = pygame.mixer.Sound(self.audio_dir + '/music.wav')
        self.bg_music.set_volume(0.05)
        self.bg_music.play(loops=-1)

        # Data which need to be stored
        self.player_name = "player"
        self.reset_score()
        self.sl_manager = SaveLoadManager()

        # States
        self.state_stack: list[State] = []
        self.running: bool = True
        self.playing: bool = False
        self.init_state()
    
    def game_loop(self):

        while self.playing:
            # Update time
            self.get_dt()
            # Update events
            self.events = pygame.event.get()
            # Update state
            self.update()
            # Render state
            self.render()
            # FPS
            self.clock.tick(FRAMERATE)
    
    def get_dt(self):
        now = time.time()
        self.dt = now - self.prev_dt
        self.prev_dt = now
    
    def update(self):
        self.state_stack[-1].update(self.dt, self.events)
    
    def render(self):
        self.state_stack[-1].render(self.game_canvas)
        self.screen.blit(pygame.transform.scale(self.game_canvas, (SCREEN_W, SCREEN_H)), (0, 0))
        pygame.display.flip()

    def load_assets(self) -> None:
        self.assets_dir: str = "./assets"
        self.graphics_dir: str = self.assets_dir + "/graphics"
        self.audio_dir: str = self.assets_dir + "/audio"
        self.font = pygame.font.Font(self.assets_dir + '/font/Pixeled.ttf', FONTSIZE)

    def init_state(self):
        self.state_stack.append(MainMenu(self))
    
    def reset_score(self):
        self.score = 0

    def update_score(self, add_value):
        self.score += add_value

    def save_score(self):
        self.sl_manager.save_data((self.player_name, self.score))

    def load_score(self):
        self.sl_manager.load_data()


class SaveLoadManager():
    # Manage ranking
    # Save the top 10 score
    # Remember the name and the associated score
    def __init__(self):
        self.filename = SAVE_FILE
        self.ranking = {}
        self.TOP_N = 10
    
    def sorted_ranking(self, ranking):
        return dict(sorted(ranking.items(), key=lambda item: item[1]))

    def load_data(self):
        try:
            with open(self.filename, "r+") as file:
                self.ranking = json.load(file)
                self.update_ranking(self.ranking)
        except:
            pass
    
    def save_data(self, data):
        """Add the new data to the current ranking."""
        self.update_ranking(data)
        with open(self.filename, "w+") as file:
            json.dump(self.ranking, file)

    def update_ranking(self, data):
        """Check if the new data can be integrated into the ranking
        
        Add the new data and sort the ranking. Then, keep the 10 best.
        Args:
            data, a tuple (name, score)
        """
        # If the player already exists
        if data[0] in self.ranking.keys():
            # Check if the new score is greater than before
            if data[1] > self.ranking[data[0]]:
                self.ranking[data[0]] = data[1]
        else:
            self.ranking[data[0]] = data[1]
        # Sorted the ranking and keep the 10 best
        self.ranking = self.sorted_ranking(self.ranking)
        self.ranking = {kv[0]:kv[1] for i, kv in enumerate(self.ranking.items()) if i <= self.TOP_N}


if __name__ == "__main__":
    g = Game()

    while g.running:
        g.playing = True
        g.game_loop()


    
