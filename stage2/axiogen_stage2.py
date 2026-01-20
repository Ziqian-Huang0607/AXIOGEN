import pygame
import sys
import math
import neat
import os
import random
import pickle
import csv
import datetime
import copy

# --- PROJECT AXIOGEN: STAGE 2 (V4.2 - STABLE) ---

# Initialize global generation counter
generation = 0 

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"axiogen_stage2_{timestamp}.csv"
autosave_filename = f"axiogen_stage2_AUTOSAVE.pkl"

# Setup CSV
with open(log_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Generation", "Max Exploration", "Avg Exploration", "Alive Count"])

class World:
    def __init__(self):
        self.width, self.height = 800, 600
        self.friction = 0.92
        self.walls = []
        # Borders
        self.create_wall(0, 0, 800, 15)
        self.create_wall(0, 585, 800, 15)
        self.create_wall(0, 0, 15, 600)
        self.create_wall(785, 0, 15, 600)
        # Random Maze
        for _ in range(12):
            w, h = random.randint(60, 200), random.randint(60, 200)
            x, y = random.randint(100, 600), random.randint(100, 400)
            if random.random() > 0.5: self.create_wall(x, y, w, 20)
            else: self.create_wall(x, y, 20, h)

    def create_wall(self, x, y, w, h):
        self.walls.append(pygame.Rect(x, y, w, h))

class Agent:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = 10
        self.angle = random.randint(0, 360) 
        self.vel = 0
        self.alive = True
        self.visited_sectors = set() 
        self.stagnation_timer = 0 

    def move(self, world, speed_output, turn_output):
        if not self.alive: return False
        self.angle += turn_output * 10 
        self.vel += speed_output * 2
        self.vel = max(-1, min(6, self.vel)) 
        
        rad = math.radians(self.angle)
        new_x = self.x + math.cos(rad) * self.vel
        new_y = self.y + math.sin(rad) * self.vel
        
        agent_rect = pygame.Rect(new_x - 10, new_y - 10, 20, 20)
        collision_idx = agent_rect.collidelist(world.walls)
        
        if collision_idx == -1:
            self.x, self.y = new_x, new_y
            self.vel *= world.friction
            hit = False
        else:
            wall = world.walls[collision_idx]
            if self.x < wall.centerx: self.x -= 3
            else: self.x += 3
            if self.y < wall.centery: self.y -= 3
            else: self.y += 3
            self.vel = 0 
            hit = True
        
        self.stagnation_timer += 1
        if self.stagnation_timer > 180: self.alive = False
        return hit

    def sense(self, world):
        angles = [-45, -20, 0, 20, 45]
        self.radars = []
        for a in angles:
            radar_angle = math.radians(self.angle + a)
            start_pos = (self.x, self.y)
            end_pos = (self.x + math.cos(radar_angle)*150, self.y + math.sin(radar_angle)*150)
            closest_dist = 150
            for wall in world.walls:
                clipped_line = wall.clipline(start_pos, end_pos)
                if clipped_line:
                    dist = math.hypot(clipped_line[0][0] - self.x, clipped_line[0][1] - self.y)
                    if dist < closest_dist: closest_dist = dist
            self.radars.append(closest_dist)

    def draw(self, screen):
        if not self.alive: return
        color_val = max(0, 255 - (self.stagnation_timer * 1.4))
        pygame.draw.circle(screen, (255 - color_val, color_val, 255), (int(self.x), int(self.y)), self.radius)

def eval_genomes(genomes, config):
    global generation
    generation += 1
    pygame.init()
    world = World() 
    screen = pygame.display.set_mode((world.width, world.height))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)
    memory_surface = pygame.Surface((world.width, world.height))
    memory_surface.set_alpha(70); memory_surface.fill((0, 0, 0))

    nets, ge, agents = [], [], []
    for _, genome in genomes:
        genome.fitness = 0.0 # Force float initialization
        nets.append(neat.nn.FeedForwardNetwork.create(genome, config))
        ge.append(genome)
        agents.append(Agent(400, 300))

    for frame in range(1200): 
        screen.fill((15, 15, 15))
        for wall in world.walls: pygame.draw.rect(screen, (60, 60, 60), wall)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

        alive_count = 0
        for i, agent in enumerate(agents):
            if not agent.alive: continue
            alive_count += 1
            agent.sense(world)
            inputs = [(150.0 - x) / 150.0 for x in agent.radars]
            output = nets[i].activate(inputs)
            hit_wall = agent.move(world, output[0], output[1])
            if hit_wall: ge[i].fitness -= 1.0
            
            grid_size = 20
            sx, sy = int(agent.x // grid_size), int(agent.y // grid_size)
            if (sx, sy) not in agent.visited_sectors:
                agent.visited_sectors.add((sx, sy))
                ge[i].fitness += 15.0 
                agent.stagnation_timer = 0
                pygame.draw.rect(memory_surface, (0, 100, 255), (sx*grid_size, sy*grid_size, grid_size, grid_size))
            else:
                ge[i].fitness -= 0.04

        if alive_count == 0: break
        screen.blit(memory_surface, (0,0))
        for agent in agents: agent.draw(screen)
        text = font.render(f"Gen: {generation} | Explorers: {alive_count}", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        pygame.display.flip()
        clock.tick(60)

    # Logging & AutoSave
    if len(ge) > 0:
        best_g = max(ge, key=lambda x: x.fitness)
        with open(log_filename, mode='a', newline='') as f:
            csv.writer(f).writerow([generation, best_g.fitness, sum(g.fitness for g in ge)/len(ge), alive_count])
        with open(autosave_filename, 'wb') as f:
            pickle.dump(best_g, f)

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    
    # Proper Transfer Learning Injection
    p = neat.Population(config)
    
    try:
        # LOOK FOR THE BRAIN
        with open('axiogen_stage1_BEST.pkl', 'rb') as f:
            stage1_genome = pickle.load(f)
        
        # We must replace the population and RESET species to avoid the TypeError
        new_pop = {}
        for i in range(config.pop_size):
            key = i + 1
            g = copy.deepcopy(stage1_genome)
            g.key = key
            g.fitness = 0.0
            g.mutate(config.genome_config) # Add variation
            new_pop[key] = g
            
        p.population = new_pop
        # FORCE re-speciation
        p.species.speciate(config, p.population, p.generation)
        print(" >> SUCCESS: Wolf Brain Injected and Speciated.")
        
    except Exception as e:
        print(f" >> NOTICE: Starting from scratch. (Reason: {e})")

    p.add_reporter(neat.StdOutReporter(True))
    p.run(eval_genomes, 100)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)