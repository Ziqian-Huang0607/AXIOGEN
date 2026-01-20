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

# --- PROJECT AXIOGEN: STAGE 4 (THE SENTINEL - PLASTICITY EDITION) ---

generation = 0
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
autosave_filename = f"axiogen_stage4_AUTOSAVE.pkl"

class World:
    def __init__(self):
        self.width, self.height = 800, 600
        self.friction = 0.92
        self.walls = [
            pygame.Rect(0, 0, 800, 15), pygame.Rect(0, 585, 800, 15),
            pygame.Rect(0, 0, 15, 600), pygame.Rect(785, 0, 15, 600),
            pygame.Rect(390, 0, 20, 250), pygame.Rect(390, 350, 20, 250)
        ]
        self.gate_rect = pygame.Rect(390, 250, 20, 100)
        self.switch_pos = (100, 100)
        self.goal_pos = (700, 300)

class Agent:
    def __init__(self, x, y, genome, config):
        self.x, self.y = x, y
        self.radius = 10
        self.angle = 0
        self.vel = 0
        self.alive = True
        self.has_key = False
        self.energy = 2000
        self.pain = 0 # Grounded Pain Sensor
        
        # NEAT Brain
        self.genome = genome
        self.config = config
        self.net = neat.nn.FeedForwardNetwork.create(genome, config)

    def move(self, world, outputs):
        if not self.alive: return
        
        # outputs[0] = Speed, outputs[1] = Turn
        self.angle += outputs[1] * 10 
        self.vel += outputs[0] * 2
        self.vel = max(-1, min(8, self.vel)) 

        dx = math.cos(math.radians(self.angle)) * self.vel
        dy = math.sin(math.radians(self.angle)) * self.vel
        new_x, new_y = self.x + dx, self.y + dy
        
        agent_rect = pygame.Rect(new_x - 10, new_y - 10, 20, 20)
        self.pain = 0 # Reset pain
        
        collision = False
        if agent_rect.collidelist(world.walls) != -1: collision = True
        if not self.has_key and agent_rect.colliderect(world.gate_rect): collision = True
        
        if not collision:
            self.x, self.y = new_x, new_y
        else:
            self.vel = -2
            self.pain = 1.0 # FEEL THE PAIN (Groundedness)
            # --- REAL-TIME PLASTICITY: PUNISH THE RECENT ACTION ---
            self.apply_plasticity(-0.1) # Weaken the connections that caused this crash

        self.vel *= world.friction
        self.energy -= 1
        if self.energy <= 0: self.alive = False

    def apply_plasticity(self, factor):
        """ Manually nudges weights in the genome based on immediate experience """
        for conn in self.genome.connections.values():
            if conn.enabled:
                # If we hit a wall, we nudge the weights slightly
                # In a real brain, this would be restricted to recently active synapses
                conn.weight += (random.random() * factor)
        # Rebuild the network with new weights
        self.net = neat.nn.FeedForwardNetwork.create(self.genome, self.config)

    def sense(self, world):
        angles = [-45, -20, 0, 20, 45]
        self.radars = []
        for a in angles:
            radar_angle = math.radians(self.angle + a)
            start_pos = (self.x, self.y)
            end_pos = (self.x + math.cos(radar_angle)*150, self.y + math.sin(radar_angle)*150)
            closest_dist = 150
            targets = world.walls + ([world.gate_rect] if not self.has_key else [])
            for wall in targets:
                clipped = wall.clipline(start_pos, end_pos)
                if clipped:
                    d = math.hypot(clipped[0][0]-self.x, clipped[0][1]-self.y)
                    if d < closest_dist: closest_dist = d
            self.radars.append(closest_dist)
            
        self.dist_s = math.hypot(world.switch_pos[0]-self.x, world.switch_pos[1]-self.y)
        self.ang_s = math.atan2(world.switch_pos[1]-self.y, world.switch_pos[0]-self.x) - math.radians(self.angle)
        self.dist_g = math.hypot(world.goal_pos[0]-self.x, world.goal_pos[1]-self.y)
        self.ang_g = math.atan2(world.goal_pos[1]-self.y, world.goal_pos[0]-self.x) - math.radians(self.angle)

def eval_genomes(genomes, config):
    global generation
    generation += 1
    pygame.init()
    world = World() 
    screen = pygame.display.set_mode((world.width, world.height))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    agents = []
    for _, genome in genomes:
        genome.fitness = 0.0
        agents.append(Agent(100, 500, genome, config))

    running = True
    while running and any(a.alive for a in agents):
        screen.fill((10, 10, 15))
        for wall in world.walls: pygame.draw.rect(screen, (50, 50, 70), wall)
        pygame.draw.rect(screen, (150, 0, 0), world.gate_rect)
        pygame.draw.circle(screen, (0, 100, 255), world.switch_pos, 20) 
        pygame.draw.circle(screen, (0, 255, 100), world.goal_pos, 25)   

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

        for agent in agents:
            if not agent.alive: continue
            
            agent.sense(world)
            # 12 INPUTS: 1-5 Radars, 6-7 Switch, 8-9 Goal, 10 Key, 11 PAIN, 12 ENERGY
            inputs = [
                *[(150-x)/150 for x in agent.radars],
                agent.dist_s / 800, math.sin(agent.ang_s),
                agent.dist_g / 800, math.sin(agent.ang_g),
                1.0 if agent.has_key else 0.0,
                agent.pain,
                agent.energy / 2000
            ]
            
            output = agent.net.activate(inputs)
            agent.move(world, output)
            
            # --- GROUNDED REWARDS ---
            if not agent.has_key:
                agent.genome.fitness += (800 - agent.dist_s) / 500
                if agent.dist_s < 40:
                    agent.has_key = True
                    agent.genome.fitness += 5000
                    agent.apply_plasticity(0.2) # REWARD THE BRAIN (Strengthen synapses)
                    print("KEY FOUND")
            else:
                agent.genome.fitness += (800 - agent.dist_g) / 100
                if agent.dist_g < 40:
                    agent.genome.fitness += 20000
                    agent.alive = False
                    print("GOAL REACHED")

        # Draw Agents
        for agent in agents:
            if agent.alive:
                color = (255, 255, 0) if agent.has_key else (255, 255, 255)
                # If agent feels pain, draw it red
                if agent.pain > 0: color = (255, 0, 0)
                pygame.draw.circle(screen, color, (int(agent.x), int(agent.y)), 10)
        
        pygame.display.flip()
        clock.tick(60)

    # Auto-Save Best
    best_genome = max((a.genome for a in agents), key=lambda g: g.fitness)
    with open(autosave_filename, 'wb') as f:
        pickle.dump(best_genome, f)

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)
    
    # Load Stage 3 Logic
    try:
        with open('axiogen_stage3_AUTOSAVE.pkl', 'rb') as f:
            stage3_genome = pickle.load(f)
        print(" >> STAGE 3 Logic Injected.")
        new_pop = {}
        for i in range(config.pop_size):
            key = i + 1
            g = copy.deepcopy(stage3_genome)
            g.key = key; g.fitness = 0.0
            g.mutate(config.genome_config)
            new_pop[key] = g
        p.population = new_pop
        p.species.speciate(config, p.population, p.generation)
    except:
        print(" >> Starting Fresh Stage 4.")

    p.add_reporter(neat.StdOutReporter(True))
    p.run(eval_genomes, 100)

if __name__ == "__main__":
    run(os.path.join(os.path.dirname(__file__), 'config-feedforward.txt'))