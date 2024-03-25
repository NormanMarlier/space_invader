import pygame

from random import choice, randint
from sprites import *
from settings import *
from ui import *


class State():
	"""Base class for State.

	It implements the two basic functions:
		-enter_state(): add the current state to the stack.
		-exit_state(): pop the state out of the stack
	
	A valid state implements three additional functions:
		-update(dt, events): this function iterates over the events in that particular state.
		-handle_event(dt, event): this function handles a particular event.
		-render(surface): this function renders the state.
	"""
	def __init__(self, game):
		self.game = game
		self.prev_state = None

	def update(self, dt, events):
		for event in events:
			self.handle_event(dt, event)

	def render(self, surface):
		pass
	
	def handle_event(self, dt, event):
		if event.type == pygame.QUIT:
			self.game.running, self.game.playing = False, False

	def enter_state(self):
		if len(self.game.state_stack) >= 1:
			self.prev_state = self.game.state_stack[-1]
		self.game.state_stack.append(self)
    
	def exit_state(self):
		self.game.state_stack.pop()


class MainMenu(State):
	"""MainMenu state.
	
	It implements the main menu.
	
	-Play
	-Ranking
	-Credits
	
	This is the starting state.
	Transition state:
        1) GO TO PLAYING_STATE if Play is selected
		2) GO TO RANKING_STATE if Ranking is selected
		3) GO TO CREDITS_STATE if Cresits is selected
	
	"""
	def __init__(self, game):
		self.game = game
		# Background
		self.background = pygame.image.load(self.game.graphics_dir + "/tv.png").convert_alpha()
		# Menu
		self.menu = TextMenu({0: "Play", 1: "Ranking", 2: "Credits"}, [GAME_H//2, GAME_H], [0, GAME_W], self.game.font)

		# State
		self.trigger_state = False

	def update(self, dt, events):
		super().update(dt, events)
		self.transition_state()
	
	def handle_event(self, dt, event):
		super().handle_event(dt, event)
		self.menu.update(event)
		# If pressed a key
		if event.type == pygame.KEYDOWN:
			# update the cursor
			if event.key == pygame.K_RETURN:
				self.trigger_state = True
	
	def transition_state(self) -> None:
		new_state: State
		# If Play is selected, go to PLAY_STATE
		if self.menu.get_option() == "Play" and self.trigger_state:
			new_state = GameWorld(self.game)
			new_state.enter_state()
		elif self.menu.get_option() == "Ranking" and self.trigger_state:
			new_state = RankingMenu(self.game)
			new_state.enter_state()
		elif self.menu.get_option() == "Credits" and self.trigger_state:
			new_state = CreditsMenu(self.game)
			new_state.enter_state()
		self.trigger_state = False
	
	def render_background(self, surface) -> None:
		# Black
		surface.fill(BACKGROUND_COLOR)
		surface.blit(self.background, (0, 0))
	
	def render(self, surface):
		self.render_background(surface)
		# Menu
		draw_text(surface, self.game.font, "Space Invaders", (255, 255, 255), GAME_W//2, GAME_H//4)
		self.menu.render(surface)


class RankingMenu(State):
	def __init__(self, game):
		super(RankingMenu, self).__init__(game)
		self.game.load_score()

	def update(self, dt, events):
		super().update(dt, events)
	
	def handle_event(self, dt, event):
		super().handle_event(dt, event)
		# If pressed a key
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_RETURN:
				self.exit_state()

	def render(self, surface):
		self.prev_state.render_background(surface)
		
		if bool(self.game.sl_manager.ranking):
			for i, (k, v) in enumerate(zip(self.game.sl_manager.ranking.keys(), self.game.sl_manager.ranking.values())):
				text = str(len(self.game.sl_manager.ranking) - i) + ". " + str(k) + ": " + str(v)
				pos_y = GAME_H//2 - i * 32
				draw_text(surface, self.game.font, text, (255, 255, 255), GAME_W//2, pos_y)
		else:
			draw_text(surface, self.game.font, "There are no ranking yet !", (255, 255, 255), GAME_W//2, GAME_H//2)


class CreditsMenu(State):
	def __init__(self, game):
		super(CreditsMenu, self).__init__(game)
	
	def update(self, dt, events):
		super().update(dt, events)
	
	def handle_event(self, dt, event):
		super().handle_event(dt, event)
		# If pressed a key
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_RETURN:
				self.exit_state()
	
	def render(self, surface):
		self.prev_state.render_background(surface)	
		draw_text(surface, self.game.font, "CREDITS", (255, 255, 255), GAME_W//2, GAME_H//2 - 15)
		draw_text(surface, self.game.font, "made by Norman Marlier", (255, 255, 255), GAME_W//2, GAME_H//2 + 30)


class GameWorld(State):
	"""GameWorld state.
	
	It implements the playing world.
	
	Transition state:
        1) GO TO PAUSE_STATE if pause action is selected
		2) GO TO LOOSE_STATE if failure is trigger
	
	"""
	def __init__(self, game) -> None:
		self.game = game
		
		# State
		self.go_to_pause = False
		self.go_to_fail = False
		self.go_to_win = False

		# Reset - Create sprites - Reset score
		self.reset()

		# Lives image
		self.live_surf = pygame.image.load(self.game.graphics_dir + '/player.png').convert_alpha()
	
	def create_sprites(self):
		# Obstacles
		self.obstacles = pygame.sprite.Group()
		obstacle_calc = Obstacle(5)
		obstacle_calc.create_many_obstacles(self.obstacles, [75, 225, 375], [3*GAME_H//4]*3)
		
		# Player
		player_sprite = Player(pygame.math.Vector2(GAME_W//2, GAME_H), [0, GAME_W], self.game.graphics_dir, self.laser_sound)
		self.player = pygame.sprite.GroupSingle(player_sprite)

		# Aliens
		self.aliens_wave = AliensWave(self.game.graphics_dir, self.laser_sound)
		self.aliens_wave.create_wave(rows=6, cols=8)
		self.alien_laser_event = pygame.USEREVENT + 1
		pygame.time.set_timer(self.alien_laser_event , 800)
		self.extra = pygame.sprite.GroupSingle()
		self.extra_timer_event = pygame.USEREVENT + 2
		pygame.time.set_timer(self.extra_timer_event , randint(4*1000, 8*1000)) # Between 4 and 8 secondes
		
	
	def check_collisions(self) -> None:

		# Possible collisions with laser
		if self.player.sprite.lasers:
			for laser in self.player.sprite.lasers:
				# Obstacle collisions
				if pygame.sprite.spritecollide(laser, self.obstacles, True):
					laser.kill()
				
				# Aliens collisions
				aliens_hit = pygame.sprite.spritecollide(laser, self.aliens_wave.group, True)
				if aliens_hit:
					for alien in aliens_hit:
						self.game.update_score(alien.value)
					laser.kill()
					# self.explosion_sound.play()
				
				# Extra collisions
				extra_hit = pygame.sprite.spritecollide(laser, self.extra, True)
				if extra_hit:
					self.game.update_score(extra_hit[0].value)
					laser.kill()
		
		# Possible collisions with aliens
		if self.aliens_wave.group:
			for alien in self.aliens_wave.group:
				# Collision with obstacle
				pygame.sprite.spritecollide(alien, self.obstacles, True)

				# Collision with the player
				if pygame.sprite.spritecollide(alien, self.player, False):
					self.go_to_fail = True
		
		# Alien lasers collisions
		if self.aliens_wave.lasers:
			for laser in self.aliens_wave.lasers:
				# Obstacle collisions
				if pygame.sprite.spritecollide(laser, self.obstacles, True):
					laser.kill()
				
				# Player collisions
				if pygame.sprite.spritecollide(laser, self.player, False):
					laser.kill()
					self.player.sprite.lives -= 1
					if not self.player.sprite.is_alive():
						self.go_to_fail = True

	def update(self, dt, events) -> None:
		super().update(dt, events)
		self.obstacles.update()
		self.aliens_wave.update(dt)
		# Check if there are still aliens on the screen
		if not self.aliens_wave.still_remaining():
			self.go_to_win = True
		self.extra.update()
		self.player.update(dt)
		self.check_collisions()
		self.transition_state()
	
	def handle_event(self, dt, event) -> None:
		super().handle_event(dt, event)
		# If pressed a key
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				self.go_to_pause = True
		
		if event.type == self.extra_timer_event:
			# Spawn an extra
			self.extra.add(Extra(choice(['right','left']), self.game.graphics_dir + "/extra.png"))
			# Reset timer to a random time
			pygame.time.set_timer(self.extra_timer_event , randint(4*1000, 8*1000))
		
		if event.type == self.alien_laser_event:
			# Shoot a laser
			self.aliens_wave.shoot_laser()
			
	def render(self, surface) -> None:
		self.prev_state.render_background(surface)
		# Sprites
		self.obstacles.draw(surface)
		self.aliens_wave.render(surface)
		self.extra.draw(surface)
		draw_text(surface, self.game.font, f'score: {self.game.score}', (255, 255, 255), 10, -10, options="topleft")
		draw_lives(surface, self.live_surf, self.player.sprite.lives)
		self.player.draw(surface)
		self.player.sprite.lasers.draw(surface)
		
	def transition_state(self) -> None:
		# If go_to_fail -> FailState
		new_state: State
		if self.go_to_fail:
			self.game.save_score()
			# Kill the obstacles
			self.obstacles.empty()
			# Kill the aliens wave
			self.aliens_wave.clear_wave()
			new_state = FailedMenu(self.game)
			new_state.enter_state()
			self.go_to_fail = False
		# Elif go_to_pause -> PauseState
		elif self.go_to_pause and not self.go_to_fail:
			new_state = PauseMenu(self.game)
			new_state.enter_state()
			self.go_to_pause = False
		elif self.go_to_win and not self.go_to_fail:
			new_state = WinState(self.game)
			new_state.enter_state()
			self.go_to_win = False
	
	def reset(self) -> None:
		self.game.reset_score()
		self.laser_sound = pygame.mixer.Sound(self.game.audio_dir + "/laser.wav")
		self.laser_sound.set_volume(0.1)
		self.create_sprites()


class FailedMenu(State):
	"""This class handles the state where the player fails.
	
	Possess only Exit state.
	"""
	def __init__(self, game):
		self.game = game
	
	def update(self, dt, events):
		super().update(dt, events)
	
	def handle_event(self, dt, event):
		super().handle_event(dt, event)
		# If pressed a key
		if event.type == pygame.KEYDOWN:
			# Check the key
			if event.key == pygame.K_ESCAPE:
				self.game.save_score()
				# Reset the previous state
				self.prev_state.reset()
				self.exit_state()
	
	def render(self, surface):
		# Black
		surface.fill(BACKGROUND_COLOR)
		self.prev_state.render(surface)
		draw_text(surface, self.game.font, 'You died!', (255, 255, 255), GAME_W//2, GAME_H//2 - 50)
		draw_text(surface, self.game.font, f'score: {self.game.score}', (255, 255, 255), GAME_W//2, GAME_H//2)


class WinState(State):
	"""This class handles when the player survives."""
	def __init__(self, game) -> None:

		self.game = game
	
	def update(self, dt, events):
		super().update(dt, events)
	
	def handle_event(self, dt, event):
		super().handle_event(dt, event)
		# If pressed a key
		if event.type == pygame.KEYDOWN:
			# Check the key
			if event.key == pygame.K_ESCAPE:
				self.game.save_score()
				# Reset the previous state
				self.prev_state.reset()
				self.exit_state()
	
	def render(self, surface):
		# Black
		surface.fill(BACKGROUND_COLOR)
		self.prev_state.render(surface)
		draw_text(surface, self.game.font, 'You won!', (255, 255, 255), GAME_W//2, GAME_H//2 - 50)
		draw_text(surface, self.game.font, f'score: {self.game.score}', (255, 255, 255), GAME_W//2, GAME_H//2)


class PauseMenu(State):
	def __init__(self, game):
		super(PauseMenu, self).__init__(game)
		self.trigger_state = False
		# Menu
		self.menu = TextMenu({0: "Restart", 1: "Exit"}, [GAME_H//4, 3*GAME_H//4], [GAME_W//4, 3*GAME_W//4], self.game.font)
	
	def update(self, dt, events):
		super().update(dt, events)
		self.transition_state()
	
	def handle_event(self, dt, event):
		super().handle_event(dt, event)
		self.menu.update(event)
		# If pressed a key
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_RETURN:
				self.trigger_state = True
	
	def transition_state(self):
		if self.menu.get_option() == "Restart" and self.trigger_state:
			self.trigger_state = False
			self.exit_state()
		elif self.menu.get_option() == "Exit" and self.trigger_state:
			self.game.save_score()
			self.trigger_state = False
			while len(self.game.state_stack) > 1:
				self.game.state_stack.pop()

	def render(self, surface):
		surface.fill(BACKGROUND_COLOR)
		self.prev_state.render(surface)
		self.menu.render(surface)

		
