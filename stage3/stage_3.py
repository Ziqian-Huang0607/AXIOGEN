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

# --- PROJECT AXIOGEN: STAGE 3 (STRICT LOGIC GATE) ---

generation = 0
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"axiogen_stage3_{timestamp}.csv"
autosave_filename = f"axiogen_stage3_AUTOSAVE.pkl"

# Force-initialize CSV
with open(log_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Generation", "Max Fitness", "Avg Fitness", "Success Count"])

class World:
    def __init__(self):
        self.width, self.height = 800, 600
        self.friction = 0.92
        # THE GREAT WALL: Completely splits the screen at x=400
        self.walls = [
            pygame.Rect(0, 0, 800, 15), pygame.Rect(0, 585, 800, 15), # Top/Bottom
            pygame.Rect(0, 0, 15, 600), pygame.Rect(785, 0, 15, 600), # Left/Right
            pygame.Rect(390, 0, 20, 250), # Top half of divider
            pygame.Rect(390, 350, 20, 250) # Bottom half of divider
        ]
        # THE GATE: Fills the gap in the divider
        self.gate_rect = pygame.Rect(390, 250, 20, 100)
        
        # KEY & GOAL
        self.switch_pos = (100, 100) # Top Left
        self.goal_pos = (700, 300)   # Center Right
        
class Agent:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = 10
        self.angle = 0 
        self.vel = 0
        self.alive = True
        self.has_key = False 
        self.energy = 1500 
        self.radars = [] 

    def move(self, world, speed_output, turn_output):
        if not self.alive: return False
        self.angle += turn_output * 10 
        self.vel += speed_output * 2
        self.vel = max(-1, min(8, self.vel)) 

        dx, dy = math.cos(math.radians(self.angle)) * self.vel, math.sin(math.radians(self.angle)) * self.vel
        new_x, new_y = self.x + dx, self.y + dy
        
        agent_rect = pygame.Rect(new_x - 10, new_y - 10, 20, 20)
        hit = False
        if agent_rect.collidelist(world.walls) != -1: hit = True
        
        # INDIVIDUAL GATE: Only solid if you don't have the key
        if not self.has_key and agent_rect.colliderect(world.gate_rect): 
            hit = True
        
        if not hit:
            self.x, self.y = new_x, new_y
        else:
            self.vel = -2 # Bounce
            
        self.vel *= world.friction
        self.energy -= 1
        if self.energy <= 0: self.alive = False
        return hit

    def sense(self, world):
        angles = [-45, -20, 0, 20, 45]
        self.radars = []
        for a in angles:
            radar_angle = math.radians(self.angle + a)
            start_pos = (self.x, self.y)
            end_pos = (self.x + math.cos(radar_angle)*150, self.y + math.sin(radar_angle)*150)
            closest_dist = 150
            # Sense walls. Only sense gate if key is missing.
            targets = world.walls + ([world.gate_rect] if not self.has_key else [])
            for wall in targets:
                clipped = wall.clipline(start_pos, end_pos)
                if clipped:
                    d = math.hypot(clipped[0][0]-self.x, clipped[0][1]-self.y)
                    if d < closest_dist: closest_dist = d
            self.radars.append(closest_dist)
            
        # Distances to objects
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

    nets, ge, agents = [], [], []
    for _, genome in genomes:
        genome.fitness = 0.0
        nets.append(neat.nn.FeedForwardNetwork.create(genome, config))
        ge.append(genome)
        # SPAWN ON LEFT SIDE (Same as key)
        agents.append(Agent(100, 500)) 

    success_count = 0
    running = True
    while running and len(agents) > 0:
        screen.fill((15, 15, 15))
        for wall in world.walls: pygame.draw.rect(screen, (60, 60, 60), wall)
        pygame.draw.rect(screen, (180, 0, 0), world.gate_rect) # Gate
        pygame.draw.circle(screen, (0, 100, 255), world.switch_pos, 20) # Key
        pygame.draw.circle(screen, (0, 255, 100), world.goal_pos, 25)   # Goal

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

        active_agents = 0
        for i, agent in enumerate(agents):
            if not agent.alive: continue
            active_agents += 1
            agent.sense(world)
            
            inputs = [
                *[(150-x)/150 for x in agent.radars],
                agent.dist_s / 800, math.sin(agent.ang_s),
                agent.dist_g / 800, math.sin(agent.ang_g),
                1.0 if agent.has_key else 0.0
            ]
            
            output = nets[i].activate(inputs)
            hit = agent.move(world, output[0], output[1])
            if hit: ge[i].fitness -= 0.1

            # REWARD LOGIC
            if not agent.has_key:
                # 1. Drive toward Key
                ge[i].fitness += (800 - agent.dist_s) / 400
                if agent.dist_s < 40:
                    agent.has_key = True
                    ge[i].fitness += 5000
                    print(f"Gen {generation}: [KEY FOUND]")
            else:
                # 2. Drive toward Goal (Now that gate is phased)
                ge[i].fitness += (800 - agent.dist_g) / 100
                if agent.dist_g < 40:
                    ge[i].fitness += 15000
                    success_count += 1
                    agent.alive = False
                    print(f"Gen {generation}: [GOAL REACHED]")

        if active_agents == 0: running = False
        for agent in agents:
            c = (255, 255, 0) if agent.has_key else (0, 200, 255)
            pygame.draw.circle(screen, c, (int(agent.x), int(agent.y)), 10)
        
        text = font.render(f"Gen: {generation} | Success: {success_count} | Alive: {active_agents}", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        pygame.display.flip()
        clock.tick(60)

    # SECURE LOGGING
    if len(ge) > 0:
        max_f = max(g.fitness for g in ge)
        avg_f = sum(g.fitness for g in ge) / len(ge)
        with open(log_filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([generation, max_f, avg_f, success_count])
            f.flush()
        
        best_agent = max(ge, key=lambda x: x.fitness)
        with open(autosave_filename, 'wb') as f:
            pickle.dump(best_agent, f)

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)
    try:
        with open('axiogen_stage2_AUTOSAVE.pkl', 'rb') as f:
            stage2_genome = pickle.load(f)
        new_pop = {}
        for i in range(config.pop_size):
            key = i + 1
            g = copy.deepcopy(stage2_genome)
            g.key = key
            g.fitness = 0.0
            g.mutate(config.genome_config)
            new_pop[key] = g
        p.population = new_pop
        p.species.speciate(config, p.population, p.generation)
        print(" >> Stage 2 Explorer DNA Injected.")
    except:
        print(" >> Starting Fresh.")

    p.add_reporter(neat.StdOutReporter(True))
    p.run(eval_genomes, 150)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)